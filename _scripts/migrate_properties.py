#!/usr/bin/env python3
"""
Property Migration Script
Standardizes property names across all markdown files in the vault.

Changes:
- arc/arc(s) → arcs
- location/location(s) → locations
- combat? → combat
- has_recap? → has_recap
- scene → scenes
- encounter → encounters
- item(s) → items
- barovian_date(s) → barovian_dates
- Removes 'acts' property from all files
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
import shutil
from datetime import datetime

# Property migration map: old_name → new_name
PROPERTY_MIGRATIONS = {
    'arc': 'arcs',
    'arc(s)': 'arcs',
    'location': 'locations',
    'location(s)': 'locations',
    'combat?': 'combat',
    'has_recap?': 'has_recap',
    'scene': 'scenes',
    'encounter': 'encounters',
    'item(s)': 'items',
    'barovian_date(s)': 'barovian_dates',
}

# Properties to remove
PROPERTIES_TO_REMOVE = ['acts']


def extract_frontmatter(content: str) -> Tuple[str, str, str]:
    """
    Extract frontmatter, body, and delimiter from markdown content.
    Returns: (frontmatter_yaml, body, delimiter)
    """
    # Check for YAML frontmatter with --- delimiters
    yaml_match = re.match(r'^---\s*\n(.*?\n)---\s*\n(.*)', content, re.DOTALL)
    if yaml_match:
        return yaml_match.group(1), yaml_match.group(2), '---'

    # No frontmatter found
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


def migrate_properties(frontmatter: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Migrate property names in frontmatter dictionary.
    Returns: (updated_frontmatter, list_of_changes)
    """
    changes = []
    new_fm = {}

    for key, value in frontmatter.items():
        # Check if property should be removed
        if key in PROPERTIES_TO_REMOVE:
            changes.append(f"Removed property: {key}")
            continue

        # Check if property needs migration
        if key in PROPERTY_MIGRATIONS:
            new_key = PROPERTY_MIGRATIONS[key]
            # If target key already exists, merge values if they're lists
            if new_key in new_fm:
                if isinstance(new_fm[new_key], list) and isinstance(value, list):
                    # Merge lists and deduplicate
                    new_fm[new_key] = list(set(new_fm[new_key] + value))
                    changes.append(f"Merged {key} → {new_key} (combined lists)")
                else:
                    # Keep the first value encountered
                    changes.append(f"Skipped {key} → {new_key} (target already exists)")
            else:
                new_fm[new_key] = value
                changes.append(f"Renamed: {key} → {new_key}")
        else:
            # Keep property as-is
            new_fm[key] = value

    return new_fm, changes


def serialize_frontmatter(frontmatter: Dict[str, Any]) -> str:
    """Serialize frontmatter dictionary back to YAML string."""
    if not frontmatter:
        return ''

    # Use safe_dump with custom settings for readability
    yaml_str = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )
    return yaml_str


def process_file(file_path: Path, dry_run: bool = True) -> Tuple[bool, List[str]]:
    """
    Process a single markdown file to migrate properties.
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

        # Migrate properties
        new_frontmatter, changes = migrate_properties(frontmatter)

        if not changes:
            return False, []

        # Serialize back to YAML
        new_fm_text = serialize_frontmatter(new_frontmatter)

        # Reconstruct file content
        new_content = f"{delimiter}\n{new_fm_text}{delimiter}\n{body}"

        if not dry_run:
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return True, changes

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, [f"Error: {e}"]


def create_backup(vault_path: Path) -> Path:
    """Create a backup of the vault before migration."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_before_migration_{timestamp}"
    backup_path = vault_path.parent / backup_name

    print(f"Creating backup at: {backup_path}")
    shutil.copytree(vault_path, backup_path, dirs_exist_ok=True)
    print(f"✓ Backup created successfully")

    return backup_path


def main():
    """Main migration script."""
    # Get vault path
    script_dir = Path(__file__).parent
    vault_path = script_dir.parent

    print("=" * 80)
    print("Property Migration Script")
    print("=" * 80)
    print(f"Vault path: {vault_path}")
    print()

    # Ask for confirmation
    print("This script will:")
    print("  - Standardize property names (arc→arcs, location→locations, etc.)")
    print("  - Remove 'acts' property from all files")
    print("  - Create a backup before making changes")
    print()

    mode = input("Run in (d)ry-run mode or (m)igrate mode? [d/m]: ").strip().lower()
    dry_run = mode != 'm'

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print("\n⚠️  MIGRATION MODE - Files will be modified!\n")
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm != 'YES':
            print("Migration cancelled.")
            return

        # Create backup
        backup_path = create_backup(vault_path)
        print()

    # Find all markdown files
    md_files = list(vault_path.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files\n")

    # Process files
    modified_count = 0
    total_changes = 0

    for md_file in md_files:
        was_modified, changes = process_file(md_file, dry_run=dry_run)

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
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(md_files)}")
    print(f"Files modified: {modified_count}")
    print(f"Total changes: {total_changes}")

    if dry_run:
        print("\n✓ Dry run complete. No files were modified.")
        print("  Run with 'm' to apply changes.")
    else:
        print(f"\n✓ Migration complete!")
        print(f"  Backup saved at: {backup_path}")

    print("=" * 80)


if __name__ == "__main__":
    main()
