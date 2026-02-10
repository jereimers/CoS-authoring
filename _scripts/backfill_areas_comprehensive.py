#!/usr/bin/env python3
"""
Comprehensive Area Property Backfill Script
Extracts Area properties from Arc documents, CoS-WotC, and NPC files:
- arcs: which arcs feature this area
- notable_npcs: NPCs associated with this area
- connected_locations: areas that connect to this one
- key_factions: factions operating in this area
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


def normalize_name(name: str) -> str:
    """Normalize name for matching (remove namespace, pipes, etc.)."""
    name = name.split('/')[-1] if '/' in name else name
    name = name.split('|')[0] if '|' in name else name
    return name.strip()


def get_known_areas(vault_path: Path) -> Dict[str, List[str]]:
    """
    Build a dictionary of known area names and their aliases.
    Returns: {primary_name: [alias1, alias2, ...]}
    """
    area_names = {}
    area_files = list(vault_path.glob("DM Wiki/Entities/Areas/**/*.md"))

    for area_file in area_files:
        try:
            with open(area_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm_text, _, _ = extract_frontmatter(content)
            frontmatter = parse_frontmatter(fm_text)

            if frontmatter.get('type') == 'Area':
                name = frontmatter.get('name') or area_file.stem
                aliases = frontmatter.get('aliases', []) or []
                if isinstance(aliases, str):
                    aliases = [aliases]

                all_names = [name] + aliases
                area_names[name] = all_names
        except Exception:
            continue

    return area_names


def get_npcs_by_location(vault_path: Path) -> Dict[str, List[str]]:
    """
    Build a mapping of area names to NPCs that are located there.
    Returns: {area_name: [npc1, npc2, ...]}
    """
    location_to_npcs = defaultdict(list)
    npc_files = list(vault_path.glob("DM Wiki/Entities/NPCs/*.md"))

    for npc_file in npc_files:
        try:
            with open(npc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm_text, _, _ = extract_frontmatter(content)
            frontmatter = parse_frontmatter(fm_text)

            if frontmatter.get('type') == 'NPC':
                npc_name = frontmatter.get('name') or npc_file.stem

                # Check current_location
                current_loc = frontmatter.get('current_location')
                if current_loc:
                    loc_name = normalize_name(current_loc)
                    location_to_npcs[loc_name].append(npc_name)

                # Check home_base
                home_base = frontmatter.get('home_base')
                if home_base:
                    loc_name = normalize_name(home_base)
                    location_to_npcs[loc_name].append(npc_name)

        except Exception:
            continue

    return dict(location_to_npcs)


def build_area_cache(vault_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Build comprehensive Area data cache from all source documents.
    Returns: {area_name: {arcs, connected_locations, key_factions}}
    """
    area_cache = defaultdict(lambda: {
        'arcs': set(),
        'connected_locations': set(),
        'key_factions': set(),
        'notable_npcs': set(),
    })

    # Get known areas and their aliases
    print("Building list of known areas...")
    known_areas = get_known_areas(vault_path)
    print(f"Found {len(known_areas)} known areas")

    # Get NPCs by location
    print("Mapping NPCs to locations...")
    npcs_by_location = get_npcs_by_location(vault_path)

    # Add NPCs to area cache
    for area_name, npc_list in npcs_by_location.items():
        area_cache[area_name]['notable_npcs'].update(npc_list)

    # Find all source documents
    arc_files = list(vault_path.glob("Source/CoS-Reloaded/**/*.md"))
    wotc_files = list(vault_path.glob("Source/CoS-WotC/**/*.md"))
    all_source_files = arc_files + wotc_files

    print(f"Scanning {len(arc_files)} Arc documents and {len(wotc_files)} WotC documents...")

    for source_file in all_source_files:
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract arc name from filename if it's an Arc file
            arc_name = None
            if 'CoS-Reloaded' in str(source_file):
                filename = source_file.name
                if filename.startswith('Arc '):
                    arc_name = filename.replace('.md', '')

            # Search for mentions of known areas
            for primary_name, all_names in known_areas.items():
                area_mentioned = False

                for name_variant in all_names:
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(name_variant) + r'\b'
                    if re.search(pattern, content, re.IGNORECASE):
                        area_mentioned = True
                        break

                if area_mentioned:
                    # Add arc association
                    if arc_name:
                        area_cache[primary_name]['arcs'].add(arc_name)

                    # Look for connected locations mentioned near this area
                    # Search for patterns like "connects to X", "leads to X", "path to X"
                    for check_name, check_aliases in known_areas.items():
                        if check_name == primary_name:
                            continue

                        for alias in check_aliases:
                            # Look for connection phrases
                            patterns = [
                                rf'{re.escape(name_variant)}[^.]*?\b(?:connects? to|leads? to|path to|road to|route to|adjacent to|near)\b[^.]*?\b{re.escape(alias)}\b',
                                rf'\b{re.escape(alias)}\b[^.]*?\b(?:connects? to|leads? to|path to|road to|route to|adjacent to|near)\b[^.]*?\b{re.escape(name_variant)}\b',
                            ]

                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                                    area_cache[primary_name]['connected_locations'].add(check_name)
                                    break

                    # Look for faction mentions in context
                    # Find paragraphs mentioning this area and extract factions
                    sentences = re.split(r'[.!?]\s+', content)
                    for sentence in sentences:
                        if any(re.search(r'\b' + re.escape(name) + r'\b', sentence, re.IGNORECASE)
                               for name in all_names):
                            # Look for faction keywords
                            faction_keywords = [
                                'Keepers of the Feather', 'Wachters', 'Vallakoviches',
                                'Church of the Morninglord', 'Vistani', 'Dusk Elves',
                                "Strahd's Spies", 'Order of the Silver Dragon',
                                'Barovian Villagers', 'Vallakians'
                            ]

                            for faction in faction_keywords:
                                if faction.lower() in sentence.lower():
                                    area_cache[primary_name]['key_factions'].add(faction)

        except Exception as e:
            continue

    # Convert sets to lists
    for area_name in area_cache:
        area_cache[area_name]['arcs'] = list(area_cache[area_name]['arcs'])
        area_cache[area_name]['connected_locations'] = list(area_cache[area_name]['connected_locations'])
        area_cache[area_name]['key_factions'] = list(area_cache[area_name]['key_factions'])
        area_cache[area_name]['notable_npcs'] = list(area_cache[area_name]['notable_npcs'])

    return dict(area_cache)


