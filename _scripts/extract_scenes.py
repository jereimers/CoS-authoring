#!/usr/bin/env python3
"""
Extract scenes from Arc files and create scene pages in DM Wiki/Scenes.
"""

import os
import re
from pathlib import Path

# Paths
WORKSPACE = Path("/Users/blor/blorgit/Curse-of-Strahd-Reloaded")
SOURCE_DIR = WORKSPACE / "Source/CoS-R"
SCENES_DIR = WORKSPACE / "DM Wiki/Scenes"

# Arc name pattern
ARC_PATTERN = re.compile(r"^Arc ([A-Z]) - (.+)\.md$")

# Scene header pattern (# or ## followed by letter+number+optional_letter. Scene Name)
SCENE_HEADER_PATTERN = re.compile(r"^(#{1,3})\s+([A-Z])(\d+)([a-z])?\.(.+)$")

# Map arcs to their acts
ARC_TO_ACT = {
    "A": "Act I - Into the Mists",
    "B": "Act I - Into the Mists", 
    "C": "Act I - Into the Mists",
    "D": "Act II - The Shadowed Town",
    "E": "Act II - The Shadowed Town",
    "F": "Act II - The Shadowed Town",
    "G": "Act II - The Shadowed Town",
    "H": "Act II - The Shadowed Town",
    "I": "Act II - The Shadowed Town",
    "J": "Act III - The Broken Land",
    "K": "Act III - The Broken Land",
    "L": "Act III - The Broken Land",
    "M": "Act III - The Broken Land",
    "N": "Act III - The Broken Land",
    "O": "Act III - The Broken Land",
    "P": "Act III - The Broken Land",
    "Q": "Act III - The Broken Land",
    "R": "Act IV - Secrets of the Ancient",
    "S": "Act IV - Secrets of the Ancient",
    "T": "Act IV - Secrets of the Ancient",
    "U": "Act IV - Secrets of the Ancient",
}

def find_arc_files():
    """Find all Arc .md files in the Source directory."""
    arc_files = []
    for act_dir in SOURCE_DIR.iterdir():
        if act_dir.is_dir() and act_dir.name.startswith("Act"):
            for file in act_dir.iterdir():
                if file.is_file() and ARC_PATTERN.match(file.name):
                    arc_files.append(file)
    return sorted(arc_files, key=lambda f: f.name)

def parse_scenes_from_arc(arc_file):
    """Parse scene headers from an Arc file."""
    scenes = []
    arc_match = ARC_PATTERN.match(arc_file.name)
    if not arc_match:
        return scenes
    
    arc_letter = arc_match.group(1)
    arc_name = arc_match.group(2)
    
    with open(arc_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_scene = None
    current_content = []
    
    for i, line in enumerate(lines):
        match = SCENE_HEADER_PATTERN.match(line.strip())
        if match:
            # Save previous scene if exists
            if current_scene:
                current_scene['content'] = ''.join(current_content).strip()
                scenes.append(current_scene)
            
            # Start new scene
            header_level = len(match.group(1))  # 1, 2, or 3
            scene_letter = match.group(2)
            scene_number = match.group(3)
            scene_subletter = match.group(4) or ""
            scene_name = match.group(5).strip()
            
            # Clean up scene name (remove wiki links)
            clean_name = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', scene_name)
            
            scene_code = f"{scene_letter}{scene_number}{scene_subletter}"
            
            current_scene = {
                'arc_letter': arc_letter,
                'arc_name': arc_name,
                'code': scene_code,
                'name': clean_name,
                'full_name': f"{scene_code}. {clean_name}",
                'header_level': header_level,
                'line_number': i + 1
            }
            current_content = []
        elif current_scene:
            current_content.append(line)
    
    # Don't forget the last scene
    if current_scene:
        current_scene['content'] = ''.join(current_content).strip()
        scenes.append(current_scene)
    
    return scenes

def create_scene_page(scene, scenes_dir):
    """Create a scene page file."""
    arc_letter = scene['arc_letter']
    arc_name = scene['arc_name']
    scene_code = scene['code']
    scene_name = scene['name']
    full_name = scene['full_name']
    
    # Create filename (sanitize for filesystem)
    safe_name = re.sub(r'[<>:"/\\|?*]', '', scene_name)
    filename = f"{scene_code} - {safe_name}.md"
    filepath = scenes_dir / filename
    
    # Extract potential location from scene name
    location = ""
    
    # Create CoS-R reference (link to original Arc file with heading anchor)
    cos_r_ref = f"[[Arc {arc_letter} - {arc_name}#{full_name}]]"
    
    # Create frontmatter
    frontmatter = f"""---
party_presence:
npc_presence:
arc: "[[Arc {arc_letter} - {arc_name}]]"
CoS-R_Ref: "{cos_r_ref}"
location: {location}
session:
party_level:
combat_possible?: false
has_vignette: false
tags:
  - cos
  - scene
  - ai_generated
---
"""
    
    # Create body
    body = f"""<!-- DM ONLY -->
%% a scene is a chunk of role-playing not requiring initiative -- it has NPCs, a setting, party members present, etc. %%
<!-- /DM ONLY -->
# {scene_code}. {scene_name}

## Vignette


"""
    
    content = frontmatter + body
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def main():
    # Ensure scenes directory exists
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all arc files
    arc_files = find_arc_files()
    print(f"Found {len(arc_files)} Arc files")
    
    total_scenes = 0
    
    for arc_file in arc_files:
        scenes = parse_scenes_from_arc(arc_file)
        print(f"  {arc_file.name}: {len(scenes)} scenes")
        
        for scene in scenes:
            filepath = create_scene_page(scene, SCENES_DIR)
            total_scenes += 1
    
    print(f"\nCreated {total_scenes} scene pages in {SCENES_DIR}")

if __name__ == "__main__":
    main()


