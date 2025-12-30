#!/usr/bin/env python3
"""
Convert 5etools JSON files to Obsidian-compatible markdown with YAML frontmatter.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Base paths
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "data"
OUTPUT_DIR = SCRIPT_DIR / "obsidian_output"

# Lookup tables
SCHOOL_ABBREV = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "V": "Evocation",
    "I": "Illusion",
    "N": "Necromancy",
    "T": "Transmutation",
    "P": "Psionic",
}

SIZE_ABBREV = {
    "T": "Tiny",
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "H": "Huge",
    "G": "Gargantuan",
}

ALIGNMENT_ABBREV = {
    "L": "Lawful",
    "N": "Neutral",
    "C": "Chaotic",
    "G": "Good",
    "E": "Evil",
    "U": "Unaligned",
    "A": "Any",
}

SOURCE_NAMES = {
    "PHB": "Player's Handbook",
    "XPHB": "2024 Player's Handbook",
    "DMG": "Dungeon Master's Guide",
    "XDMG": "2024 Dungeon Master's Guide",
    "MM": "Monster Manual",
    "XMM": "2024 Monster Manual",
    "TCE": "Tasha's Cauldron of Everything",
    "XGE": "Xanathar's Guide to Everything",
    "VGM": "Volo's Guide to Monsters",
    "MTF": "Mordenkainen's Tome of Foes",
    "MPMM": "Mordenkainen Presents: Monsters of the Multiverse",
    "FTD": "Fizban's Treasury of Dragons",
    "SCAG": "Sword Coast Adventurer's Guide",
    "EGW": "Explorer's Guide to Wildemount",
    "ERLW": "Eberron: Rising from the Last War",
    "GGR": "Guildmasters' Guide to Ravnica",
    "MOT": "Mythic Odysseys of Theros",
    "VRGR": "Van Richten's Guide to Ravenloft",
    "SCC": "Strixhaven: A Curriculum of Chaos",
    "AAG": "Astral Adventurer's Guide",
    "BAM": "Boo's Astral Menagerie",
    "BGG": "Bigby Presents: Glory of the Giants",
    "BMT": "The Book of Many Things",
    "CoS": "Curse of Strahd",
    "SKT": "Storm King's Thunder",
    "ToA": "Tomb of Annihilation",
    "WDH": "Waterdeep: Dragon Heist",
    "WDMM": "Waterdeep: Dungeon of the Mad Mage",
    "BGDiA": "Baldur's Gate: Descent into Avernus",
    "IDRotF": "Icewind Dale: Rime of the Frostmaiden",
    "WBtW": "The Wild Beyond the Witchlight",
    "CRCotN": "Critical Role: Call of the Netherdeep",
    "DoD": "Domains of Dread",
    "DSotDQ": "Dragonlance: Shadow of the Dragon Queen",
    "KftGV": "Keys from the Golden Vault",
    "PaBTSO": "Phandelver and Below: The Shattered Obelisk",
}


def sanitize_filename(name: str) -> str:
    """Convert a name to a valid filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def format_yaml_value(value: Any, indent: int = 0) -> str:
    """Format a value for YAML frontmatter."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if any(c in value for c in [':', '#', '[', ']', '{', '}', '&', '*', '!', '|', '>', "'", '"', '%', '@', '`', '\n']):
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        if value == "" or value.strip() != value:
            return f'"{value}"'
        return value
    if isinstance(value, list):
        if not value:
            return "[]"
        if all(isinstance(item, str) and len(item) < 50 and '\n' not in item for item in value):
            formatted_items = [format_yaml_value(item) for item in value]
            return f"[{', '.join(formatted_items)}]"
        lines = []
        for item in value:
            if isinstance(item, dict):
                dict_str = format_yaml_value(item, indent + 2)
                lines.append(f"\n{'  ' * indent}  - {dict_str.lstrip()}")
            else:
                lines.append(f"\n{'  ' * indent}  - {format_yaml_value(item)}")
        return "".join(lines)
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = []
        for k, v in value.items():
            formatted_v = format_yaml_value(v, indent + 1)
            lines.append(f"{'  ' * (indent + 1)}{k}: {formatted_v}")
        return "\n" + "\n".join(lines)
    return str(value)


def create_frontmatter(fields: Dict[str, Any]) -> str:
    """Create YAML frontmatter from data dict."""
    if 'tags' not in fields:
        fields['tags'] = ['ai_generated', '5etools']
    elif 'ai_generated' not in fields['tags']:
        fields['tags'].insert(0, 'ai_generated')
    if '5etools' not in fields['tags']:
        fields['tags'].append('5etools')
    
    lines = ["---"]
    for key, value in fields.items():
        if value is not None:
            formatted = format_yaml_value(value)
            lines.append(f"{key}: {formatted}")
    lines.append("---")
    
    return "\n".join(lines)


def parse_5etools_tag(tag_content: str) -> str:
    """Parse 5etools-style tags like {@spell fireball} into markdown."""
    if not tag_content:
        return ""
    
    # Pattern: @type content|additional
    match = re.match(r'@(\w+)\s+(.+)', tag_content)
    if not match:
        return tag_content
    
    tag_type = match.group(1).lower()
    content = match.group(2)
    
    # Handle pipe-separated content (display text)
    parts = content.split('|')
    name = parts[0]
    display = parts[1] if len(parts) > 1 else name
    
    # Convert based on tag type
    link_types = ['spell', 'item', 'creature', 'condition', 'disease', 'action', 
                  'background', 'race', 'class', 'subclass', 'feat', 'skill', 
                  'sense', 'optfeature', 'variantrule', 'reward', 'vehicle',
                  'object', 'trap', 'hazard', 'deity', 'language', 'classfeature',
                  'subclassfeature', 'table', 'book', 'adventure']
    
    if tag_type in link_types:
        # Create an Obsidian wikilink
        if display != name:
            return f"[[{name}|{display}]]"
        return f"[[{name}]]"
    
    if tag_type == 'damage':
        return f"**{name}**"
    if tag_type == 'dice':
        return f"`{name}`"
    if tag_type == 'dc':
        return f"DC {name}"
    if tag_type == 'hit':
        return f"+{name}"
    if tag_type == 'atk':
        atk_types = {
            'mw': 'Melee Weapon Attack',
            'rw': 'Ranged Weapon Attack',
            'ms': 'Melee Spell Attack',
            'rs': 'Ranged Spell Attack',
            'mw,rw': 'Melee or Ranged Weapon Attack',
        }
        return atk_types.get(name.lower(), f"Attack ({name})")
    if tag_type == 'h':
        return "**Hit:**"
    if tag_type == 'recharge':
        if name == "":
            return "(Recharge 6)"
        return f"(Recharge {name}-6)"
    if tag_type == 'status':
        return f"[[{name}]]"
    if tag_type == 'note':
        return f"*{name}*"
    if tag_type == 'b':
        return f"**{name}**"
    if tag_type == 'i':
        return f"*{name}*"
    if tag_type == 'filter':
        # Filter links - just use the display name
        return display.split('|')[0] if '|' in display else name
    if tag_type == 'quickref':
        return name
    if tag_type == 'chance':
        return f"{name}%"
    if tag_type == 'scaledice':
        # Scaled dice notation
        parts = name.split('|')
        return f"`{parts[-1]}`" if parts else name
    if tag_type == 'scaledamage':
        parts = name.split('|')
        return f"`{parts[-1]}`" if parts else name
    
    # Default: just return the content
    return name


def convert_5etools_text(text: str) -> str:
    """Convert 5etools tagged text to markdown."""
    if not isinstance(text, str):
        return str(text) if text else ""
    
    # Replace all {@...} tags
    result = text
    pattern = r'\{(@[^}]+)\}'
    
    def replace_tag(match):
        return parse_5etools_tag(match.group(1))
    
    result = re.sub(pattern, replace_tag, result)
    return result


def convert_entries(entries: Any, depth: int = 0) -> str:
    """Recursively convert 5etools entry structures to markdown."""
    if entries is None:
        return ""
    
    if isinstance(entries, str):
        return convert_5etools_text(entries)
    
    if isinstance(entries, list):
        parts = []
        for entry in entries:
            converted = convert_entries(entry, depth)
            if converted:
                parts.append(converted)
        return "\n\n".join(parts)
    
    if isinstance(entries, dict):
        entry_type = entries.get('type', 'entries')
        
        if entry_type == 'entries':
            name = entries.get('name', '')
            sub_entries = entries.get('entries', [])
            
            header_level = min(depth + 2, 6)
            header = f"{'#' * header_level} {name}\n\n" if name else ""
            content = convert_entries(sub_entries, depth + 1)
            return header + content
        
        elif entry_type == 'list':
            items = entries.get('items', [])
            lines = []
            for item in items:
                if isinstance(item, dict) and item.get('type') == 'item':
                    name = item.get('name', '')
                    entry = convert_entries(item.get('entry', item.get('entries', '')), depth)
                    lines.append(f"- **{name}:** {entry}")
                else:
                    lines.append(f"- {convert_entries(item, depth)}")
            return "\n".join(lines)
        
        elif entry_type == 'table':
            caption = entries.get('caption', '')
            col_labels = entries.get('colLabels', [])
            rows = entries.get('rows', [])
            
            lines = []
            if caption:
                lines.append(f"**{caption}**\n")
            
            if col_labels:
                header = "| " + " | ".join(convert_5etools_text(str(c)) for c in col_labels) + " |"
                separator = "|" + "|".join("---" for _ in col_labels) + "|"
                lines.append(header)
                lines.append(separator)
            
            for row in rows:
                if isinstance(row, list):
                    cells = [convert_5etools_text(str(c)) if c else "" for c in row]
                    lines.append("| " + " | ".join(cells) + " |")
            
            return "\n".join(lines)
        
        elif entry_type == 'item':
            name = entries.get('name', '')
            entry = convert_entries(entries.get('entry', entries.get('entries', '')), depth)
            return f"**{name}:** {entry}"
        
        elif entry_type == 'inline':
            return convert_entries(entries.get('entries', []), depth)
        
        elif entry_type == 'inlineBlock':
            return convert_entries(entries.get('entries', []), depth)
        
        elif entry_type == 'options':
            return convert_entries(entries.get('entries', []), depth)
        
        elif entry_type == 'inset':
            name = entries.get('name', '')
            sub_entries = entries.get('entries', [])
            content = convert_entries(sub_entries, depth + 1)
            if name:
                return f"> **{name}**\n> \n> {content.replace(chr(10), chr(10) + '> ')}"
            return f"> {content.replace(chr(10), chr(10) + '> ')}"
        
        elif entry_type == 'quote':
            sub_entries = entries.get('entries', [])
            by = entries.get('by', '')
            content = convert_entries(sub_entries, depth)
            quote = f"> {content.replace(chr(10), chr(10) + '> ')}"
            if by:
                quote += f"\n> \n> — *{by}*"
            return quote
        
        elif entry_type == 'abilityDc':
            name = entries.get('name', 'Ability')
            attrs = entries.get('attributes', [])
            return f"**{name} save DC** = 8 + proficiency bonus + {' or '.join(a.upper() for a in attrs)} modifier"
        
        elif entry_type == 'abilityAttackMod':
            name = entries.get('name', 'Spell')
            attrs = entries.get('attributes', [])
            return f"**{name} attack modifier** = proficiency bonus + {' or '.join(a.upper() for a in attrs)} modifier"
        
        elif entry_type == 'cell':
            return convert_entries(entries.get('entry', ''), depth)
        
        else:
            # Unknown type, try to extract entries
            sub_entries = entries.get('entries', entries.get('entry', ''))
            if sub_entries:
                return convert_entries(sub_entries, depth)
            return ""
    
    return str(entries)


def get_source_name(abbrev: str) -> str:
    """Get full source name from abbreviation."""
    return SOURCE_NAMES.get(abbrev, abbrev)


def format_range(range_data: Any) -> str:
    """Format spell/ability range."""
    if isinstance(range_data, str):
        return range_data
    if isinstance(range_data, dict):
        range_type = range_data.get('type', '')
        distance = range_data.get('distance', {})
        
        if range_type == 'point':
            dist_type = distance.get('type', '')
            amount = distance.get('amount', '')
            if dist_type == 'self':
                return 'Self'
            if dist_type == 'touch':
                return 'Touch'
            if dist_type == 'sight':
                return 'Sight'
            if dist_type == 'unlimited':
                return 'Unlimited'
            if amount:
                return f"{amount} {dist_type}"
            return dist_type
        
        elif range_type in ['radius', 'sphere', 'cone', 'line', 'cube', 'hemisphere']:
            dist_type = distance.get('type', 'feet')
            amount = distance.get('amount', '')
            return f"Self ({amount}-{dist_type} {range_type})"
        
        elif range_type == 'special':
            return 'Special'
    
    return str(range_data)


def format_duration(duration_data: Any) -> str:
    """Format spell duration."""
    if isinstance(duration_data, str):
        return duration_data
    if isinstance(duration_data, list):
        return ", ".join(format_duration(d) for d in duration_data)
    if isinstance(duration_data, dict):
        d_type = duration_data.get('type', '')
        
        if d_type == 'instant':
            return 'Instantaneous'
        elif d_type == 'permanent':
            ends = duration_data.get('ends', [])
            if ends:
                return f"Until {', '.join(ends)}"
            return 'Permanent'
        elif d_type == 'special':
            return 'Special'
        elif d_type == 'timed':
            dur = duration_data.get('duration', {})
            amount = dur.get('amount', '')
            d_unit = dur.get('type', '')
            concentration = duration_data.get('concentration', False)
            prefix = "Concentration, up to " if concentration else ""
            if amount == 1:
                return f"{prefix}{amount} {d_unit}"
            return f"{prefix}{amount} {d_unit}s"
    
    return str(duration_data)


def format_time(time_data: Any) -> str:
    """Format casting time."""
    if isinstance(time_data, str):
        return time_data
    if isinstance(time_data, list):
        return ", ".join(format_time(t) for t in time_data)
    if isinstance(time_data, dict):
        number = time_data.get('number', 1)
        unit = time_data.get('unit', 'action')
        condition = time_data.get('condition', '')
        
        base = f"{number} {unit}" if number > 1 else f"1 {unit}"
        if condition:
            base += f" ({condition})"
        return base
    
    return str(time_data)


def format_components(comp_data: Any) -> str:
    """Format spell components."""
    if isinstance(comp_data, dict):
        parts = []
        if comp_data.get('v'):
            parts.append('V')
        if comp_data.get('s'):
            parts.append('S')
        if comp_data.get('m'):
            m = comp_data['m']
            if isinstance(m, dict):
                m_text = m.get('text', '')
            else:
                m_text = str(m)
            parts.append(f'M ({m_text})')
        return ', '.join(parts)
    return str(comp_data)


def format_alignment(align_data: Any) -> str:
    """Format alignment."""
    if isinstance(align_data, str):
        return align_data
    if isinstance(align_data, list):
        parts = []
        for a in align_data:
            if isinstance(a, str):
                parts.append(ALIGNMENT_ABBREV.get(a, a))
            elif isinstance(a, dict):
                # Special alignment rules
                if 'special' in a:
                    return a['special']
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2:
            return f"{parts[0]} {parts[1]}"
        return " ".join(parts)
    return str(align_data)


def format_ac(ac_data: Any) -> str:
    """Format armor class."""
    if isinstance(ac_data, (int, float)):
        return str(int(ac_data))
    if isinstance(ac_data, list):
        parts = []
        for ac in ac_data:
            if isinstance(ac, (int, float)):
                parts.append(str(int(ac)))
            elif isinstance(ac, dict):
                val = ac.get('ac', 10)
                source = ac.get('from', [])
                condition = ac.get('condition', '')
                
                ac_str = str(val)
                if source:
                    ac_str += f" ({', '.join(convert_5etools_text(s) for s in source)})"
                if condition:
                    ac_str += f" {condition}"
                parts.append(ac_str)
        return ", ".join(parts)
    return str(ac_data)


def format_hp(hp_data: Any) -> str:
    """Format hit points."""
    if isinstance(hp_data, dict):
        avg = hp_data.get('average', 0)
        formula = hp_data.get('formula', '')
        if formula:
            return f"{avg} ({formula})"
        return str(avg)
    return str(hp_data)


def format_speed(speed_data: Any) -> str:
    """Format speed."""
    if isinstance(speed_data, dict):
        parts = []
        for move_type, value in speed_data.items():
            if value is True:
                parts.append(f"{move_type} (equal to walking)")
            elif isinstance(value, dict):
                num = value.get('number', 0)
                cond = value.get('condition', '')
                parts.append(f"{move_type} {num} ft.{' ' + cond if cond else ''}")
            elif value:
                parts.append(f"{move_type} {value} ft.")
        return ", ".join(parts)
    return str(speed_data)


def format_cr(cr_data: Any) -> str:
    """Format challenge rating."""
    if isinstance(cr_data, dict):
        return cr_data.get('cr', str(cr_data))
    return str(cr_data)


def get_xp_for_cr(cr: str) -> int:
    """Get XP value for a challenge rating."""
    xp_table = {
        "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
        "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800,
        "6": 2300, "7": 2900, "8": 3900, "9": 5000, "10": 5900,
        "11": 7200, "12": 8400, "13": 10000, "14": 11500, "15": 13000,
        "16": 15000, "17": 18000, "18": 20000, "19": 22000, "20": 25000,
        "21": 33000, "22": 41000, "23": 50000, "24": 62000, "25": 75000,
        "26": 90000, "27": 105000, "28": 120000, "29": 135000, "30": 155000
    }
    return xp_table.get(cr, 0)


# =============================================================================
# Converters for each data type
# =============================================================================

def convert_spells(data: Dict) -> Dict[str, str]:
    """Convert spells to markdown."""
    files = {}
    spells = data.get('spell', [])
    
    for spell in spells:
        name = spell.get('name', 'Unknown')
        source = spell.get('source', 'Unknown')
        level = spell.get('level', 0)
        school = SCHOOL_ABBREV.get(spell.get('school', 'U'), 'Unknown')
        
        level_str = "Cantrip" if level == 0 else f"{level}{'st' if level == 1 else 'nd' if level == 2 else 'rd' if level == 3 else 'th'}-level"
        
        # Components
        components = spell.get('components', {})
        comp_str = format_components(components)
        
        # Get class lists
        classes = []
        if 'classes' in spell:
            class_data = spell['classes']
            if 'fromClassList' in class_data:
                classes.extend(c.get('name', '') for c in class_data['fromClassList'])
        
        ritual = spell.get('meta', {}).get('ritual', False)
        concentration = False
        duration = spell.get('duration', [])
        if isinstance(duration, list):
            for d in duration:
                if isinstance(d, dict) and d.get('concentration'):
                    concentration = True
                    break
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'spell', school.lower(), f"level-{level}"],
            'type': 'spell',
            'level': level,
            'school': school,
            'casting_time': format_time(spell.get('time', '1 action')),
            'range': format_range(spell.get('range', 'Self')),
            'duration': format_duration(duration),
            'concentration': concentration,
            'ritual': ritual,
            'classes': classes if classes else None,
        })
        
        # Build spell content
        entries = convert_entries(spell.get('entries', []))
        higher_level = spell.get('entriesHigherLevel', [])
        higher_level_text = convert_entries(higher_level) if higher_level else ""
        
        ritual_tag = " (ritual)" if ritual else ""
        
        content = f"""{frontmatter}