def backfill_area_properties(
    frontmatter: Dict[str, Any],
    file_path: Path,
    area_cache: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[str]]:
    """Backfill comprehensive Area properties from cache."""
    changes = []

    # Only process Areas
    if frontmatter.get('type') != 'Area':
        return frontmatter, changes

    area_name = frontmatter.get('name') or file_path.stem

    if area_name in area_cache:
        area_data = area_cache[area_name]

        # Backfill or merge arcs
        existing_arcs = frontmatter.get('arcs', []) or []
        if isinstance(existing_arcs, str):
            existing_arcs = [existing_arcs]
        # Remove null values
        existing_arcs = [a for a in existing_arcs if a]

        new_arcs = area_data['arcs']
        if new_arcs:
            new_arcs_links = [f"[[{a}]]" if not a.startswith('[[') else a for a in new_arcs]
            all_arcs = list(set(existing_arcs + new_arcs_links))
            if all_arcs != existing_arcs:
                frontmatter['arcs'] = all_arcs
                changes.append(f"Added/merged arcs: {', '.join([a.replace('[[', '').replace(']]', '') for a in new_arcs_links[:2]])}...")

        # Backfill or merge notable_npcs
        existing_npcs = frontmatter.get('notable_npcs', []) or []
        if isinstance(existing_npcs, str):
            existing_npcs = [existing_npcs]
        existing_npcs = [n for n in existing_npcs if n]

        new_npcs = area_data['notable_npcs']
        if new_npcs:
            new_npcs_links = [f"[[{n}]]" if not n.startswith('[[') else n for n in new_npcs]
            all_npcs = list(set(existing_npcs + new_npcs_links))
            if all_npcs != existing_npcs:
                frontmatter['notable_npcs'] = all_npcs
                changes.append(f"Added/merged notable_npcs: {len(new_npcs)} NPCs")

        # Backfill or merge connected_locations
        existing_locs = frontmatter.get('connected_locations', []) or []
        if isinstance(existing_locs, str):
            existing_locs = [existing_locs]
        existing_locs = [l for l in existing_locs if l]

        new_locs = area_data['connected_locations']
        if new_locs:
            new_locs_links = [f"[[{l}]]" if not l.startswith('[[') else l for l in new_locs]
            all_locs = list(set(existing_locs + new_locs_links))
            if all_locs != existing_locs:
                frontmatter['connected_locations'] = all_locs
                changes.append(f"Added/merged connected_locations: {len(new_locs)} locations")

        # Backfill or merge key_factions
        existing_factions = frontmatter.get('key_factions', []) or []
        if isinstance(existing_factions, str):
            existing_factions = [existing_factions]
        existing_factions = [f for f in existing_factions if f]

        new_factions = area_data['key_factions']
        if new_factions:
            new_factions_links = [f"[[{f}]]" if not f.startswith('[[') else f for f in new_factions]
            all_factions = list(set(existing_factions + new_factions_links))
            if all_factions != existing_factions:
                frontmatter['key_factions'] = all_factions
                changes.append(f"Added/merged key_factions: {', '.join(new_factions[:2])}...")

    return frontmatter, changes


