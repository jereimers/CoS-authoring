#!/usr/bin/env python3
"""
Faction Property Backfill Script
Backfills:
- type: Faction
- arcs: from Arc document mentions
- notable_npcs: from NPC faction properties
- Cleans up [None] values to []
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
import shutil
from datetime import datetime
from collections import defaultdict


def extract_frontmatter(content: str) -> Tuple[str, str, str]:
    yaml_match = re.match(r'^---\s*\n(.*?\n)---\s*\n(.*)', content, re.DOTALL)
    if yaml_match:
        return yaml_match.group(1), yaml_match.group(2), '---'
    return '', content, ''


def parse_frontmatter(fm_text: str) -> Dict[str, Any]:
    if not fm_text.strip():
        return {}
    try:
        return yaml.safe_load(fm_text) or {}
    except:
        return {}


def serialize_frontmatter(frontmatter: Dict[str, Any]) -> str:
    if not frontmatter:
        return ''
    return yaml.safe_dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False, width=100)


def normalize_name(name: str) -> str:
    name = name.split('/')[-1] if '/' in name else name
    name = name.split('|')[0] if '|' in name else name
    name = name.strip('[]')  # Remove wikilink brackets
    return name.strip()


def get_known_faction_names(vault_path: Path) -> Dict[str, List[str]]:
    """Build a map of faction names to their aliases."""
    faction_files = list(vault_path.glob("DM Wiki/Entities/Factions/*.md"))
    faction_names = defaultdict(list)

    for faction_file in faction_files:
        try:
            with open(faction_file, 'r', encoding='utf-8') as f:
                fm_text, _, _ = extract_frontmatter(f.read())

            fm = parse_frontmatter(fm_text)
            # Use the 'name' property if available, otherwise filename
            faction_name = fm.get('name') or faction_file.stem
            faction_names[faction_name].append(faction_name)

            # Add aliases
            aliases = fm.get('aliases', [])
            if isinstance(aliases, str):
                aliases = [aliases]
            if aliases and aliases != [None]:
                for alias in aliases:
                    if alias and alias != faction_name:
                        faction_names[faction_name].append(alias)
        except:
            continue

    return faction_names


def get_npcs_by_faction(vault_path: Path) -> Dict[str, List[str]]:
    """Map faction names to NPCs that belong to them."""
    faction_to_npcs = defaultdict(set)
    npc_files = list(vault_path.glob("DM Wiki/Entities/NPCs/*.md"))

    print(f"Scanning {len(npc_files)} NPC files for faction memberships...")
    for npc_file in npc_files:
        try:
            with open(npc_file, 'r', encoding='utf-8') as f:
                fm_text, _, _ = extract_frontmatter(f.read())

            frontmatter = parse_frontmatter(fm_text)
            if frontmatter.get('type') == 'NPC':
                npc_name = frontmatter.get('name') or npc_file.stem

                factions = frontmatter.get('factions', [])
                if isinstance(factions, str):
                    factions = [factions]

                for faction in factions:
                    if faction:
                        faction_name = normalize_name(faction)
                        faction_to_npcs[faction_name].add(npc_name)
        except:
            continue

    return {k: list(v) for k, v in faction_to_npcs.items()}


def get_factions_by_arc(vault_path: Path, known_factions: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Map arc names to factions mentioned in them (wikilinked or plain text)."""
    arc_files = list(vault_path.glob("Source/CoS-Reloaded/**/Arc *.md"))

    print(f"Scanning {len(arc_files)} Arc files for {len(known_factions)} known factions...")
    arc_to_factions = defaultdict(set)

    for arc_file in arc_files:
        arc_name = arc_file.stem
        try:
            with open(arc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Search for each known faction (by name and aliases)
            for faction_name, variants in known_factions.items():
                for variant in variants:
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(pattern, content):
                        arc_to_factions[arc_name].add(faction_name)
                        break  # Found this faction, move to next
        except:
            continue

    return {k: list(v) for k, v in arc_to_factions.items()}


def clean_null_list(value):
    """Clean up lists that contain None values."""
    if value is None or value == [None]:
        return []
    if isinstance(value, list):
        return [v for v in value if v is not None]
    return value


def main():
    script_dir = Path(__file__).parent
    vault_path = script_dir.parent

    print("=" * 80)
    print("Faction Property Backfill Script")
    print("=" * 80)
    print()

    mode = input("Run in (d)ry-run or (b)ackfill mode? [d/b]: ").strip().lower()
    dry_run = mode != 'b'

    if not dry_run:
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm != 'YES':
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = vault_path.parent / f"backup_faction_backfill_{timestamp}"
        shutil.copytree(vault_path, backup_path, dirs_exist_ok=True)
        print(f"✓ Backup at: {backup_path}\n")

    # Build data
    print("Building known faction names...")
    known_factions = get_known_faction_names(vault_path)
    print(f"Found {len(known_factions)} known factions\n")

    npcs_by_faction = get_npcs_by_faction(vault_path)
    factions_by_arc = get_factions_by_arc(vault_path, known_factions)

    # Invert arc mapping: faction -> arcs
    faction_to_arcs = defaultdict(set)
    for arc, factions in factions_by_arc.items():
        for faction in factions:
            faction_to_arcs[faction].add(arc)

    print(f"\nData collected:")
    print(f"  - {len(npcs_by_faction)} factions have NPCs")
    print(f"  - {len(faction_to_arcs)} factions found in Arcs\n")

    # Process faction files
    faction_files = list(vault_path.glob("DM Wiki/Entities/Factions/*.md"))
    print(f"Processing {len(faction_files)} faction files...\n")

    modified = 0
    changes = 0

    for faction_file in faction_files:
        try:
            with open(faction_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm_text, body, delim = extract_frontmatter(content)
            if not delim:
                # Add minimal frontmatter if missing
                fm = {}
                delim = '---'
            else:
                fm = parse_frontmatter(fm_text)

            faction_name = fm.get('name') or faction_file.stem
            file_changes = []

            # Add type: Faction if missing
            if not fm.get('type'):
                fm['type'] = 'Faction'
                file_changes.append("Added type: Faction")

            # Clean up null values in arcs
            if 'arcs' in fm:
                cleaned = clean_null_list(fm['arcs'])
                if cleaned != fm['arcs']:
                    fm['arcs'] = cleaned
                    file_changes.append("Cleaned null values from arcs")

            # Backfill arcs
            if faction_name in faction_to_arcs:
                existing = fm.get('arcs', []) or []
                existing = clean_null_list(existing)

                new_arcs = [f"[[{a}]]" if not a.startswith('[[') else a for a in faction_to_arcs[faction_name]]
                all_arcs = list(set(existing + new_arcs))

                if all_arcs != existing:
                    fm['arcs'] = all_arcs
                    file_changes.append(f"Added {len(new_arcs)} arcs")

            # Clean up null values in notable_npcs
            if 'notable_npcs' in fm:
                cleaned = clean_null_list(fm['notable_npcs'])
                if cleaned != fm['notable_npcs']:
                    fm['notable_npcs'] = cleaned
                    file_changes.append("Cleaned null values from notable_npcs")

            # Backfill notable_npcs
            if faction_name in npcs_by_faction:
                existing = fm.get('notable_npcs', []) or []
                existing = clean_null_list(existing)

                new_npcs = [f"[[{n}]]" if not n.startswith('[[') else n for n in npcs_by_faction[faction_name]]
                all_npcs = list(set(existing + new_npcs))

                if all_npcs != existing:
                    fm['notable_npcs'] = all_npcs
                    file_changes.append(f"Added {len(new_npcs)} NPCs")

            if file_changes:
                modified += 1
                changes += len(file_changes)

                if not dry_run:
                    new_content = f"{delim}\n{serialize_frontmatter(fm)}{delim}\n{body}"
                    with open(faction_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                rel = faction_file.relative_to(vault_path)
                print(f"{'[DRY RUN] ' if dry_run else ''}✏️  {rel}")
                for change in file_changes:
                    print(f"    - {change}")

        except Exception as e:
            continue

    print("\n" + "=" * 80)
    print(f"Files processed: {len(faction_files)}")
    print(f"Files modified: {modified}")
    print(f"Total changes: {changes}")
    if dry_run:
        print("\n✓ Dry run complete. Run with 'b' to apply.")
    else:
        print("\n✓ Backfill complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
