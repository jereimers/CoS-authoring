#!/usr/bin/env python3
"""
Replace <!-- .?DM ONLY --> comments with %% throughout DM Wiki and Player Wiki folders.
"""

import re
from pathlib import Path

# Pattern to match: <!-- DM ONLY --> or <!-- XDM ONLY --> (with optional single char before DM)
PATTERN = re.compile(r'%%\n%%')
REPLACEMENT = '%%'

# Folders to process
FOLDERS = ['DM Wiki']

def process_file(filepath: Path) -> bool:
    """Process a single file, returning True if changes were made."""
    try:
        content = filepath.read_text(encoding='utf-8')
        new_content = PATTERN.sub(REPLACEMENT, content)
        
        if content != new_content:
            filepath.write_text(new_content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    base_path = Path(__file__).parent.parent  # Go up from _scripts to vault root
    
    total_files = 0
    modified_files = 0
    
    for folder_name in FOLDERS:
        folder_path = base_path / folder_name
        
        if not folder_path.exists():
            print(f"Warning: Folder '{folder_name}' not found at {folder_path}")
            continue
        
        print(f"Processing folder: {folder_name}")
        
        # Process all markdown files recursively
        for filepath in folder_path.rglob('*.md'):
            total_files += 1
            if process_file(filepath):
                modified_files += 1
                print(f"  Modified: {filepath.relative_to(base_path)}")
    
    print(f"\nDone! Processed {total_files} files, modified {modified_files} files.")

if __name__ == '__main__':
    main()

