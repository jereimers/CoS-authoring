#!/usr/bin/env python3
"""
Area File Standardization Script

This script standardizes all Area files in the Curse of Strahd Reloaded vault:
1. Extracts WotC area codes from filenames (e.g., "K. Castle Ravenloft" -> code "K")
2. Renames files/directories to remove the code prefix
3. Adds/updates the area_code property in frontmatter
4. Standardizes content structure to match template

No external dependencies required - uses pure Python.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Paths
VAULT_ROOT = Path("/Users/blor/blorgit/Curse-of-Strahd-Reloaded")
AREAS_DIR = VAULT_ROOT / "DM Wiki" / "Entities" / "Areas"

# Pattern to match WotC area codes in filenames
AREA_CODE_PATTERN = re.compile(r'^([A-Z][0-9]*[a-z]?)\.\s+(.+)$')

# Standard frontmatter fields (in order)
FRONTMATTER_FIELDS = [
    "type",
    "name",
    "aliases",
    "area_code",
    "WotC_ref",
    "CoS-R_ref",
    "parent_region",
    "arcs",
    "connected_locations",
    "notable_npcs",
    "threat_level",
    "first_appearance_date",
    "tags",
    "key_factions",
    "area_type",
    "first_appearance_session",
    "scene",
    "encounter",
    "item(s)",
    "handouts",
    "loot",
]

# Template body structure
BODY_TEMPLATE = """# Overview

{overview}

# What the party knows

{what_party_knows}

# Notable places

{notable_places}

# Notable figures

{notable_figures}

# Visits

{visits}

<!-- DM ONLY -->
# Map
{map_content}

# Images
{images}

# Notes
{notes}
<!-- /DM ONLY -->"""


def parse_yaml_value(value_str: str) -> Any:
    """Parse a YAML value string into Python object."""
    value_str = value_str.strip()
    
    if not value_str:
        return None
    
    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False
    
    try:
        if '.' in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass
    
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]
    
    if value_str == '|':
        return '|'
    
    return value_str


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Parse YAML frontmatter from content."""
    if not content.startswith("---"):
        return None, content
    
    lines = content.split('\n')
    end_idx = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break
    
    if end_idx == -1:
        return None, content
    
    frontmatter_lines = lines[1:end_idx]
    body = '\n'.join(lines[end_idx + 1:])
    
    fm = {}
    current_key = None
    current_list = None
    multiline_value = None
    multiline_indent = 0
    
    for line in frontmatter_lines:
        if multiline_value is not None:
            if line.startswith(' ' * multiline_indent) and line.strip():
                multiline_value.append(line.strip())
                continue
            else:
                fm[current_key] = '\n'.join(multiline_value)
                multiline_value = None
        
        if current_list is not None and line.startswith('  - '):
            item = line[4:].strip()
            if (item.startswith('"') and item.endswith('"')) or \
               (item.startswith("'") and item.endswith("'")):
                item = item[1:-1]
            current_list.append(item)
            continue
        elif current_list is not None and not line.startswith('  '):
            fm[current_key] = current_list if current_list else None
            current_list = None
        
        if ':' in line and not line.startswith(' '):
            parts = line.split(':', 1)
            key = parts[0].strip()
            value_str = parts[1].strip() if len(parts) > 1 else ''
            
            current_key = key
            
            if not value_str:
                current_list = []
                continue
            
            value = parse_yaml_value(value_str)
            
            if value == '|':
                multiline_value = []
                multiline_indent = 2
            else:
                fm[key] = value
    
    if current_list is not None:
        fm[current_key] = current_list if current_list else None
    if multiline_value is not None:
        fm[current_key] = '\n'.join(multiline_value)
    
    return fm, body


def extract_area_code(filename: str) -> Tuple[Optional[str], str]:
    """Extract area code from filename and return (code, clean_name)."""
    match = AREA_CODE_PATTERN.match(filename)
    if match:
        return match.group(1), match.group(2)
    return None, filename


def extract_section(content: str, header: str, level: int = 1) -> str:
    """Extract content under a markdown header."""
    pattern = rf'^{"#" * level}\s*{re.escape(header)}\s*$'
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    
    start = match.end()
    next_header = re.search(rf'^#{"{1," + str(level) + "}"}\s+\S', content[start:], re.MULTILINE)
    if next_header:
        end = start + next_header.start()
    else:
        end = len(content)
    
    return content[start:end].strip()


def standardize_tags(tags: Any) -> List[str]:
    """Ensure tags list has required tags."""
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [tags]
    else:
        tags = list(tags)
    
    if 'area' not in tags:
        tags.insert(0, 'area')
    if 'cos' not in tags:
        tags.insert(1, 'cos')
    
    if 'needs_filling' in tags:
        tags.remove('needs_filling')
    
    return tags


