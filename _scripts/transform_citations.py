#!/usr/bin/env python3
"""
Transform HTML citation spans into wikilinks pointing to CoS-WotC chapter files.

This script:
1. Reads Lore of Barovia and History of Barovia files
2. Finds all <span class="citation">...</span> tags
3. Maps citation text to the correct chapter file and section
4. Replaces HTML spans with wikilinks like [[filename#section]]
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Base paths
AUTHORING_DIR = Path("/Users/blor/blorgit/blors-obsidian-tomb/authoring")
SOURCE_DIR = AUTHORING_DIR / "Source/CoS-WotC/Chapters"
RELOADED_DIR = AUTHORING_DIR / "Source/CoS-Reloaded"

# Files to process - can be set via command line or default to specific files
DEFAULT_TARGET_FILES = [
    RELOADED_DIR / "Chapter 2 - The Land of Barovia/Lore of Barovia.md",
    RELOADED_DIR / "Chapter 2 - The Land of Barovia/History of Barovia.md"
]


def build_section_mapping() -> Dict[str, Tuple[str, str]]:
    """
    Build a mapping from section names to (filename, section_heading).

    Returns:
        Dict mapping normalized section names to (chapter_filename, heading_text)
    """
    mapping = {}

    # Iterate through all chapter files
    for chapter_file in sorted(SOURCE_DIR.glob("*.md")):
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract all headings (# through #####)
        headings = re.findall(r'^(#{1,5})\s+(.+?)(?:\s+%%.*%%)?$', content, re.MULTILINE)

        for level, heading in headings:
            # Clean heading text (remove special markers, page numbers, etc.)
            clean_heading = heading.strip()

            # Normalize for mapping (lowercase, remove punctuation)
            normalized = re.sub(r'[^\w\s]', '', clean_heading).lower().strip()

            # Store mapping with full normalized name
            if normalized:
                mapping[normalized] = (chapter_file.name, clean_heading)

            # Also store chapter names without "chapter X:" prefix for easier matching
            if level == '#' and 'chapter' in normalized:
                # Extract just the chapter title without "chapter X:"
                title_only = re.sub(r'^chapter\s+\d+\s+', '', normalized).strip()
                if title_only and title_only not in mapping:
                    mapping[title_only] = (chapter_file.name, clean_heading)

    return mapping


def extract_citation_text(citation_span: str) -> str:
    """
    Extract the text content from a citation span.

    Args:
        citation_span: Full HTML span tag like '<span class="citation">Text (p. 23)</span>'

    Returns:
        The inner text without page numbers
    """
    # Extract text between tags
    match = re.search(r'<span class="citation">(.+?)</span>', citation_span)
    if not match:
        return ""

    text = match.group(1)

    # Remove page numbers like "(p. 23)" or "(p. 23-24)"
    text = re.sub(r'\s*\(p\.\s*\d+(?:-\d+)?\)', '', text)

    # Remove "Chapter X: " prefix
    text = re.sub(r'^Chapter \d+:\s*', '', text)

    return text.strip()


def normalize_for_lookup(text: str) -> str:
    """Normalize text for dictionary lookup."""
    # Remove section codes like "S3. "
    text = re.sub(r'^[A-Z]\d+\.\s+', '', text)

    # Remove special characters and convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', text).lower().strip()

    return normalized


def create_wikilink(citation_text: str, section_mapping: Dict[str, Tuple[str, str]]) -> str:
    """
    Create a wikilink from citation text.

    Args:
        citation_text: The cleaned citation text (without page numbers)
        section_mapping: Dictionary mapping normalized names to (filename, heading)

    Returns:
        Wikilink string like "[[filename#Section Heading]]"
    """
    # Try to find the section in our mapping
    normalized = normalize_for_lookup(citation_text)

    if normalized in section_mapping:
        filename, heading = section_mapping[normalized]
        # Remove file extension
        filename_base = filename.replace('.md', '')
        return f"[[{filename_base}#{heading}]]"

    # Try fuzzy matching for partial matches (e.g., "Areas of Barovia" might match "Areas of Barovia (A-I)")
    for key, (filename, heading) in section_mapping.items():
        if normalized in key or key.startswith(normalized):
            filename_base = filename.replace('.md', '')
            print(f"  INFO: Fuzzy match '{citation_text}' -> '{heading}'")
            return f"[[{filename_base}#{heading}]]"

    # If not found, return the original text wrapped in a wikilink (will show as broken link)
    print(f"  WARNING: Could not map citation: '{citation_text}' (normalized: '{normalized}')")
    return f"[[{citation_text}]]"


def transform_citations_in_file(filepath: Path, section_mapping: Dict[str, Tuple[str, str]], dry_run: bool = True):
    """
    Transform all citations in a file.

    Args:
        filepath: Path to the markdown file
        section_mapping: Dictionary mapping section names to files
        dry_run: If True, only print changes without modifying files
    """
    print(f"\nProcessing: {filepath.name}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all citation spans
    citation_pattern = r'<span class="citation">([^<]+)</span>'
    citations = re.findall(citation_pattern, content)

    if not citations:
        print("  No citations found")
        return

    print(f"  Found {len(citations)} citations")

    # Track changes
    changes = []
    new_content = content

    for citation_html in re.finditer(citation_pattern, content):
        full_match = citation_html.group(0)
        citation_inner = citation_html.group(1)

        # Skip if already contains a wikilink
        if '[[' in citation_inner:
            print(f"  SKIP (already wikilink): {citation_inner}")
            continue

        # Extract clean text
        clean_text = extract_citation_text(full_match)

        # Create wikilink
        wikilink = create_wikilink(clean_text, section_mapping)

        # Track change
        changes.append((full_match, wikilink))

        # Replace in content
        new_content = new_content.replace(full_match, wikilink, 1)

    if changes:
        print(f"  Transformed {len(changes)} citations")

        if dry_run:
            print("  DRY RUN - showing first 5 changes:")
            for i, (old, new) in enumerate(changes[:5], 1):
                print(f"    {i}. {old[:60]}... -> {new}")
        else:
            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✓ File updated")
    else:
        print("  No changes needed")


def find_files_with_citations(base_dir: Path) -> List[Path]:
    """
    Find all markdown files in a directory that contain citation spans.

    Args:
        base_dir: Directory to search

    Returns:
        List of file paths containing citations
    """
    files_with_citations = []

    for md_file in base_dir.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '<span class="citation">' in content:
                    files_with_citations.append(md_file)
        except Exception as e:
            print(f"  WARNING: Could not read {md_file}: {e}")

    return sorted(files_with_citations)


def main():
    """Main execution function."""
    import sys

    # Check flags
    dry_run = '--execute' not in sys.argv
    process_all = '--all' in sys.argv

    # Determine which files to process
    if process_all:
        print("=" * 70)
        print("SCANNING for all files with citations in CoS-Reloaded...")
        print("=" * 70)
        target_files = find_files_with_citations(RELOADED_DIR)
        print(f"Found {len(target_files)} files with citations\n")
    else:
        target_files = DEFAULT_TARGET_FILES

    if dry_run:
        print("=" * 70)
        print("DRY RUN MODE - No files will be modified")
        print("Run with --execute flag to apply changes")
        if not process_all:
            print("Run with --all flag to process all files in CoS-Reloaded")
        print("=" * 70)
    else:
        print("=" * 70)
        print("EXECUTE MODE - Files will be modified!")
        print("=" * 70)

    # Build section mapping
    print("\nBuilding section mapping from chapter files...")
    section_mapping = build_section_mapping()
    print(f"Mapped {len(section_mapping)} sections from {len(list(SOURCE_DIR.glob('*.md')))} chapter files")

    # Process each target file
    for filepath in target_files:
        if filepath.exists():
            transform_citations_in_file(filepath, section_mapping, dry_run=dry_run)
        else:
            print(f"\nWARNING: File not found: {filepath}")

    if dry_run:
        print("\n" + "=" * 70)
        print("DRY RUN COMPLETE - No files were modified")
        print("Review the output above, then run with --execute to apply changes")
        if not process_all:
            print("Add --all flag to process all files in CoS-Reloaded")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("EXECUTION COMPLETE - Files have been modified")
        print("=" * 70)


if __name__ == "__main__":
    main()
