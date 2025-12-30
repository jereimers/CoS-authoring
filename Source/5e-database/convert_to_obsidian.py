#!/usr/bin/env python3
"""
Convert 5e SRD JSON files to Obsidian-compatible markdown with YAML frontmatter.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Base paths
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "src" / "2014"
OUTPUT_DIR = SCRIPT_DIR / "obsidian_output"


def sanitize_filename(name: str) -> str:
    """Convert a name to a valid filename."""
    # Replace problematic characters
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
        # Escape special characters and wrap in quotes if needed
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
            # Simple list on one line
            formatted_items = [format_yaml_value(item) for item in value]
            return f"[{', '.join(formatted_items)}]"
        # Multi-line list
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


def create_frontmatter(data: Dict[str, Any], extra_fields: Optional[Dict] = None) -> str:
    """Create YAML frontmatter from data dict."""
    fields = extra_fields.copy() if extra_fields else {}
    
    # Add ai_generated tag as required
    if 'tags' not in fields:
        fields['tags'] = ['ai_generated', '5e-srd']
    elif 'ai_generated' not in fields['tags']:
        fields['tags'].insert(0, 'ai_generated')
    
    lines = ["---"]
    for key, value in fields.items():
        formatted = format_yaml_value(value)
        lines.append(f"{key}: {formatted}")
    lines.append("---")
    
    return "\n".join(lines)


def extract_ref_name(ref: Dict) -> str:
    """Extract name from a reference dict."""
    return ref.get('name', ref.get('index', ''))


def extract_ref_names(refs: List[Dict]) -> List[str]:
    """Extract names from a list of reference dicts."""
    return [extract_ref_name(ref) for ref in refs if ref]


def join_descriptions(desc: Any) -> str:
    """Join description array into paragraphs."""
    if isinstance(desc, list):
        return "\n\n".join(desc)
    return str(desc) if desc else ""


# =============================================================================
# Converters for each data type
# =============================================================================

def convert_ability_scores(data: List[Dict]) -> Dict[str, str]:
    """Convert ability scores to markdown."""
    files = {}
    for item in data:
        name = item['full_name']
        abbr = item['name']
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'abbreviation': abbr,
            'aliases': [abbr, item['index']],
            'tags': ['ai_generated', '5e-srd', 'ability-score'],
            'type': 'ability-score',
        })
        
        skills = extract_ref_names(item.get('skills', []))
        skills_section = f"## Related Skills\n\n" + ", ".join(f"[[{s}]]" for s in skills) if skills else ""
        
        content = f"""{frontmatter}

# {name} ({abbr})

{join_descriptions(item.get('desc', []))}

{skills_section}
"""
        files[f"Ability Scores/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_alignments(data: List[Dict]) -> Dict[str, str]:
    """Convert alignments to markdown."""
    files = {}
    for item in data:
        name = item['name']
        abbr = item.get('abbreviation', '')
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'abbreviation': abbr,
            'aliases': [abbr, item['index']],
            'tags': ['ai_generated', '5e-srd', 'alignment'],
            'type': 'alignment',
        })
        
        content = f"""{frontmatter}

# {name}