# {name}

*{level_str} {school.lower()}{ritual_tag}*

---

**Casting Time:** {format_time(spell.get('time', '1 action'))}  
**Range:** {format_range(spell.get('range', 'Self'))}  
**Components:** {comp_str}  
**Duration:** {format_duration(duration)}

---

{entries}

{higher_level_text}

---

**Source:** {get_source_name(source)}, p. {spell.get('page', '?')}
"""
        level_folder = "Cantrips" if level == 0 else f"Level {level}"
        files[f"Spells/{level_folder}/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_monsters(data: Dict) -> Dict[str, str]:
    """Convert monsters to markdown."""
    files = {}
    monsters = data.get('monster', [])
    
    for mon in monsters:
        name = mon.get('name', 'Unknown')
        source = mon.get('source', 'Unknown')
        
        # Skip copy references
        if '_copy' in mon:
            continue
        
        size = ", ".join(SIZE_ABBREV.get(s, s) for s in mon.get('size', ['M']))
        
        # Type handling
        mon_type = mon.get('type', 'unknown')
        if isinstance(mon_type, dict):
            type_name = mon_type.get('type', 'unknown')
            type_tags = mon_type.get('tags', [])
            if type_tags:
                type_str = f"{type_name} ({', '.join(str(t) for t in type_tags if isinstance(t, str))})"
            else:
                type_str = type_name
        else:
            type_str = str(mon_type)
        
        alignment = format_alignment(mon.get('alignment', ['U']))
        ac = format_ac(mon.get('ac', 10))
        hp = format_hp(mon.get('hp', {'average': 1}))
        speed = format_speed(mon.get('speed', {'walk': 30}))
        cr = format_cr(mon.get('cr', '0'))
        xp = get_xp_for_cr(cr)
        
        # Ability scores
        abilities = {
            'STR': mon.get('str', 10),
            'DEX': mon.get('dex', 10),
            'CON': mon.get('con', 10),
            'INT': mon.get('int', 10),
            'WIS': mon.get('wis', 10),
            'CHA': mon.get('cha', 10),
        }
        
        # Extract numeric AC and HP for frontmatter
        ac_num = ac.split()[0] if isinstance(ac, str) and ac else "10"
        hp_num = hp.split()[0] if isinstance(hp, str) and hp else "1"
        type_tag = type_str.split()[0].lower() if isinstance(type_str, str) else "unknown"
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'monster', type_tag, f"cr-{cr}"],
            'type': 'monster',
            'size': size,
            'monster_type': type_str,
            'alignment': alignment,
            'armor_class': ac_num,
            'hit_points': hp_num,
            'challenge_rating': cr,
            'xp': xp,
        })
        
        # Stats
        stat_row = " | ".join(f"**{k}** {v} ({(v-10)//2:+d})" for k, v in abilities.items())
        
        # Saves
        saves = mon.get('save', {})
        saves_str = ", ".join(f"{k.upper()} {v}" for k, v in saves.items()) if saves else "—"
        
        # Skills
        skills = mon.get('skill', {})
        skills_str = ", ".join(f"{k.title()} {v}" for k, v in skills.items()) if skills else "—"
        
        # Senses
        senses = mon.get('senses', [])
        passive = mon.get('passive', 10)
        senses_parts = senses if isinstance(senses, list) else [senses]
        senses_parts.append(f"passive Perception {passive}")
        senses_str = ", ".join(senses_parts)
        
        # Languages
        languages = mon.get('languages', [])
        lang_str = ", ".join(languages) if languages else "—"
        
        # Traits
        traits = mon.get('trait', [])
        traits_section = ""
        if traits:
            traits_section = "## Traits\n\n"
            for trait in traits:
                trait_name = trait.get('name', 'Unknown')
                trait_entries = convert_entries(trait.get('entries', []))
                traits_section += f"**{trait_name}.** {trait_entries}\n\n"
        
        # Actions
        actions = mon.get('action', [])
        actions_section = ""
        if actions:
            actions_section = "## Actions\n\n"
            for action in actions:
                action_name = action.get('name', 'Unknown')
                action_entries = convert_entries(action.get('entries', []))
                actions_section += f"**{action_name}.** {action_entries}\n\n"
        
        # Bonus Actions
        bonus_actions = mon.get('bonus', [])
        bonus_section = ""
        if bonus_actions:
            bonus_section = "## Bonus Actions\n\n"
            for action in bonus_actions:
                action_name = action.get('name', 'Unknown')
                action_entries = convert_entries(action.get('entries', []))
                bonus_section += f"**{action_name}.** {action_entries}\n\n"
        
        # Reactions
        reactions = mon.get('reaction', [])
        reaction_section = ""
        if reactions:
            reaction_section = "## Reactions\n\n"
            for reaction in reactions:
                reaction_name = reaction.get('name', 'Unknown')
                reaction_entries = convert_entries(reaction.get('entries', []))
                reaction_section += f"**{reaction_name}.** {reaction_entries}\n\n"
        
        # Legendary Actions
        legendary = mon.get('legendary', [])
        legendary_section = ""
        if legendary:
            legendary_section = "## Legendary Actions\n\n"
            legendary_desc = mon.get('legendaryHeader', ['The creature can take 3 legendary actions.'])
            legendary_section += convert_entries(legendary_desc) + "\n\n"
            for action in legendary:
                action_name = action.get('name', 'Unknown')
                action_entries = convert_entries(action.get('entries', []))
                legendary_section += f"**{action_name}.** {action_entries}\n\n"
        
        # Damage immunities, resistances, vulnerabilities
        dmg_immune = mon.get('immune', [])
        dmg_resist = mon.get('resist', [])
        dmg_vuln = mon.get('vulnerable', [])
        cond_immune = mon.get('conditionImmune', [])
        
        def format_damage_list(lst):
            parts = []
            for item in lst:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    types = item.get('damage', item.get('immune', []))
                    if isinstance(types, list):
                        parts.extend(types)
            return ", ".join(parts) if parts else "—"
        
        content = f"""{frontmatter}

