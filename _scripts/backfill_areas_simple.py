#!/usr/bin/env python3
"""
Simple Area Property Backfill Script
Quickly backfills:
- arcs: from Arc document mentions
- notable_npcs: from NPC location properties
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


def get_npcs_by_location(vault_path: Path) -> Dict[str, List[str]]:
    """Map area names to NPCs located there."""
    location_to_npcs = defaultdict(set)
    npc_files = list(vault_path.glob("DM Wiki/Entities/NPCs/*.md"))

    print(f"Scanning {len(npc_files)} NPC files for locations...")
    for npc_file in npc_files:
        try:
            with open(npc_file, 'r', encoding='utf-8') as f:
                fm_text, _, _ = extract_frontmatter(f.read())

            frontmatter = parse_frontmatter(fm_text)
            if frontmatter.get('type') == 'NPC':
                npc_name = frontmatter.get('name') or npc_file.stem

                for loc_key in ['current_location', 'home_base']:
                    loc = frontmatter.get(loc_key)
                    if loc:
                        loc_name = normalize_name(loc)
                        location_to_npcs[loc_name].add(npc_name)
        except:
            continue

    return {k: list(v) for k, v in location_to_npcs.items()}


def get_known_area_names(vault_path: Path) -> Dict[str, List[str]]:
    """Build a map of area names to their aliases."""
    area_files = list(vault_path.glob("DM Wiki/Entities/Areas/**/*.md"))
    area_names = defaultdict(list)

    for area_file in area_files:
        try:
            with open(area_file, 'r', encoding='utf-8') as f:
                fm_text, _, _ = extract_frontmatter(f.read())

            fm = parse_frontmatter(fm_text)
            if fm.get('type') == 'Area':
                area_name = fm.get('name') or area_file.stem
                area_names[area_name].append(area_name)

                # Add aliases
                aliases = fm.get('aliases', [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                for alias in aliases:
                    if alias and alias != area_name:
                        area_names[area_name].append(alias)
        except:
            continue

    return area_names


def get_areas_by_arc(vault_path: Path, known_areas: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Map arc names to areas mentioned in them (wikilinked or plain text)."""
    arc_files = list(vault_path.glob("Source/CoS-Reloaded/**/Arc *.md"))

    print(f"Scanning {len(arc_files)} Arc files for {len(known_areas)} known areas...")
    arc_to_areas = defaultdict(set)

    for arc_file in arc_files:
        arc_name = arc_file.stem
        try:
            with open(arc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Search for each known area (by name and aliases)
            for area_name, variants in known_areas.items():
                for variant in variants:
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(pattern, content):
                        arc_to_areas[arc_name].add(area_name)
                        break  # Found this area, move to next
        except:
            continue

    return {k: list(v) for k, v in arc_to_areas.items()}


def main():
    script_dir = Path(__file__).parent
    vault_path = script_dir.parent

    print("=" * 80)
    print("Simple Area Property Backfill Script")
    print("=" * 80)
    print()

    mode = input("Run in (d)ry-run or (b)ackfill mode? [d/b]: ").strip().lower()
    dry_run = mode != 'b'

    if not dry_run:
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm != 'YES':
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = vault_path.parent / f"backup_area_backfill_{timestamp}"
        shutil.copytree(vault_path, backup_path, dirs_exist_ok=True)
        print(f"✓ Backup at: {backup_path}\n")

    # Build data
    print("Building known area names...")
    known_areas = get_known_area_names(vault_path)
    print(f"Found {len(known_areas)} known areas\n")

    npcs_by_location = get_npcs_by_location(vault_path)
    areas_by_arc = get_areas_by_arc(vault_path, known_areas)

    # Invert arc mapping: area -> arcs
    area_to_arcs = defaultdict(set)
    for arc, areas in areas_by_arc.items():
        for area in areas:
            area_to_arcs[area].add(arc)

    print(f"\nData collected:")
    print(f"  - {len(npcs_by_location)} areas have NPCs")
    print(f"  - {len(area_to_arcs)} areas found in Arcs\n")

    # Process area files
    area_files = list(vault_path.glob("DM Wiki/Entities/Areas/**/*.md"))
    print(f"Processing {len(area_files)} area files...\n")

    modified = 0
    changes = 0

    for area_file in area_files:
        try:
            with open(area_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm_text, body, delim = extract_frontmatter(content)
            if not fm_text:
                continue

            fm = parse_frontmatter(fm_text)
            if fm.get('type') != 'Area':
                continue

            area_name = fm.get('name') or area_file.stem
            file_changes = []

            # Backfill notable_npcs
            if area_name in npcs_by_location:
                existing = fm.get('notable_npcs', []) or []
                if isinstance(existing, str):
                    existing = [existing]
                existing = [n for n in existing if n]

                new_npcs = [f"[[{n}]]" if not n.startswith('[[') else n for n in npcs_by_location[area_name]]
                all_npcs = list(set(existing + new_npcs))

                if all_npcs != existing:
                    fm['notable_npcs'] = all_npcs
                    file_changes.append(f"Added {len(new_npcs)} NPCs")

            # Backfill arcs
            if area_name in area_to_arcs:
                existing = fm.get('arcs', []) or []
                if isinstance(existing, str):
                    existing = [existing]
                existing = [a for a in existing if a]

                new_arcs = [f"[[{a}]]" if not a.startswith('[[') else a for a in area_to_arcs[area_name]]
                all_arcs = list(set(existing + new_arcs))

                if all_arcs != existing:
                    fm['arcs'] = all_arcs
                    file_changes.append(f"Added {len(new_arcs)} arcs")

            if file_changes:
                modified += 1
                changes += len(file_changes)

                if not dry_run:
                    new_content = f"{delim}\n{serialize_frontmatter(fm)}{delim}\n{body}"
                    with open(area_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                rel = area_file.relative_to(vault_path)
                print(f"{'[DRY RUN] ' if dry_run else ''}✏️  {rel}")
                for change in file_changes:
                    print(f"    - {change}")

        except Exception as e:
            continue

    print("\n" + "=" * 80)
    print(f"Files processed: {len(area_files)}")
    print(f"Files modified: {modified}")
    print(f"Total changes: {changes}")
    if dry_run:
        print("\n✓ Dry run complete. Run with 'b' to apply.")
    else:
        print("\n✓ Backfill complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
