#!/usr/bin/env python3
"""
Item Property Backfill Script
Backfills:
- type: Item
- arcs: from Arc document mentions
- first_appearance_session: from session recaps
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


def get_known_item_names(vault_path: Path) -> Dict[str, List[str]]:
    """Build a map of item names to their aliases."""
    item_files = list(vault_path.glob("DM Wiki/Entities/Items/*.md"))
    item_names = defaultdict(list)

    for item_file in item_files:
        try:
            with open(item_file, 'r', encoding='utf-8') as f:
                fm_text, _, _ = extract_frontmatter(f.read())

            fm = parse_frontmatter(fm_text)
            # Use filename as the primary name
            item_name = item_file.stem
            item_names[item_name].append(item_name)

            # Add aliases
            aliases = fm.get('aliases', [])
            if isinstance(aliases, str):
                aliases = [aliases]
            for alias in aliases:
                if alias and alias != item_name:
                    item_names[item_name].append(alias)
        except:
            continue

    return item_names


def get_items_by_arc(vault_path: Path, known_items: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Map arc names to items mentioned in them (wikilinked or plain text)."""
    arc_files = list(vault_path.glob("Source/CoS-Reloaded/**/Arc *.md"))

    print(f"Scanning {len(arc_files)} Arc files for {len(known_items)} known items...")
    arc_to_items = defaultdict(set)

    for arc_file in arc_files:
        arc_name = arc_file.stem
        try:
            with open(arc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Search for each known item (by name and aliases)
            for item_name, variants in known_items.items():
                for variant in variants:
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(pattern, content, re.IGNORECASE):
                        arc_to_items[arc_name].add(item_name)
                        break  # Found this item, move to next
        except:
            continue

    return {k: list(v) for k, v in arc_to_items.items()}


def get_items_first_appearance(vault_path: Path, known_items: Dict[str, List[str]]) -> Dict[str, int]:
    """Map item names to their first appearance session number."""
    session_files = list(vault_path.glob("Player Wiki/Session Recaps/*.md"))

    print(f"Scanning {len(session_files)} session recaps for item first appearances...")
    item_first_session = {}

    for session_file in session_files:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                fm_text, body, _ = extract_frontmatter(f.read())

            fm = parse_frontmatter(fm_text)
            session_num = fm.get('session_number')
            if not session_num:
                continue

            # Search for each known item in the session body
            for item_name, variants in known_items.items():
                # Skip if we already found an earlier appearance
                if item_name in item_first_session and item_first_session[item_name] < session_num:
                    continue

                for variant in variants:
                    pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(pattern, body, re.IGNORECASE):
                        if item_name not in item_first_session or session_num < item_first_session[item_name]:
                            item_first_session[item_name] = session_num
                        break
        except:
            continue

    return item_first_session


def main():
    script_dir = Path(__file__).parent
    vault_path = script_dir.parent

    print("=" * 80)
    print("Item Property Backfill Script")
    print("=" * 80)
    print()

    mode = input("Run in (d)ry-run or (b)ackfill mode? [d/b]: ").strip().lower()
    dry_run = mode != 'b'

    if not dry_run:
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm != 'YES':
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = vault_path.parent / f"backup_item_backfill_{timestamp}"
        shutil.copytree(vault_path, backup_path, dirs_exist_ok=True)
        print(f"✓ Backup at: {backup_path}\n")

    # Build data
    print("Building known item names...")
    known_items = get_known_item_names(vault_path)
    print(f"Found {len(known_items)} known items\n")

    items_by_arc = get_items_by_arc(vault_path, known_items)
    item_first_session = get_items_first_appearance(vault_path, known_items)

    # Invert arc mapping: item -> arcs
    item_to_arcs = defaultdict(set)
    for arc, items in items_by_arc.items():
        for item in items:
            item_to_arcs[item].add(arc)

    print(f"\nData collected:")
    print(f"  - {len(item_to_arcs)} items found in Arcs")
    print(f"  - {len(item_first_session)} items found in session recaps\n")

    # Process item files
    item_files = list(vault_path.glob("DM Wiki/Entities/Items/*.md"))
    print(f"Processing {len(item_files)} item files...\n")

    modified = 0
    changes = 0

    for item_file in item_files:
        try:
            with open(item_file, 'r', encoding='utf-8') as f:
                content = f.read()

            fm_text, body, delim = extract_frontmatter(content)
            if not delim:
                continue

            fm = parse_frontmatter(fm_text)
            item_name = item_file.stem
            file_changes = []

            # Add type: Item if missing
            if not fm.get('type'):
                fm['type'] = 'Item'
                file_changes.append("Added type: Item")

            # Backfill arcs
            if item_name in item_to_arcs:
                existing = fm.get('arcs', []) or []
                if isinstance(existing, str):
                    existing = [existing]
                existing = [a for a in existing if a]

                new_arcs = [f"[[{a}]]" if not a.startswith('[[') else a for a in item_to_arcs[item_name]]
                all_arcs = list(set(existing + new_arcs))

                if all_arcs != existing:
                    fm['arcs'] = all_arcs
                    file_changes.append(f"Added {len(new_arcs)} arcs")

            # Backfill first_appearance_session
            if item_name in item_first_session and not fm.get('first_appearance_session'):
                fm['first_appearance_session'] = item_first_session[item_name]
                file_changes.append(f"Added first appearance: Session {item_first_session[item_name]}")

            if file_changes:
                modified += 1
                changes += len(file_changes)

                if not dry_run:
                    new_content = f"{delim}\n{serialize_frontmatter(fm)}{delim}\n{body}"
                    with open(item_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                rel = item_file.relative_to(vault_path)
                print(f"{'[DRY RUN] ' if dry_run else ''}✏️  {rel}")
                for change in file_changes:
                    print(f"    - {change}")

        except Exception as e:
            continue

    print("\n" + "=" * 80)
    print(f"Files processed: {len(item_files)}")
    print(f"Files modified: {modified}")
    print(f"Total changes: {changes}")
    if dry_run:
        print("\n✓ Dry run complete. Run with 'b' to apply.")
    else:
        print("\n✓ Backfill complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
