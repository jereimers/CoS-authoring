#!/usr/bin/env python3
"""
Property Backfill Script
Adds missing properties to content, especially the 'region' property for NPCs.

Region extraction rules:
- Vallaki: If location contains "Vallaki" or is in Town of Vallaki folder
- Barovia: If location contains "Barovia" (village) or is in Village of Barovia folder
- Ravenloft: If location contains "Ravenloft" or is in Castle Ravenloft folder
- Krezk: If location contains "Krezk"
- Mount Ghakis: If location contains "Ghakis"
- Wilderness: Default for anything else

Profile extraction:
- Extracts roleplay properties (resonance, emotions, motivations, inspirations)
  from Profile callouts in Arc documents
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import shutil
from datetime import datetime
from collections import defaultdict


# Region detection keywords
REGION_KEYWORDS = {
    'Vallaki': ['Vallaki', 'Blue Water Inn', 'Burgomaster\'s Mansion', 'Wachterhaus',
                'St. Andral', 'Blinsky', 'Coffin Maker', 'Arasek', 'Town Square'],
    'Barovia': ['Village of Barovia', 'Blood of the Vine', 'Church (Barovia)',
                'Bildrath', 'Burgomaster\'s Mansion (Barovia)'],
    'Ravenloft': ['Castle Ravenloft', 'Ravenloft'],
    'Krezk': ['Krezk', 'Abbey of Saint Markovia'],
    'Mount Ghakis': ['Mt Ghakis', 'Mount Ghakis', 'Ghakis'],
}


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


def extract_location_string(location_value: Any) -> str:
    """
    Extract location string from various formats.
    Could be: "[[Location]]", ["[[Loc1]]", "[[Loc2]]"], or plain text.
    """
    if not location_value:
        return ''

    if isinstance(location_value, str):
        return location_value
    elif isinstance(location_value, list) and len(location_value) > 0:
        return location_value[0]  # Use first location

    return ''


def extract_profile_from_text(profile_text: str) -> Dict[str, Any]:
    """
    Extract roleplay properties from a Profile callout text.
    Returns dict with: resonance, emotions, motivations, inspirations
    """
    profile_data = {}

    # Extract Resonance
    resonance_match = re.search(r'\*\*\*Resonance\.\*\*\*\s+(.+?)(?=\n\n|\*\*\*)', profile_text, re.DOTALL)
    if resonance_match:
        resonance_text = resonance_match.group(1).strip()
        # Remove wiki links and clean up
        resonance_text = re.sub(r'\[\[([^\]]+)\|([^\]]+)\]\]', r'\2', resonance_text)  # [[link|text]] -> text
        resonance_text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', resonance_text)  # [[link]] -> link
        profile_data['resonance'] = resonance_text

    # Extract Emotions
    emotions_match = re.search(r'\*\*\*Emotions\.\*\*\*\s+.+?feels\s+(.+?)\.', profile_text, re.DOTALL)
    if emotions_match:
        emotions_text = emotions_match.group(1).strip()
        # Split by commas and "and"
        emotions_list = re.split(r',\s*(?:and\s+)?|\s+and\s+', emotions_text)
        emotions_list = [e.strip() for e in emotions_list if e.strip()]
        profile_data['emotions'] = emotions_list

    # Extract Motivations
    motivations_match = re.search(r'\*\*\*Motivations\.\*\*\*\s+.+?wants to\s+(.+?)\.', profile_text, re.DOTALL)
    if motivations_match:
        motivations_text = motivations_match.group(1).strip()
        # Split by commas and "and"
        motivations_list = re.split(r',\s*(?:and\s+)?|\s+and\s+', motivations_text)
        motivations_list = [m.strip() for m in motivations_list if m.strip()]
        profile_data['motivations'] = motivations_list

    # Extract Inspirations
    inspirations_match = re.search(r'\*\*\*Inspirations\.\*\*\*\s+When playing.+?channel\s+(.+?)\.', profile_text, re.DOTALL)
    if inspirations_match:
        inspirations_text = inspirations_match.group(1).strip()
        # Split by commas and "and"
        inspirations_list = re.split(r',\s*(?:and\s+)?|\s+and\s+', inspirations_text)
        inspirations_list = [i.strip() for i in inspirations_list if i.strip()]
        profile_data['inspirations'] = inspirations_list

    return profile_data


def build_profile_cache(vault_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Build a cache of all NPC profiles from Arc documents.
    Returns: {npc_name: profile_data}
    """
    profile_cache = {}

    # Find all Arc documents
    arc_files = list(vault_path.glob("Source/CoS-Reloaded/**/*.md"))
    arc_files.extend(list(vault_path.glob("Source/homebrew/**/*.md")))

    for arc_file in arc_files:
        try:
            with open(arc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all profile callouts
            # Pattern: > [!profile]+ **Profile: [[NPC Name]]**
            profile_pattern = r'> \[!profile\]\+\s+\*\*Profile:\s+\[\[([^\]]+)\]\]\*\*\s*\n((?:>.*\n)*)'

            for match in re.finditer(profile_pattern, content, re.MULTILINE):
                npc_name = match.group(1).strip()
                profile_block = match.group(2)

                # Remove "> " from each line
                profile_text = '\n'.join(line[2:] if line.startswith('> ') else line
                                        for line in profile_block.split('\n'))

                # Extract profile data
                profile_data = extract_profile_from_text(profile_text)

                if profile_data:
                    # Normalize NPC name (remove namespaces like "DM Wiki/Entities/NPCs/")
                    npc_name_clean = npc_name.split('/')[-1] if '/' in npc_name else npc_name
                    profile_cache[npc_name_clean] = profile_data

        except Exception as e:
            print(f"Warning: Error processing {arc_file}: {e}")
            continue

    return profile_cache


def determine_region(current_location: Any, home_base: Any, file_path: Path) -> Optional[str]:
    """
    Determine region based on location properties and file path.
    Returns: region name or None if can't determine
    """
    # Extract location strings
    current_loc_str = extract_location_string(current_location)
    home_base_str = extract_location_string(home_base)

    # Combine both for checking
    location_text = f"{current_loc_str} {home_base_str}".lower()

    # Check against region keywords
    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in location_text:
                return region

    # If location is a wikilink, try to resolve it by checking file existence
    # Look for patterns like [[Location Name]]
    link_pattern = r'\[\[([^\]]+)\]\]'
    links = re.findall(link_pattern, current_loc_str + home_base_str)

    if links:
        # Check if any linked location is in a known region folder
        for link in links:
            # Check for Vallaki
            if 'vallaki' in link.lower():
                return 'Vallaki'
            elif 'barovia' in link.lower() and 'village' in link.lower():
                return 'Barovia'
            elif 'ravenloft' in link.lower():
                return 'Ravenloft'
            elif 'krezk' in link.lower():
                return 'Krezk'
            elif 'ghakis' in link.lower():
                return 'Mount Ghakis'

    # Default to Wilderness if we can't determine
    return 'Wilderness'


def backfill_npc_properties(
    frontmatter: Dict[str, Any],
    file_path: Path,
    profile_cache: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Add missing properties to NPC frontmatter:
    - region (from location)
    - roleplay properties (from profile cache)
    Returns: (updated_frontmatter, list_of_changes)
    """
    changes = []

    # Only process NPCs
    if frontmatter.get('type') != 'NPC':
        return frontmatter, changes

    # Backfill region
    if 'region' not in frontmatter:
        current_location = frontmatter.get('current_location')
        home_base = frontmatter.get('home_base')
        region = determine_region(current_location, home_base, file_path)

        if region:
            frontmatter['region'] = region
            changes.append(f"Added region: {region}")

    # Backfill roleplay properties from profile
    npc_name = frontmatter.get('name') or file_path.stem

    if npc_name in profile_cache:
        profile_data = profile_cache[npc_name]

        # Backfill resonance
        if 'resonance' not in frontmatter or not frontmatter['resonance']:
            if 'resonance' in profile_data:
                frontmatter['resonance'] = profile_data['resonance']
                changes.append(f"Added resonance from profile")

        # Backfill emotions
        if 'emotions' not in frontmatter or not frontmatter['emotions']:
            if 'emotions' in profile_data:
                frontmatter['emotions'] = profile_data['emotions']
                changes.append(f"Added emotions: {', '.join(profile_data['emotions'][:3])}...")

        # Backfill motivations
        if 'motivations' not in frontmatter or not frontmatter['motivations']:
            if 'motivations' in profile_data:
                frontmatter['motivations'] = profile_data['motivations']
                changes.append(f"Added motivations from profile")

        # Backfill inspirations
        if 'inspirations' not in frontmatter or not frontmatter['inspirations']:
            if 'inspirations' in profile_data:
                frontmatter['inspirations'] = profile_data['inspirations']
                changes.append(f"Added inspirations: {', '.join(profile_data['inspirations'][:2])}...")

    return frontmatter, changes


def backfill_session_properties(frontmatter: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Add missing session properties like plot_threads_introduced, plot_threads_advanced.
    Returns: (updated_frontmatter, list_of_changes)
    """
    changes = []

    # Only process sessions
    if frontmatter.get('type') != 'session':
        return frontmatter, changes

    # Add plot_threads_introduced if missing
    if 'plot_threads_introduced' not in frontmatter:
        frontmatter['plot_threads_introduced'] = []
        changes.append("Added plot_threads_introduced: []")

    # Add plot_threads_advanced if missing
    if 'plot_threads_advanced' not in frontmatter:
        frontmatter['plot_threads_advanced'] = []
        changes.append("Added plot_threads_advanced: []")

    return frontmatter, changes


def process_file(
    file_path: Path,
    profile_cache: Dict[str, Dict[str, Any]],
    dry_run: bool = True
) -> Tuple[bool, List[str]]:
    """
    Process a single markdown file to backfill properties.
    Returns: (was_modified, list_of_changes)
    """
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

        # Backfill NPC properties (region + roleplay properties)
        frontmatter, changes = backfill_npc_properties(frontmatter, file_path, profile_cache)
        all_changes.extend(changes)

        # Backfill session properties
        frontmatter, changes = backfill_session_properties(frontmatter)
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
    backup_name = f"backup_before_backfill_{timestamp}"
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
    print("Property Backfill Script")
    print("=" * 80)
    print(f"Vault path: {vault_path}")
    print()

    # Ask for confirmation
    print("This script will:")
    print("  - Add 'region' property to all NPCs based on their location")
    print("  - Add roleplay properties to NPCs from Profile callouts in Arcs")
    print("  - Add plot_threads properties to sessions")
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

    # Build profile cache from Arc documents
    print("Building profile cache from Arc documents...")
    profile_cache = build_profile_cache(vault_path)
    print(f"✓ Found {len(profile_cache)} NPC profiles in Arc documents\n")

    # Find all markdown files
    md_files = list(vault_path.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files\n")

    # Process files
    modified_count = 0
    total_changes = 0

    for md_file in md_files:
        was_modified, changes = process_file(md_file, profile_cache, dry_run=dry_run)

        if was_modified:
            modified_count += 1
            total_changes += len(changes)

            # Print relative path
            rel_path = md_file.relative_to(vault_path)
            print(f"\n{'[DRY RUN] ' if dry_run else ''}✏️  {rel_path}")
            for change in changes:
                print(f"    - {change}")

    # Summary
    print("\n" + "=" * 80)
    print("BACKFILL SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(md_files)}")
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
