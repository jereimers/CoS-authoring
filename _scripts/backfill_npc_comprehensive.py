#!/usr/bin/env python3
"""
Comprehensive NPC Property Backfill Script
Extracts NPC properties from Arc and CoS-WotC source documents:
- race and class from stat block descriptions
- factions from context
- home_base from location sections
- arcs from which Arc document they appear in
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set
import shutil
from datetime import datetime
from collections import defaultdict


def extract_frontmatter(content: str) -> Tuple[str, str, str]:
    """Extract frontmatter, body, and delimiter from markdown content."""
    yaml_match = re.match(r'^---\s*\n(.*?\n)---\s*\n(.*)', content, re.DOTALL)
    if yaml_match:
        return yaml_match.group(1), yaml_match.group(2), '---'
    return '', content, ''


def parse_frontmatter(fm_text: str) -> Dict[str, Any]:
    """Parse YAML frontmatter text into a dictionary."""
    if not fm_text.strip():
        return {}
    try:
        return yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        print(f"Warning: YAML parsing error: {e}")
        return {}


def serialize_frontmatter(frontmatter: Dict[str, Any]) -> str:
    """Serialize frontmatter dictionary back to YAML string."""
    if not frontmatter:
        return ''
    yaml_str = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )
    return yaml_str


def normalize_npc_name(name: str) -> str:
    """Normalize NPC name for matching (remove namespace, pipes, etc.)."""
    # Remove namespace like "DM Wiki/Entities/NPCs/"
    name = name.split('/')[-1] if '/' in name else name
    # Remove pipes like "Urwin Martikov|Urwin"
    name = name.split('|')[0] if '|' in name else name
    return name.strip()


def get_known_npc_names(vault_path: Path) -> Dict[str, List[str]]:
    """
    Build a dictionary of known NPC names and their aliases.
    Returns: {primary_name: [alias1, alias2, ...]}
    """
    npc_names = {}
    npc_files = list(vault_path.glob("DM Wiki/Entities/NPCs/*.md"))

    for npc_file in npc_files:
        try:
            with open(npc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm_text, _, _ = extract_frontmatter(content)
            frontmatter = parse_frontmatter(fm_text)

            if frontmatter.get('type') == 'NPC':
                name = frontmatter.get('name') or npc_file.stem
                aliases = frontmatter.get('aliases', []) or []
                if isinstance(aliases, str):
                    aliases = [aliases]

                # Store primary name with all its aliases
                all_names = [name] + aliases
                npc_names[name] = all_names
        except Exception:
            continue

    return npc_names


def build_comprehensive_npc_cache(vault_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Build comprehensive NPC data cache from all source documents.
    Returns: {npc_name: {race, class, factions, home_base, arcs}}
    """
    npc_cache = defaultdict(lambda: {
        'race': None,
        'class': None,
        'factions': set(),
        'home_base': None,
        'arcs': set(),
    })

    # First, get list of known NPCs and their aliases
    print("Building list of known NPCs...")
    known_npcs = get_known_npc_names(vault_path)
    print(f"Found {len(known_npcs)} known NPCs")

    # Find all source documents
    arc_files = list(vault_path.glob("Source/CoS-Reloaded/**/*.md"))
    wotc_files = list(vault_path.glob("Source/CoS-WotC/**/*.md"))
    all_source_files = arc_files + wotc_files

    print(f"Scanning {len(arc_files)} Arc documents and {len(wotc_files)} WotC documents...")

    npcs_with_arcs = 0
    for source_file in all_source_files:
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract arc name from filename
            arc_name = None
            if 'CoS-Reloaded' in str(source_file):
                # Extract arc from filename like "Arc C - Into the Valley.md"
                filename = source_file.name
                if filename.startswith('Arc '):
                    arc_name = filename.replace('.md', '')

            # Extract location from file path or section headings
            location_context = extract_location_context(source_file, content)

            # For Arc files, search for mentions of known NPCs (with or without wikilinks)
            if arc_name:
                # Search for each known NPC in the content
                for primary_name, all_names in known_npcs.items():
                    # Check if any variant of this NPC's name appears in the content
                    for name_variant in all_names:
                        # Use word boundaries to avoid partial matches
                        # e.g., "Urwin" matches but "Urwinia" doesn't
                        pattern = r'\b' + re.escape(name_variant) + r'\b'
                        if re.search(pattern, content, re.IGNORECASE):
                            npc_cache[primary_name]['arcs'].add(arc_name)
                            npcs_with_arcs += 1
                            break  # Found this NPC, no need to check other aliases

            # Pattern 1: NPCs with wikilinks and alignment/gender/race
            # Example: [[Urwin Martikov]] (LG male human)
            npc_pattern_wikilink = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]\s*\((?:LG|NG|CG|LN|N|CN|LE|NE|CE)\s+(male|female|nonbinary)?\s*([a-z][a-z\s]+?)\)'

            # Pattern 2: NPCs without wikilinks
            # Example: Bildrath Cantemir (LN male human commoner)
            npc_pattern_plain = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\((?:LG|NG|CG|LN|N|CN|LE|NE|CE)\s+(male|female)?\s*([a-z][a-z\s]+?)\)'

            # Combine both patterns
            all_matches = []
            all_matches.extend([(m, 'wikilink') for m in re.finditer(npc_pattern_wikilink, content, re.IGNORECASE)])
            all_matches.extend([(m, 'plain') for m in re.finditer(npc_pattern_plain, content)])

            for match, match_type in all_matches:
                npc_name = normalize_npc_name(match.group(1))
                gender = match.group(2)
                race_class_text = match.group(3).strip() if match.group(3) else None

                # Split race_class_text into race and class
                # Examples: "human", "human commoner", "dusk elf", "wereraven"
                race = None
                class_name = None

                if race_class_text:
                    parts = race_class_text.lower().split()

                    # Common D&D races (including multi-word races)
                    races = ['human', 'elf', 'dwarf', 'halfling', 'gnome', 'half-elf', 'half-orc',
                             'tiefling', 'dragonborn', 'dusk elf', 'vistani', 'wereraven']

                    # Try to match race
                    for known_race in races:
                        race_words = known_race.split()
                        if len(parts) >= len(race_words):
                            if ' '.join(parts[:len(race_words)]) == known_race:
                                race = known_race.title()
                                # Rest is class
                                if len(parts) > len(race_words):
                                    class_name = ' '.join(parts[len(race_words):]).title()
                                break

                    # If no race found, assume first word is race and rest is class
                    if not race and parts:
                        race = parts[0].title()
                        if len(parts) > 1:
                            class_name = ' '.join(parts[1:]).title()

                # Store race
                if race and not npc_cache[npc_name]['race']:
                    npc_cache[npc_name]['race'] = race

                # Store class if found in parentheses
                if class_name and not npc_cache[npc_name]['class']:
                    npc_cache[npc_name]['class'] = class_name

                # Extract class/role from following text if not in parentheses
                context_start = match.end()
                context_end = min(context_start + 200, len(content))
                context = content[context_start:context_end]

                if not npc_cache[npc_name]['class']:
                    class_match = re.search(r'is (?:a|an|the)\s+([a-z][a-z\s]+?)(?:\s+(?:and|who|with|\.|,))', context, re.IGNORECASE)
                    if class_match:
                        class_candidate = class_match.group(1).strip()
                        # Filter out common non-class descriptions
                        if class_candidate.lower() not in ['member', 'resident', 'close friend', 'the', 'a', 'an']:
                            npc_cache[npc_name]['class'] = class_candidate.title()

                # Extract faction from context
                faction_patterns = [
                    r'member of (?:the )?(.+?)(?:\.|,|\s+(?:and|who))',
                    r'belongs to (?:the )?(.+?)(?:\.|,|\s+(?:and|who))',
                    r'spymaster of (?:the )?(.+?)(?:\.|,|\s+(?:and|who))',
                    r'leader of (?:the )?(.+?)(?:\.|,|\s+(?:and|who))',
                ]

                for faction_pattern in faction_patterns:
                    faction_match = re.search(faction_pattern, context, re.IGNORECASE)
                    if faction_match:
                        faction = faction_match.group(1).strip()
                        # Clean up faction name
                        faction = re.sub(r'\[\[([^\]|]+).*?\]\]', r'\1', faction)  # Remove wikilinks
                        if faction and len(faction) < 50:  # Sanity check
                            npc_cache[npc_name]['factions'].add(faction)

                # Add location if in a specific location section
                if location_context and not npc_cache[npc_name]['home_base']:
                    npc_cache[npc_name]['home_base'] = location_context

                # Add arc
                if arc_name:
                    npc_cache[npc_name]['arcs'].add(arc_name)
                    npcs_with_arcs += 1

        except Exception as e:
            print(f"Warning: Error processing {source_file}: {e}")
            continue

    # Convert sets to lists for YAML serialization
    for npc_name in npc_cache:
        npc_cache[npc_name]['factions'] = list(npc_cache[npc_name]['factions'])
        npc_cache[npc_name]['arcs'] = list(npc_cache[npc_name]['arcs'])

    print(f"DEBUG: Total NPC-arc associations found: {npcs_with_arcs}")

    return dict(npc_cache)