def process_file(
    file_path: Path,
    area_cache: Dict[str, Dict[str, Any]],
    dry_run: bool = True
) -> Tuple[bool, List[str]]:
    """Process a single markdown file to backfill properties."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fm_text, body, delimiter = extract_frontmatter(content)
        if not fm_text:
            return False, []

        frontmatter = parse_frontmatter(fm_text)

        frontmatter, changes = backfill_area_properties(frontmatter, file_path, area_cache)

        if not changes:
            return False, []

        new_fm_text = serialize_frontmatter(frontmatter)
        new_content = f"{delimiter}\n{new_fm_text}{delimiter}\n{body}"

        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return True, changes

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, [f"Error: {e}"]


def create_backup(vault_path: Path) -> Path:
    """Create a backup of the vault before backfilling."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_before_area_backfill_{timestamp}"
    backup_path = vault_path.parent / backup_name

    print(f"Creating backup at: {backup_path}")
    shutil.copytree(vault_path, backup_path, dirs_exist_ok=True)
    print(f"✓ Backup created successfully")

    return backup_path


def main():
    """Main backfill script."""
    script_dir = Path(__file__).parent
    vault_path = script_dir.parent

    print("=" * 80)
    print("Comprehensive Area Property Backfill Script")
    print("=" * 80)
    print(f"Vault path: {vault_path}")
    print()

    print("This script will:")
    print("  - Extract area data (arcs, notable_npcs, connected_locations, key_factions)")
    print("  - From Arc documents, CoS-WotC chapters, and NPC files")
    print("  - Backfill missing properties for all Areas")
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

        backup_path = create_backup(vault_path)
        print()

    # Build area cache from source documents
    print("Building comprehensive area cache...")
    area_cache = build_area_cache(vault_path)
    print(f"✓ Found data for {len(area_cache)} areas\n")

    # Show sample
    print("Sample areas found:")
    for i, (area_name, area_data) in enumerate(list(area_cache.items())[:5]):
        print(f"  - {area_name}: arcs={len(area_data['arcs'])}, "
              f"npcs={len(area_data['notable_npcs'])}, "
              f"connected={len(area_data['connected_locations'])}, "
              f"factions={len(area_data['key_factions'])}")
    print()

    # Find all area files
    area_files = list(vault_path.glob("DM Wiki/Entities/Areas/**/*.md"))
    print(f"Found {len(area_files)} area files\n")

    # Process files
    modified_count = 0
    total_changes = 0

    for area_file in area_files:
        was_modified, changes = process_file(area_file, area_cache, dry_run=dry_run)

        if was_modified:
            modified_count += 1
            total_changes += len(changes)

            rel_path = area_file.relative_to(vault_path)
            print(f"\n{'[DRY RUN] ' if dry_run else ''}✏️  {rel_path}")
            for change in changes:
                print(f"    - {change}")

    # Summary
    print("\n" + "=" * 80)
    print("BACKFILL SUMMARY")
    print("=" * 80)
    print(f"Area files processed: {len(area_files)}")
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