# {name}

*{size} {type_str}, {alignment}*

---

**Armor Class** {ac}  
**Hit Points** {hp}  
**Speed** {speed}

---

| {stat_row} |

---

**Saving Throws** {saves_str}  
**Skills** {skills_str}  
**Damage Resistances** {format_damage_list(dmg_resist)}  
**Damage Immunities** {format_damage_list(dmg_immune)}  
**Condition Immunities** {', '.join(str(c) for c in cond_immune) if cond_immune else '—'}  
**Senses** {senses_str}  
**Languages** {lang_str}  
**Challenge** {cr} ({xp:,} XP)

---

{traits_section}
{actions_section}
{bonus_section}
{reaction_section}
{legendary_section}

---

**Source:** {get_source_name(source)}, p. {mon.get('page', '?')}
"""
        files[f"Monsters/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_items(data: Dict) -> Dict[str, str]:
    """Convert items to markdown."""
    files = {}
    items = data.get('item', [])
    
    for item in items:
        name = item.get('name', 'Unknown')
        source = item.get('source', 'Unknown')
        
        # Skip copy references
        if '_copy' in item:
            continue
        
        rarity = item.get('rarity', 'common')
        if isinstance(rarity, dict):
            rarity = rarity.get('name', 'common')
        
        item_type = item.get('type', 'G')
        wondrous = item.get('wondrous', False)
        attunement = item.get('reqAttune', False)
        
        # Weight and value
        weight = item.get('weight', 0)
        value = item.get('value', 0)
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'item', rarity.lower().replace(' ', '-')],
            'type': 'item',
            'rarity': rarity.title() if rarity else 'Common',
            'requires_attunement': bool(attunement),
            'wondrous': wondrous,
            'weight': weight if weight else None,
        })
        
        attunement_str = ""
        if attunement:
            if isinstance(attunement, str):
                attunement_str = f" *(requires attunement {attunement})*"
            else:
                attunement_str = " *(requires attunement)*"
        
        category = "Wondrous Item" if wondrous else "Item"
        entries = convert_entries(item.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

*{category}, {rarity.title() if rarity else 'Common'}*{attunement_str}

{entries}

---

**Source:** {get_source_name(source)}, p. {item.get('page', '?')}
"""
        files[f"Items/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_feats(data: Dict) -> Dict[str, str]:
    """Convert feats to markdown."""
    files = {}
    feats = data.get('feat', [])
    
    for feat in feats:
        name = feat.get('name', 'Unknown')
        source = feat.get('source', 'Unknown')
        
        # Prerequisites
        prereqs = feat.get('prerequisite', [])
        prereq_strs = []
        for prereq in prereqs:
            if isinstance(prereq, dict):
                for key, value in prereq.items():
                    if key == 'ability':
                        for ab in value:
                            for stat, min_val in ab.items():
                                prereq_strs.append(f"{stat.upper()} {min_val}+")
                    elif key == 'race':
                        prereq_strs.extend(r.get('name', str(r)) for r in value)
                    elif key == 'level':
                        prereq_strs.append(f"Level {value}")
                    elif key == 'spellcasting':
                        prereq_strs.append("Spellcasting ability")
                    elif key == 'other':
                        prereq_strs.append(str(value))
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'feat'],
            'type': 'feat',
            'prerequisites': prereq_strs if prereq_strs else None,
        })
        
        entries = convert_entries(feat.get('entries', []))
        prereq_line = f"\n**Prerequisites:** {', '.join(prereq_strs)}\n" if prereq_strs else ""
        
        content = f"""{frontmatter}

# {name}
{prereq_line}
{entries}

---

**Source:** {get_source_name(source)}, p. {feat.get('page', '?')}
"""
        files[f"Feats/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_backgrounds(data: Dict) -> Dict[str, str]:
    """Convert backgrounds to markdown."""
    files = {}
    backgrounds = data.get('background', [])
    
    for bg in backgrounds:
        name = bg.get('name', 'Unknown')
        source = bg.get('source', 'Unknown')
        
        # Skip copy references
        if '_copy' in bg:
            continue
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'background'],
            'type': 'background',
        })
        
        entries = convert_entries(bg.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

{entries}

---

**Source:** {get_source_name(source)}, p. {bg.get('page', '?')}
"""
        files[f"Backgrounds/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_races(data: Dict) -> Dict[str, str]:
    """Convert races to markdown."""
    files = {}
    races = data.get('race', [])
    
    for race in races:
        name = race.get('name', 'Unknown')
        source = race.get('source', 'Unknown')
        
        # Skip copy references
        if '_copy' in race:
            continue
        
        size = ", ".join(SIZE_ABBREV.get(s, s) for s in race.get('size', ['M']))
        speed = format_speed(race.get('speed', {'walk': 30}))
        
        # Ability bonuses
        ability = race.get('ability', [])
        ability_strs = []
        for ab in ability:
            if isinstance(ab, dict):
                for stat, bonus in ab.items():
                    if stat == 'choose':
                        continue
                    ability_strs.append(f"{stat.upper()} +{bonus}")
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'race'],
            'type': 'race',
            'size': size,
            'speed': speed,
            'ability_bonuses': ability_strs if ability_strs else None,
        })
        
        entries = convert_entries(race.get('entries', []))
        ability_line = f"**Ability Score Increase:** {', '.join(ability_strs)}\n" if ability_strs else ""
        
        content = f"""{frontmatter}

# {name}

**Size:** {size}  
**Speed:** {speed}  
{ability_line}
{entries}

---

**Source:** {get_source_name(source)}, p. {race.get('page', '?')}
"""
        files[f"Races/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_conditions(data: Dict) -> Dict[str, str]:
    """Convert conditions and diseases to markdown."""
    files = {}
    
    for condition in data.get('condition', []):
        name = condition.get('name', 'Unknown')
        source = condition.get('source', 'Unknown')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'condition'],
            'type': 'condition',
        })
        
        entries = convert_entries(condition.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

{entries}

---

**Source:** {get_source_name(source)}, p. {condition.get('page', '?')}
"""
        files[f"Conditions/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    for disease in data.get('disease', []):
        name = disease.get('name', 'Unknown')
        source = disease.get('source', 'Unknown')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'disease'],
            'type': 'disease',
        })
        
        entries = convert_entries(disease.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

{entries}

---

**Source:** {get_source_name(source)}, p. {disease.get('page', '?')}
"""
        files[f"Diseases/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_actions(data: Dict) -> Dict[str, str]:
    """Convert actions to markdown."""
    files = {}
    actions = data.get('action', [])
    
    for action in actions:
        name = action.get('name', 'Unknown')
        source = action.get('source', 'Unknown')
        
        time_data = action.get('time', [])
        time_str = format_time(time_data) if time_data else "Varies"
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'action'],
            'type': 'action',
            'time': time_str,
        })
        
        entries = convert_entries(action.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

**Time:** {time_str}

{entries}

---

**Source:** {get_source_name(source)}, p. {action.get('page', '?')}
"""
        files[f"Actions/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_classes(data: Dict) -> Dict[str, str]:
    """Convert classes to markdown."""
    files = {}
    
    for cls in data.get('class', []):
        name = cls.get('name', 'Unknown')
        source = cls.get('source', 'Unknown')
        
        # Skip copy references
        if '_copy' in cls:
            continue
        
        hd = cls.get('hd', {})
        hit_die = hd.get('faces', 8) if isinstance(hd, dict) else 8
        
        proficiency = cls.get('proficiency', [])
        prof_strs = [p.upper() for p in proficiency]
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'class'],
            'type': 'class',
            'hit_die': hit_die,
            'saving_throws': prof_strs,
        })
        
        # Starting proficiencies
        starting_profs = cls.get('startingProficiencies', {})
        armor = starting_profs.get('armor', [])
        weapons = starting_profs.get('weapons', [])
        tools = starting_profs.get('tools', [])
        skills = starting_profs.get('skills', [])
        
        armor_str = ", ".join(convert_5etools_text(str(a)) for a in armor) if armor else "None"
        weapons_str = ", ".join(convert_5etools_text(str(w)) for w in weapons) if weapons else "None"
        
        content = f"""{frontmatter}

# {name}

**Hit Die:** d{hit_die}  
**Saving Throws:** {', '.join(prof_strs)}

## Proficiencies

**Armor:** {armor_str}  
**Weapons:** {weapons_str}

---

**Source:** {get_source_name(source)}, p. {cls.get('page', '?')}
"""
        files[f"Classes/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    # Subclasses
    for subcls in data.get('subclass', []):
        name = subcls.get('name', 'Unknown')
        source = subcls.get('source', 'Unknown')
        class_name = subcls.get('className', 'Unknown')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'subclass', class_name.lower()],
            'type': 'subclass',
            'class': class_name,
        })
        
        content = f"""{frontmatter}

# {name}

*Subclass for [[{class_name}]]*

---

**Source:** {get_source_name(source)}, p. {subcls.get('page', '?')}
"""
        files[f"Subclasses/{sanitize_filename(class_name)}/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_optionalfeatures(data: Dict) -> Dict[str, str]:
    """Convert optional features (invocations, infusions, etc.) to markdown."""
    files = {}
    features = data.get('optionalfeature', [])
    
    for feat in features:
        name = feat.get('name', 'Unknown')
        source = feat.get('source', 'Unknown')
        
        feature_type = feat.get('featureType', ['OF'])
        if isinstance(feature_type, list):
            feature_type = feature_type[0] if feature_type else 'OF'
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'optional-feature', feature_type.lower()],
            'type': 'optional-feature',
            'feature_type': feature_type,
        })
        
        entries = convert_entries(feat.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

{entries}

---

**Source:** {get_source_name(source)}, p. {feat.get('page', '?')}
"""
        files[f"Optional Features/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_deities(data: Dict) -> Dict[str, str]:
    """Convert deities to markdown."""
    files = {}
    deities = data.get('deity', [])
    
    for deity in deities:
        name = deity.get('name', 'Unknown')
        source = deity.get('source', 'Unknown')
        
        pantheon = deity.get('pantheon', 'Unknown')
        alignment = format_alignment(deity.get('alignment', []))
        domains = deity.get('domains', [])
        symbol = deity.get('symbol', '')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'deity', pantheon.lower().replace(' ', '-')],
            'type': 'deity',
            'pantheon': pantheon,
            'alignment': alignment,
            'domains': domains,
        })
        
        entries = convert_entries(deity.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

**Pantheon:** {pantheon}  
**Alignment:** {alignment}  
**Domains:** {', '.join(domains) if domains else 'Unknown'}  
**Symbol:** {symbol}

{entries}

---

**Source:** {get_source_name(source)}, p. {deity.get('page', '?')}
"""
        files[f"Deities/{sanitize_filename(pantheon)}/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_vehicles(data: Dict) -> Dict[str, str]:
    """Convert vehicles to markdown."""
    files = {}
    vehicles = data.get('vehicle', [])
    
    for vehicle in vehicles:
        name = vehicle.get('name', 'Unknown')
        source = vehicle.get('source', 'Unknown')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'vehicle'],
            'type': 'vehicle',
        })
        
        entries = convert_entries(vehicle.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

{entries}

---

**Source:** {get_source_name(source)}, p. {vehicle.get('page', '?')}
"""
        files[f"Vehicles/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_rewards(data: Dict) -> Dict[str, str]:
    """Convert rewards (boons, blessings, etc.) to markdown."""
    files = {}
    rewards = data.get('reward', [])
    
    for reward in rewards:
        name = reward.get('name', 'Unknown')
        source = reward.get('source', 'Unknown')
        
        reward_type = reward.get('type', 'reward')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'reward', reward_type.lower()],
            'type': 'reward',
            'reward_type': reward_type,
        })
        
        entries = convert_entries(reward.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

*{reward_type.title()}*

{entries}

---

**Source:** {get_source_name(source)}, p. {reward.get('page', '?')}
"""
        files[f"Rewards/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_traps_hazards(data: Dict) -> Dict[str, str]:
    """Convert traps and hazards to markdown."""
    files = {}
    
    for trap in data.get('trap', []):
        name = trap.get('name', 'Unknown')
        source = trap.get('source', 'Unknown')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'trap'],
            'type': 'trap',
        })
        
        entries = convert_entries(trap.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

{entries}

---

**Source:** {get_source_name(source)}, p. {trap.get('page', '?')}
"""
        files[f"Traps/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    for hazard in data.get('hazard', []):
        name = hazard.get('name', 'Unknown')
        source = hazard.get('source', 'Unknown')
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'hazard'],
            'type': 'hazard',
        })
        
        entries = convert_entries(hazard.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

{entries}

---

**Source:** {get_source_name(source)}, p. {hazard.get('page', '?')}
"""
        files[f"Hazards/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


def convert_languages(data: Dict) -> Dict[str, str]:
    """Convert languages to markdown."""
    files = {}
    languages = data.get('language', [])
    
    for lang in languages:
        name = lang.get('name', 'Unknown')
        source = lang.get('source', 'Unknown')
        
        lang_type = lang.get('type', 'standard')
        script = lang.get('script', '')
        speakers = lang.get('typicalSpeakers', [])
        
        frontmatter = create_frontmatter({
            'name': name,
            'source': source,
            'source_full': get_source_name(source),
            'aliases': [f"{name} ({source})"],
            'tags': ['ai_generated', '5etools', 'language', lang_type.lower()],
            'type': 'language',
            'language_type': lang_type,
            'script': script,
            'typical_speakers': speakers,
        })
        
        entries = convert_entries(lang.get('entries', []))
        
        content = f"""{frontmatter}

# {name}

**Type:** {lang_type.title()}  
**Script:** {script if script else 'None'}  
**Typical Speakers:** {', '.join(speakers) if speakers else 'Unknown'}

{entries}

---

**Source:** {get_source_name(source)}, p. {lang.get('page', '?')}
"""
        files[f"Languages/{sanitize_filename(name)} ({source}).md"] = content.strip() + "\n"
    
    return files


# =============================================================================
# Main conversion logic
# =============================================================================

def load_json_file(filepath: Path) -> Optional[Dict]:
    """Load a JSON file, returning None on error."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  ⚠️  Error loading {filepath}: {e}")
        return None


def process_directory_files(directory: Path, converter_func, data_key: str = None) -> Dict[str, str]:
    """Process all JSON files in a directory."""
    all_files = {}
    
    if not directory.exists():
        return all_files
    
    for filepath in directory.glob("*.json"):
        # Skip fluff, foundry, index, and template files
        if any(skip in filepath.name for skip in ['fluff-', 'foundry', 'index.json', 'template.json', 'sources.json']):
            continue
        
        data = load_json_file(filepath)
        if data:
            files = converter_func(data)
            all_files.update(files)
    
    return all_files


def main():
    """Main conversion function."""
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_files = 0
    
    # Single file conversions
    single_files = {
        'feats.json': convert_feats,
        'backgrounds.json': convert_backgrounds,
        'races.json': convert_races,
        'conditionsdiseases.json': convert_conditions,
        'actions.json': convert_actions,
        'optionalfeatures.json': convert_optionalfeatures,
        'deities.json': convert_deities,
        'vehicles.json': convert_vehicles,
        'rewards.json': convert_rewards,
        'trapshazards.json': convert_traps_hazards,
        'languages.json': convert_languages,
        'items.json': convert_items,
    }
    
    for filename, converter in single_files.items():
        filepath = INPUT_DIR / filename
        if filepath.exists():
            print(f"📄 Processing {filename}...")
            data = load_json_file(filepath)
            if data:
                files = converter(data)
                for fp, content in files.items():
                    output_path = OUTPUT_DIR / fp
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    total_files += 1
                print(f"   ✅ Created {len(files)} files")
    
    # Directory-based conversions
    directory_converters = {
        'spells': convert_spells,
        'bestiary': convert_monsters,
        'class': convert_classes,
    }
    
    for dir_name, converter in directory_converters.items():
        dir_path = INPUT_DIR / dir_name
        if dir_path.exists():
            print(f"📁 Processing {dir_name}/...")
            files = process_directory_files(dir_path, converter)
            for fp, content in files.items():
                output_path = OUTPUT_DIR / fp
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                total_files += 1
            print(f"   ✅ Created {len(files)} files")
    
    print(f"\n🎉 Conversion complete! Total files created: {total_files}")
    print(f"📁 Output location: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