def normalize_frontmatter(fm: Optional[Dict[str, Any]], area_name: str, area_code: Optional[str]) -> Dict[str, Any]:
    """Normalize frontmatter to standard format."""
    if fm is None:
        fm = {}
    
    result = {}
    
    defaults = {
        "type": "Area",
        "name": area_name,
    }
    
    for field in FRONTMATTER_FIELDS:
        key = field
        if field == "arcs" and "acts" in fm:
            key = "acts"
        
        if key in fm and fm[key] is not None:
            value = fm[key]
            
            if isinstance(value, str):
                placeholders = ["[[Location or Region]]", "[[Primary Location]]"]
                if any(p in value for p in placeholders):
                    value = None
            elif isinstance(value, list):
                cleaned = []
                for item in value:
                    if isinstance(item, str):
                        if item.strip() and item.strip() != "-":
                            cleaned.append(item)
                    elif item is not None:
                        cleaned.append(item)
                value = cleaned if cleaned else None
            
            result[field] = value
        else:
            result[field] = defaults.get(field)
    
    if area_code and not result.get("area_code"):
        result["area_code"] = area_code
    
    if result.get("name") is None:
        result["name"] = area_name
    
    result["tags"] = standardize_tags(result.get("tags"))
    
    return result


def format_yaml_value(value: Any, indent: int = 0) -> str:
    """Format a Python value as YAML string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if '\n' in value:
            lines = ["|\n"]
            for line in value.split('\n'):
                lines.append("  " + line + "\n")
            return ''.join(lines).rstrip('\n')
        if ':' in value or '"' in value or value.startswith('[') or value.startswith('{') or value.startswith('!'):
            return f'"{value}"'
        return value
    return str(value)


def build_yaml_frontmatter(fm: Dict[str, Any]) -> str:
    """Build YAML frontmatter string with proper ordering."""
    lines = ["---"]
    
    for field in FRONTMATTER_FIELDS:
        value = fm.get(field)
        if value is None:
            lines.append(f"{field}:")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{field}:")
            else:
                lines.append(f"{field}:")
                for item in value:
                    if isinstance(item, str):
                        if '"' in item:
                            lines.append(f"  - '{item}'")
                        else:
                            lines.append(f'  - "{item}"')
                    else:
                        lines.append(f"  - {item}")
        elif isinstance(value, str) and '\n' in value:
            lines.append(f"{field}: |")
            for line in value.split('\n'):
                lines.append(f"  {line}")
        else:
            formatted = format_yaml_value(value)
            lines.append(f"{field}: {formatted}")
    
    lines.append("---")
    return "\n".join(lines)


def extract_existing_content(body: str, has_frontmatter: bool) -> Dict[str, str]:
    """Extract existing content sections from body."""
    original_body = body
    
    # Clean up body - remove DM ONLY markers
    body = re.sub(r'<!--\s*DM[- ]?ONLY\s*-->', '', body, flags=re.IGNORECASE)
    body = re.sub(r'<!--\s*/\s*DM[- ]?ONLY\s*-->', '', body, flags=re.IGNORECASE)
    body = re.sub(r'%%\s*an area is a location.*?%%', '', body, flags=re.DOTALL)
    
    content = {
        "overview": "",
        "what_party_knows": "",
        "notable_places": "",
        "notable_figures": "",
        "visits": "",
        "map_content": "",
        "images": "",
        "notes": "",
    }
    
    # Extract sections
    content["overview"] = extract_section(body, "Overview", 1)
    content["what_party_knows"] = extract_section(body, "What the party knows", 1)
    content["notable_places"] = extract_section(body, "Notable places", 1)
    content["notable_figures"] = extract_section(body, "Notable figures", 1)
    content["visits"] = extract_section(body, "Visits", 1)
    content["map_content"] = extract_section(body, "Map", 1)
    content["images"] = extract_section(body, "Images", 1)
    content["notes"] = extract_section(body, "Notes", 1)
    
    # Also check for Areas section
    if not content["notable_places"]:
        areas_section = extract_section(body, "Areas", 1)
        if areas_section:
            content["notable_places"] = areas_section
    
    # Check for Residents section
    if not content["notable_figures"]:
        residents_section = extract_section(body, "Residents", 1)
        if residents_section:
            content["notable_figures"] = residents_section
    
    # Check for Sources section
    sources_section = extract_section(body, "Sources", 1)
    if sources_section:
        if content["notes"]:
            content["notes"] += "\n\n# Sources\n" + sources_section
        else:
            content["notes"] = "# Sources\n" + sources_section
    
    # If no frontmatter and no structured content, treat entire body as notes
    has_structured_content = any([
        content["overview"], 
        content["what_party_knows"], 
        content["notable_places"],
        content["notable_figures"],
        content["map_content"]
    ])
    
    if not has_frontmatter and not has_structured_content and body.strip():
        # This is a raw file - preserve entire content as notes
        # Remove "# WotC source:" header if present, keep rest
        cleaned = re.sub(r'^#\s*WotC\s*source:?\s*\n?', '', body.strip(), flags=re.IGNORECASE)
        content["notes"] = cleaned.strip()
    
    # Set defaults
    if not content["visits"]:
        content["visits"] = "*To be updated during play.*"
    
    return content


def standardize_area_file(filepath: Path, new_name: str, area_code: Optional[str]) -> str:
    """Standardize an Area file and return the new content."""
    content = filepath.read_text(encoding='utf-8')
    
    # Handle minimal files
    if len(content.strip()) < 10:
        fm = normalize_frontmatter(None, new_name, area_code)
        body_content = {
            "overview": "",
            "what_party_knows": "",
            "notable_places": "",
            "notable_figures": "",
            "visits": "*To be updated during play.*",
            "map_content": "",
            "images": "",
            "notes": "",
        }
        return build_yaml_frontmatter(fm) + "\n" + BODY_TEMPLATE.format(**body_content)
    
    # Parse frontmatter and body
    fm, body = parse_frontmatter(content)
    has_frontmatter = fm is not None
    
    # Normalize frontmatter
    fm = normalize_frontmatter(fm, new_name, area_code)
    
    # Extract existing content
    body_content = extract_existing_content(body, has_frontmatter)
    
    # Build new content
    new_content = build_yaml_frontmatter(fm) + "\n" + BODY_TEMPLATE.format(**body_content)
    
    return new_content


def get_all_paths_to_rename(base_dir: Path) -> List[Tuple[Path, str, Optional[str]]]:
    """
    Get all files and directories that need renaming.
    Returns list of (path, new_name, area_code).
    Sorted so deepest paths come first.
    """
    paths = []
    
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        
        for d in dirs:
            code, clean_name = extract_area_code(d)
            if code:
                paths.append((root_path / d, clean_name, code))
        
        for f in files:
            if f.endswith('.md'):
                name = f[:-3]
                code, clean_name = extract_area_code(name)
                if code:
                    paths.append((root_path / f, clean_name + '.md', code))
    
    # Sort by path depth (deepest first)
    paths.sort(key=lambda x: len(x[0].parts), reverse=True)
    
    return paths


def main():
    """Main function to standardize all Area files."""
    print("Phase 1: Collecting paths to rename...")
    
    paths_to_rename = get_all_paths_to_rename(AREAS_DIR)
    print(f"Found {len(paths_to_rename)} paths to rename")
    
    rename_map = {}
    
    print("\nPhase 2: Renaming and standardizing files (deepest first)...")
    for old_path, new_name, code in paths_to_rename:
        new_path = old_path.parent / new_name
        
        if old_path.exists():
            old_rel = old_path.relative_to(VAULT_ROOT)
            new_rel = new_path.relative_to(VAULT_ROOT)
            rename_map[str(old_rel)] = str(new_rel)
            
            print(f"  {old_path.name} -> {new_name}")
            
            # If it's a file, update content first
            if old_path.is_file() and old_path.suffix == '.md':
                try:
                    area_name = new_name[:-3] if new_name.endswith('.md') else new_name
                    new_content = standardize_area_file(old_path, area_name, code)
                    old_path.write_text(new_content, encoding='utf-8')
                except Exception as e:
                    print(f"    ERROR standardizing: {e}")
            
            # Rename the path
            try:
                if old_path.is_dir():
                    # Use shutil.move for directories
                    shutil.move(str(old_path), str(new_path))
                else:
                    old_path.rename(new_path)
            except Exception as e:
                print(f"    ERROR renaming: {e}")
    
    print(f"\nPhase 3: Standardizing remaining Area files...")
    
    area_files = list(AREAS_DIR.rglob("*.md"))
    processed = 0
    skipped = 0
    
    for filepath in sorted(area_files):
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Skip if already processed (has our standard structure)
            if content.startswith("---\ntype: Area\n"):
                fm, body = parse_frontmatter(content)
                if fm and fm.get("type") == "Area":
                    # Check if body has our template structure
                    if "# Overview" in body and "<!-- DM ONLY -->" in body:
                        skipped += 1
                        continue
            
            area_name = filepath.stem
            
            # Get area_code from frontmatter if present
            fm, _ = parse_frontmatter(content)
            existing_code = fm.get("area_code") if fm else None
            
            # Standardize the file
            new_content = standardize_area_file(filepath, area_name, existing_code)
            filepath.write_text(new_content, encoding='utf-8')
            processed += 1
            
            if processed % 50 == 0:
                print(f"  Processed {processed} files...")
                
        except Exception as e:
            print(f"  ERROR processing {filepath.name}: {e}")
    
    print(f"\nDone!")
    print(f"  Renamed: {len(paths_to_rename)} paths")
    print(f"  Standardized: {processed} files")
    print(f"  Skipped (already done): {skipped} files")


if __name__ == "__main__":
    main()