def extract_location_context(file_path: Path, content: str) -> Optional[str]:
    """
    Extract location context from file path or section headings.
    """
    # Try to extract from file path
    path_str = str(file_path)

    # Check for specific locations in path
    location_keywords = {
        'Vallaki': 'Town of Vallaki',
        'Barovia': 'Village of Barovia',
        'Ravenloft': 'Castle Ravenloft',
        'Krezk': 'Village of Krezk',
        'Blue Water Inn': 'Blue Water Inn',
        'Wachterhaus': 'Wachterhaus',
    }

    for keyword, location in location_keywords.items():
        if keyword in path_str:
            return location

    # Try to extract from headings
    heading_match = re.search(r'^#+\s+(.+?)$', content, re.MULTILINE)
    if heading_match:
        heading = heading_match.group(1)
        for keyword, location in location_keywords.items():
            if keyword in heading:
                return location

    return None


def backfill_npc_comprehensive(
    frontmatter: Dict[str, Any],
    file_path: Path,
    npc_cache: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Backfill comprehensive NPC properties from cache.
    """
    changes = []

    # Only process NPCs
    if frontmatter.get('type') != 'NPC':
        return frontmatter, changes

    npc_name = frontmatter.get('name') or file_path.stem

    if npc_name in npc_cache:
        npc_data = npc_cache[npc_name]

        # Backfill race
        if 'race' not in frontmatter or not frontmatter['race']:
            if npc_data['race']:
                frontmatter['race'] = npc_data['race']
                changes.append(f"Added race: {npc_data['race']}")

        # Backfill class
        if 'class' not in frontmatter or not frontmatter['class']:
            if npc_data['class']:
                frontmatter['class'] = npc_data['class']
                changes.append(f"Added class: {npc_data['class']}")

        # Backfill or merge factions
        existing_factions = frontmatter.get('factions', []) or []
        if isinstance(existing_factions, str):
            existing_factions = [existing_factions]

        new_factions = npc_data['factions']
        if new_factions:
            # Convert to wikilinks
            new_factions_links = [f"[[{f}]]" if not f.startswith('[[') else f for f in new_factions]
            # Merge with existing
            all_factions = list(set(existing_factions + new_factions_links))
            if all_factions != existing_factions:
                frontmatter['factions'] = all_factions
                changes.append(f"Added/merged factions: {', '.join(new_factions[:3])}...")

        # Backfill home_base if missing
        if 'home_base' not in frontmatter or not frontmatter['home_base']:
            if npc_data['home_base']:
                frontmatter['home_base'] = f"[[{npc_data['home_base']}]]"
                changes.append(f"Added home_base: {npc_data['home_base']}")

        # Backfill or merge arcs
        existing_arcs = frontmatter.get('arcs', []) or []
        if isinstance(existing_arcs, str):
            existing_arcs = [existing_arcs]

        new_arcs = npc_data['arcs']
        if new_arcs:
            # Convert to wikilinks
            new_arcs_links = [f"[[{a}]]" if not a.startswith('[[') else a for a in new_arcs]
            # Merge with existing
            all_arcs = list(set(existing_arcs + new_arcs_links))
            if all_arcs != existing_arcs:
                frontmatter['arcs'] = all_arcs
                changes.append(f"Added/merged arcs: {', '.join([a.replace('[[', '').replace(']]', '') for a in new_arcs_links[:2]])}...")

    return frontmatter, changes


def process_file(
    file_path: Path,
    npc_cache: Dict[str, Dict[str, Any]],
    dry_run: bool = True
) -> Tuple[bool, List[str]]:
    """Process a single markdown file to backfill properties."""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        fm_text, body, delimiter = extract_frontmatter(content)

        if not fm_text:
            return False, []

        # Parse frontmatter
        frontmatter = parse_frontmatter(fm_text)

        all_changes = []

        # Backfill NPC properties
        frontmatter, changes = backfill_npc_comprehensive(frontmatter, file_path, npc_cache)
        all_changes.extend(changes)

        if not all_changes:
            return False, []

        # Serialize back to YAML
        new_fm_text = serialize_frontmatter(frontmatter)

        # Reconstruct file content
        new_content = f"{delimiter}\n{new_fm_text}{delimiter}\n{body}"

        if not dry_run:
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return True, all_changes

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, [f"Error: {e}"]


def create_backup(vault_path: Path) -> Path:
    """Create a backup of the vault before backfilling."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_before_comprehensive_backfill_{timestamp}"
    backup_path = vault_path.parent / backup_name

    print(f"Creating backup at: {backup_path}")
    shutil.copytree(vault_path, backup_path, dirs_exist_ok=True)
    print(f"✓ Backup created successfully")

    return backup_path


def main():
    """Main backfill script."""
    # Get vault path
    script_dir = Path(__file__).parent
    vault_path = script_dir.parent

    print("=" * 80)
    print("Comprehensive NPC Property Backfill Script")
    print("=" * 80)
    print(f"Vault path: {vault_path}")
    print()

    # Ask for confirmation
    print("This script will:")
    print("  - Extract NPC data (race, class, factions, home_base, arcs)")
    print("  - From Arc and CoS-WotC source documents")
    print("  - Backfill missing properties for all NPCs")
    print("  - Create a backup before making changes")
    print()

    mode = input("Run in (d)ry-run mode or (b)ackfill mode? [d/b]: ").strip().lower()
    dry_run = mode != 'b'

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print("\n⚠️  BACKFILL MODE - Files will be modified!\n")
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm != 'YES':
            print("Backfill cancelled.")
            return

        # Create backup
        backup_path = create_backup(vault_path)
        print()

    # Build NPC cache from source documents
    print("Building comprehensive NPC cache from source documents...")
    npc_cache = build_comprehensive_npc_cache(vault_path)
    print(f"✓ Found data for {len(npc_cache)} NPCs\n")

    # Show sample of what was found
    print("Sample NPCs found:")
    for i, (npc_name, npc_data) in enumerate(list(npc_cache.items())[:5]):
        print(f"  - {npc_name}: race={npc_data['race']}, class={npc_data['class']}, "
              f"factions={len(npc_data['factions'])}, arcs={len(npc_data['arcs'])}")
    print()

    # Find all NPC markdown files
    npc_files = list(vault_path.glob("DM Wiki/Entities/NPCs/*.md"))
    print(f"Found {len(npc_files)} NPC files\n")

    # Process files
    modified_count = 0
    total_changes = 0

    for npc_file in npc_files:
        was_modified, changes = process_file(npc_file, npc_cache, dry_run=dry_run)

        if was_modified:
            modified_count += 1
            total_changes += len(changes)

            # Print relative path
            rel_path = npc_file.relative_to(vault_path)
            print(f"\n{'[DRY RUN] ' if dry_run else ''}✏️  {rel_path}")
            for change in changes:
                print(f"    - {change}")

    # Summary
    print("\n" + "=" * 80)
    print("BACKFILL SUMMARY")
    print("=" * 80)
    print(f"NPC files processed: {len(npc_files)}")
    print(f"Files modified: {modified_count}")
    print(f"Total changes: {total_changes}")

    if dry_run:
        print("\n✓ Dry run complete. No files were modified.")
        print("  Run with 'b' to apply changes.")
    else:
        print(f"\n✓ Backfill complete!")
        print(f"  Backup saved at: {backup_path}")

    print("=" * 80)


if __name__ == "__main__":
    main()