{item.get('desc', '')}
"""
        files[f"Alignments/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_backgrounds(data: List[Dict]) -> Dict[str, str]:
    """Convert backgrounds to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        # Extract starting proficiencies and equipment
        proficiencies = extract_ref_names(item.get('starting_proficiencies', []))
        equipment = []
        for eq in item.get('starting_equipment', []):
            eq_item = eq.get('equipment', {})
            qty = eq.get('quantity', 1)
            eq_name = eq_item.get('name', '')
            if qty > 1:
                equipment.append(f"{qty}x {eq_name}")
            else:
                equipment.append(eq_name)
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'background'],
            'type': 'background',
            'starting_proficiencies': proficiencies,
            'starting_equipment': equipment,
        })
        
        # Build feature section
        feature = item.get('feature', {})
        feature_section = ""
        if feature:
            feature_section = f"""## Feature: {feature.get('name', 'Unknown')}

{join_descriptions(feature.get('desc', []))}
"""
        
        content = f"""{frontmatter}

# {name}

## Starting Proficiencies

{chr(10).join(f"- [[{p}]]" for p in proficiencies) if proficiencies else "_None_"}

## Starting Equipment

{chr(10).join(f"- {e}" for e in equipment) if equipment else "_None_"}

{feature_section}
"""
        files[f"Backgrounds/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_classes(data: List[Dict]) -> Dict[str, str]:
    """Convert classes to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        proficiencies = extract_ref_names(item.get('proficiencies', []))
        saving_throws = extract_ref_names(item.get('saving_throws', []))
        subclasses = extract_ref_names(item.get('subclasses', []))
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'class'],
            'type': 'class',
            'hit_die': item.get('hit_die'),
            'saving_throws': saving_throws,
            'subclasses': subclasses,
        })
        
        # Proficiency choices
        prof_choices_section = ""
        for choice in item.get('proficiency_choices', []):
            prof_choices_section += f"- {choice.get('desc', '')}\n"
        
        content = f"""{frontmatter}

# {name}

**Hit Die:** d{item.get('hit_die', '?')}

## Saving Throws

{', '.join(f"**{st}**" for st in saving_throws)}

## Proficiencies

{chr(10).join(f"- [[{p}]]" for p in proficiencies)}

## Proficiency Choices

{prof_choices_section if prof_choices_section else "_None_"}

## Subclasses

{chr(10).join(f"- [[{sc}]]" for sc in subclasses) if subclasses else "_None_"}
"""
        files[f"Classes/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_conditions(data: List[Dict]) -> Dict[str, str]:
    """Convert conditions to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'condition'],
            'type': 'condition',
        })
        
        content = f"""{frontmatter}

# {name}

{join_descriptions(item.get('desc', []))}
"""
        files[f"Conditions/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_damage_types(data: List[Dict]) -> Dict[str, str]:
    """Convert damage types to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'damage-type'],
            'type': 'damage-type',
        })
        
        content = f"""{frontmatter}

# {name}

{join_descriptions(item.get('desc', []))}
"""
        files[f"Damage Types/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_equipment(data: List[Dict]) -> Dict[str, str]:
    """Convert equipment to markdown."""
    files = {}
    for item in data:
        name = item['name']
        category = item.get('equipment_category', {}).get('name', 'Miscellaneous')
        
        # Prepare frontmatter fields
        fm_fields = {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'equipment', category.lower().replace(' ', '-')],
            'type': 'equipment',
            'category': category,
        }
        
        # Add cost if present
        cost = item.get('cost', {})
        if cost:
            fm_fields['cost'] = f"{cost.get('quantity', 0)} {cost.get('unit', 'gp')}"
        
        # Add weight if present
        if 'weight' in item:
            fm_fields['weight'] = item['weight']
        
        # Weapon-specific fields
        if 'damage' in item:
            damage = item['damage']
            fm_fields['damage_dice'] = damage.get('damage_dice', '')
            fm_fields['damage_type'] = damage.get('damage_type', {}).get('name', '')
        
        if 'weapon_category' in item:
            fm_fields['weapon_category'] = item['weapon_category']
        if 'weapon_range' in item:
            fm_fields['weapon_range'] = item['weapon_range']
        
        # Armor-specific fields
        if 'armor_category' in item:
            fm_fields['armor_category'] = item['armor_category']
        if 'armor_class' in item:
            ac = item['armor_class']
            fm_fields['armor_class_base'] = ac.get('base', 0)
            if ac.get('dex_bonus'):
                fm_fields['armor_class_dex_bonus'] = True
        
        frontmatter = create_frontmatter(item, fm_fields)
        
        # Build content sections
        sections = []
        
        if cost:
            sections.append(f"**Cost:** {cost.get('quantity', 0)} {cost.get('unit', 'gp')}")
        if 'weight' in item:
            sections.append(f"**Weight:** {item['weight']} lb.")
        
        # Weapon info
        if 'damage' in item:
            damage = item['damage']
            damage_str = f"{damage.get('damage_dice', '')} {damage.get('damage_type', {}).get('name', '')}"
            sections.append(f"**Damage:** {damage_str}")
        
        if 'weapon_range' in item:
            sections.append(f"**Range:** {item['weapon_range']}")
        
        # Range details
        range_info = item.get('range', {})
        if range_info:
            range_str = f"Normal: {range_info.get('normal', '-')} ft."
            if 'long' in range_info:
                range_str += f", Long: {range_info['long']} ft."
            sections.append(f"**Range Details:** {range_str}")
        
        # Properties
        properties = extract_ref_names(item.get('properties', []))
        if properties:
            sections.append(f"**Properties:** {', '.join(properties)}")
        
        # Armor info
        if 'armor_class' in item:
            ac = item['armor_class']
            ac_str = str(ac.get('base', 0))
            if ac.get('dex_bonus'):
                max_bonus = ac.get('max_bonus')
                if max_bonus:
                    ac_str += f" + DEX (max {max_bonus})"
                else:
                    ac_str += " + DEX"
            sections.append(f"**Armor Class:** {ac_str}")
        
        if 'str_minimum' in item:
            sections.append(f"**Strength Required:** {item['str_minimum']}")
        if item.get('stealth_disadvantage'):
            sections.append("**Stealth:** Disadvantage")
        
        # Description
        desc = join_descriptions(item.get('desc', []))
        
        content = f"""{frontmatter}

# {name}

*{category}*

{chr(10).join(sections)}

{desc}
"""
        # Determine subfolder based on category
        subfolder = category.replace(' ', '')
        files[f"Equipment/{subfolder}/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_features(data: List[Dict]) -> Dict[str, str]:
    """Convert features to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        # Get class and level info
        class_info = item.get('class', {})
        class_name = class_info.get('name', '')
        level = item.get('level', 0)
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'feature', f"class-{class_name.lower()}" if class_name else ""],
            'type': 'feature',
            'class': class_name,
            'level': level,
        })
        
        content = f"""{frontmatter}

# {name}

**Class:** [[{class_name}]]  
**Level:** {level}

{join_descriptions(item.get('desc', []))}
"""
        # Organize by class
        subfolder = sanitize_filename(class_name) if class_name else "General"
        files[f"Features/{subfolder}/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_languages(data: List[Dict]) -> Dict[str, str]:
    """Convert languages to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'language'],
            'type': 'language',
            'language_type': item.get('type', ''),
            'typical_speakers': item.get('typical_speakers', []),
            'script': item.get('script', ''),
        })
        
        speakers = item.get('typical_speakers', [])
        
        content = f"""{frontmatter}

# {name}

**Type:** {item.get('type', 'Unknown')}  
**Script:** {item.get('script', 'None')}  
**Typical Speakers:** {', '.join(speakers) if speakers else 'Unknown'}

{item.get('desc', '')}
"""
        files[f"Languages/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_magic_items(data: List[Dict]) -> Dict[str, str]:
    """Convert magic items to markdown."""
    files = {}
    for item in data:
        name = item['name']
        rarity = item.get('rarity', {}).get('name', 'Unknown')
        category = item.get('equipment_category', {}).get('name', 'Wondrous Item')
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'magic-item', rarity.lower().replace(' ', '-')],
            'type': 'magic-item',
            'rarity': rarity,
            'category': category,
            'requires_attunement': item.get('requires_attunement', False),
        })
        
        attunement = ""
        if item.get('requires_attunement'):
            attunement = " *(requires attunement)*"
        
        content = f"""{frontmatter}

# {name}

*{category}, {rarity}*{attunement}

{join_descriptions(item.get('desc', []))}
"""
        files[f"Magic Items/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_magic_schools(data: List[Dict]) -> Dict[str, str]:
    """Convert magic schools to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'magic-school'],
            'type': 'magic-school',
        })
        
        content = f"""{frontmatter}

# {name}

{item.get('desc', '')}
"""
        files[f"Magic Schools/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_monsters(data: List[Dict]) -> Dict[str, str]:
    """Convert monsters to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        # Basic stats
        size = item.get('size', 'Medium')
        m_type = item.get('type', 'unknown')
        alignment = item.get('alignment', 'unaligned')
        
        # AC handling
        ac_list = item.get('armor_class', [])
        if ac_list and isinstance(ac_list, list):
            ac = ac_list[0].get('value', 10) if isinstance(ac_list[0], dict) else ac_list[0]
        else:
            ac = 10
        
        hp = item.get('hit_points', 0)
        hit_dice = item.get('hit_dice', '')
        cr = item.get('challenge_rating', 0)
        xp = item.get('xp', 0)
        
        # Speed
        speed = item.get('speed', {})
        speed_parts = []
        for move_type, value in speed.items():
            if value:
                speed_parts.append(f"{move_type} {value}")
        speed_str = ", ".join(speed_parts)
        
        # Ability scores
        abilities = {
            'STR': item.get('strength', 10),
            'DEX': item.get('dexterity', 10),
            'CON': item.get('constitution', 10),
            'INT': item.get('intelligence', 10),
            'WIS': item.get('wisdom', 10),
            'CHA': item.get('charisma', 10),
        }
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'monster', m_type, f"cr-{cr}"],
            'type': 'monster',
            'size': size,
            'monster_type': m_type,
            'alignment': alignment,
            'armor_class': ac,
            'hit_points': hp,
            'challenge_rating': cr,
            'xp': xp,
        })
        
        # Build stat block
        stat_row = " | ".join(f"**{k}** {v} ({(v-10)//2:+d})" for k, v in abilities.items())
        
        # Senses
        senses = item.get('senses', {})
        senses_parts = []
        for sense, value in senses.items():
            if value:
                senses_parts.append(f"{sense.replace('_', ' ')}: {value}")
        senses_str = ", ".join(senses_parts) if senses_parts else "—"
        
        # Languages
        languages = item.get('languages', '—')
        
        # Special abilities
        special_abilities = item.get('special_abilities', [])
        abilities_section = ""
        if special_abilities:
            abilities_section = "## Special Abilities\n\n"
            for ability in special_abilities:
                abilities_section += f"**{ability.get('name', 'Unknown')}.** {ability.get('desc', '')}\n\n"
        
        # Actions
        actions = item.get('actions', [])
        actions_section = ""
        if actions:
            actions_section = "## Actions\n\n"
            for action in actions:
                actions_section += f"**{action.get('name', 'Unknown')}.** {action.get('desc', '')}\n\n"
        
        # Legendary Actions
        legendary = item.get('legendary_actions', [])
        legendary_section = ""
        if legendary:
            legendary_section = "## Legendary Actions\n\n"
            for action in legendary:
                legendary_section += f"**{action.get('name', 'Unknown')}.** {action.get('desc', '')}\n\n"
        
        content = f"""{frontmatter}

# {name}

*{size} {m_type}, {alignment}*

---

**Armor Class** {ac}  
**Hit Points** {hp} ({hit_dice})  
**Speed** {speed_str}

---

| {stat_row} |

---

**Senses** {senses_str}  
**Languages** {languages}  
**Challenge** {cr} ({xp:,} XP)

---

{abilities_section}
{actions_section}
{legendary_section}
"""
        files[f"Monsters/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_proficiencies(data: List[Dict]) -> Dict[str, str]:
    """Convert proficiencies to markdown."""
    files = {}
    for item in data:
        name = item['name']
        prof_type = item.get('type', 'Other')
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'proficiency', prof_type.lower().replace(' ', '-')],
            'type': 'proficiency',
            'proficiency_type': prof_type,
        })
        
        # References
        classes = extract_ref_names(item.get('classes', []))
        races = extract_ref_names(item.get('races', []))
        
        content = f"""{frontmatter}

# {name}

**Type:** {prof_type}

## Classes

{chr(10).join(f"- [[{c}]]" for c in classes) if classes else "_None_"}

## Races

{chr(10).join(f"- [[{r}]]" for r in races) if races else "_None_"}
"""
        # Organize by type
        subfolder = sanitize_filename(prof_type)
        files[f"Proficiencies/{subfolder}/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_races(data: List[Dict]) -> Dict[str, str]:
    """Convert races to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        # Ability bonuses
        ability_bonuses = []
        for bonus in item.get('ability_bonuses', []):
            ab_score = bonus.get('ability_score', {}).get('name', '')
            ab_bonus = bonus.get('bonus', 0)
            ability_bonuses.append(f"{ab_score} +{ab_bonus}")
        
        traits = extract_ref_names(item.get('traits', []))
        languages = extract_ref_names(item.get('languages', []))
        subraces = extract_ref_names(item.get('subraces', []))
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'race'],
            'type': 'race',
            'speed': item.get('speed', 30),
            'size': item.get('size', 'Medium'),
            'ability_bonuses': ability_bonuses,
            'traits': traits,
            'languages': [l for l in languages],
            'subraces': subraces,
        })
        
        content = f"""{frontmatter}

# {name}

**Size:** {item.get('size', 'Medium')}  
**Speed:** {item.get('speed', 30)} ft.  
**Ability Score Increase:** {', '.join(ability_bonuses)}

## Age

{item.get('age', '')}

## Alignment

{item.get('alignment', '')}

## Size Description

{item.get('size_description', '')}

## Languages

{item.get('language_desc', '')}

## Traits

{chr(10).join(f"- [[{t}]]" for t in traits) if traits else "_None_"}

## Subraces

{chr(10).join(f"- [[{sr}]]" for sr in subraces) if subraces else "_None_"}
"""
        files[f"Races/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_rules(data: List[Dict]) -> Dict[str, str]:
    """Convert rules to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        subsections = item.get('subsections', [])
        subsection_names = extract_ref_names(subsections)
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'rule'],
            'type': 'rule',
            'subsections': subsection_names,
        })
        
        content = f"""{frontmatter}

# {name}

{item.get('desc', '')}

## Subsections

{chr(10).join(f"- [[{s}]]" for s in subsection_names) if subsection_names else "_None_"}
"""
        files[f"Rules/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_rule_sections(data: List[Dict]) -> Dict[str, str]:
    """Convert rule sections to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'rule-section'],
            'type': 'rule-section',
        })
        
        content = f"""{frontmatter}

# {name}

{item.get('desc', '')}
"""
        files[f"Rules/Sections/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_skills(data: List[Dict]) -> Dict[str, str]:
    """Convert skills to markdown."""
    files = {}
    for item in data:
        name = item['name']
        ability = item.get('ability_score', {}).get('name', '')
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'skill'],
            'type': 'skill',
            'ability_score': ability,
        })
        
        content = f"""{frontmatter}

# {name}

**Ability:** [[{ability}]]

{join_descriptions(item.get('desc', []))}
"""
        files[f"Skills/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_spells(data: List[Dict]) -> Dict[str, str]:
    """Convert spells to markdown."""
    files = {}
    for item in data:
        name = item['name']
        level = item.get('level', 0)
        school = item.get('school', {}).get('name', 'Unknown')
        
        level_str = "Cantrip" if level == 0 else f"{level}{'st' if level == 1 else 'nd' if level == 2 else 'rd' if level == 3 else 'th'}-level"
        
        components = item.get('components', [])
        material = item.get('material', '')
        ritual = item.get('ritual', False)
        concentration = item.get('concentration', False)
        
        classes = extract_ref_names(item.get('classes', []))
        
        # Damage info
        damage_info = item.get('damage', {})
        damage_type = damage_info.get('damage_type', {}).get('name', '')
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'spell', school.lower(), f"level-{level}"],
            'type': 'spell',
            'level': level,
            'school': school,
            'casting_time': item.get('casting_time', '1 action'),
            'range': item.get('range', 'Self'),
            'components': components,
            'duration': item.get('duration', 'Instantaneous'),
            'concentration': concentration,
            'ritual': ritual,
            'classes': classes,
            'damage_type': damage_type if damage_type else None,
        })
        
        # Build component string
        comp_str = ", ".join(components)
        if material:
            comp_str += f" ({material})"
        
        # Higher level section
        higher_level = item.get('higher_level', [])
        higher_level_section = ""
        if higher_level:
            higher_level_section = f"\n**At Higher Levels.** {join_descriptions(higher_level)}"
        
        ritual_tag = " (ritual)" if ritual else ""
        conc_tag = "Concentration, " if concentration else ""
        
        content = f"""{frontmatter}

# {name}

*{level_str} {school.lower()}{ritual_tag}*

---

**Casting Time:** {item.get('casting_time', '1 action')}  
**Range:** {item.get('range', 'Self')}  
**Components:** {comp_str}  
**Duration:** {conc_tag}{item.get('duration', 'Instantaneous')}

---

{join_descriptions(item.get('desc', []))}{higher_level_section}

---

**Classes:** {', '.join(f"[[{c}]]" for c in classes)}
"""
        # Organize by level
        level_folder = "Cantrips" if level == 0 else f"Level {level}"
        files[f"Spells/{level_folder}/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_subclasses(data: List[Dict]) -> Dict[str, str]:
    """Convert subclasses to markdown."""
    files = {}
    for item in data:
        name = item['name']
        parent_class = item.get('class', {}).get('name', 'Unknown')
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'subclass', parent_class.lower()],
            'type': 'subclass',
            'class': parent_class,
            'subclass_flavor': item.get('subclass_flavor', ''),
        })
        
        content = f"""{frontmatter}

# {name}

*{item.get('subclass_flavor', '')} for [[{parent_class}]]*

{join_descriptions(item.get('desc', []))}
"""
        files[f"Subclasses/{sanitize_filename(parent_class)}/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_subraces(data: List[Dict]) -> Dict[str, str]:
    """Convert subraces to markdown."""
    files = {}
    for item in data:
        name = item['name']
        parent_race = item.get('race', {}).get('name', 'Unknown')
        
        ability_bonuses = []
        for bonus in item.get('ability_bonuses', []):
            ab_score = bonus.get('ability_score', {}).get('name', '')
            ab_bonus = bonus.get('bonus', 0)
            ability_bonuses.append(f"{ab_score} +{ab_bonus}")
        
        traits = extract_ref_names(item.get('racial_traits', []))
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'subrace'],
            'type': 'subrace',
            'race': parent_race,
            'ability_bonuses': ability_bonuses,
            'traits': traits,
        })
        
        content = f"""{frontmatter}

# {name}

*Subrace of [[{parent_race}]]*

**Ability Score Increase:** {', '.join(ability_bonuses)}

{item.get('desc', '')}

## Racial Traits

{chr(10).join(f"- [[{t}]]" for t in traits) if traits else "_None_"}
"""
        files[f"Subraces/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_traits(data: List[Dict]) -> Dict[str, str]:
    """Convert traits to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        races = extract_ref_names(item.get('races', []))
        subraces = extract_ref_names(item.get('subraces', []))
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'trait'],
            'type': 'trait',
            'races': races,
            'subraces': subraces,
        })
        
        content = f"""{frontmatter}

# {name}

{join_descriptions(item.get('desc', []))}

## Races

{chr(10).join(f"- [[{r}]]" for r in races) if races else "_None_"}

## Subraces

{chr(10).join(f"- [[{sr}]]" for sr in subraces) if subraces else "_None_"}
"""
        files[f"Traits/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_weapon_properties(data: List[Dict]) -> Dict[str, str]:
    """Convert weapon properties to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'weapon-property'],
            'type': 'weapon-property',
        })
        
        content = f"""{frontmatter}

# {name}

{join_descriptions(item.get('desc', []))}
"""
        files[f"Weapon Properties/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_feats(data: List[Dict]) -> Dict[str, str]:
    """Convert feats to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        prerequisites = item.get('prerequisites', [])
        prereq_strs = []
        for prereq in prerequisites:
            if prereq.get('ability_score'):
                prereq_strs.append(f"{prereq['ability_score'].get('name', '')} {prereq.get('minimum_score', 0)}+")
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'feat'],
            'type': 'feat',
            'prerequisites': prereq_strs,
        })
        
        content = f"""{frontmatter}

# {name}

{"**Prerequisites:** " + ", ".join(prereq_strs) if prereq_strs else ""}

{join_descriptions(item.get('desc', []))}
"""
        files[f"Feats/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


def convert_levels(data: List[Dict]) -> Dict[str, str]:
    """Convert class levels to markdown - creates summary pages per class."""
    # Group by class
    by_class = {}
    for item in data:
        class_name = item.get('class', {}).get('name', 'Unknown')
        if class_name not in by_class:
            by_class[class_name] = []
        by_class[class_name].append(item)
    
    files = {}
    for class_name, levels in by_class.items():
        levels.sort(key=lambda x: x.get('level', 0))
        
        frontmatter = create_frontmatter({}, {
            'name': f"{class_name} Level Progression",
            'tags': ['ai_generated', '5e-srd', 'class-levels', class_name.lower()],
            'type': 'class-levels',
            'class': class_name,
        })
        
        # Build level table
        table_rows = []
        for lvl in levels:
            level_num = lvl.get('level', 0)
            prof_bonus = lvl.get('prof_bonus', 2)
            features = extract_ref_names(lvl.get('features', []))
            features_str = ", ".join(features) if features else "—"
            table_rows.append(f"| {level_num} | +{prof_bonus} | {features_str} |")
        
        content = f"""{frontmatter}

# {class_name} Level Progression

| Level | Proficiency Bonus | Features |
|-------|-------------------|----------|
{chr(10).join(table_rows)}
"""
        files[f"Class Levels/{sanitize_filename(class_name)} Levels.md"] = content.strip() + "\n"
    return files


def convert_equipment_categories(data: List[Dict]) -> Dict[str, str]:
    """Convert equipment categories to markdown."""
    files = {}
    for item in data:
        name = item['name']
        
        equipment = extract_ref_names(item.get('equipment', []))
        
        frontmatter = create_frontmatter(item, {
            'name': name,
            'aliases': [item['index']],
            'tags': ['ai_generated', '5e-srd', 'equipment-category'],
            'type': 'equipment-category',
        })
        
        content = f"""{frontmatter}

# {name}

## Equipment in this Category

{chr(10).join(f"- [[{e}]]" for e in equipment) if equipment else "_None_"}
"""
        files[f"Equipment Categories/{sanitize_filename(name)}.md"] = content.strip() + "\n"
    return files


# =============================================================================
# Main conversion logic
# =============================================================================

CONVERTERS = {
    '5e-SRD-Ability-Scores.json': convert_ability_scores,
    '5e-SRD-Alignments.json': convert_alignments,
    '5e-SRD-Backgrounds.json': convert_backgrounds,
    '5e-SRD-Classes.json': convert_classes,
    '5e-SRD-Conditions.json': convert_conditions,
    '5e-SRD-Damage-Types.json': convert_damage_types,
    '5e-SRD-Equipment.json': convert_equipment,
    '5e-SRD-Equipment-Categories.json': convert_equipment_categories,
    '5e-SRD-Feats.json': convert_feats,
    '5e-SRD-Features.json': convert_features,
    '5e-SRD-Languages.json': convert_languages,
    '5e-SRD-Levels.json': convert_levels,
    '5e-SRD-Magic-Items.json': convert_magic_items,
    '5e-SRD-Magic-Schools.json': convert_magic_schools,
    '5e-SRD-Monsters.json': convert_monsters,
    '5e-SRD-Proficiencies.json': convert_proficiencies,
    '5e-SRD-Races.json': convert_races,
    '5e-SRD-Rules.json': convert_rules,
    '5e-SRD-Rule-Sections.json': convert_rule_sections,
    '5e-SRD-Skills.json': convert_skills,
    '5e-SRD-Spells.json': convert_spells,
    '5e-SRD-Subclasses.json': convert_subclasses,
    '5e-SRD-Subraces.json': convert_subraces,
    '5e-SRD-Traits.json': convert_traits,
    '5e-SRD-Weapon-Properties.json': convert_weapon_properties,
}


def main():
    """Main conversion function."""
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_files = 0
    
    for json_file, converter in CONVERTERS.items():
        input_path = INPUT_DIR / json_file
        
        if not input_path.exists():
            print(f"⚠️  Skipping {json_file} (not found)")
            continue
        
        print(f"📄 Processing {json_file}...")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        files = converter(data)
        
        for filepath, content in files.items():
            output_path = OUTPUT_DIR / filepath
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            total_files += 1
        
        print(f"   ✅ Created {len(files)} files")
    
    print(f"\n🎉 Conversion complete! Total files created: {total_files}")
    print(f"📁 Output location: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

