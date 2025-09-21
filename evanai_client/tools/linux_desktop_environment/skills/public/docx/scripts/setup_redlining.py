#!/usr/bin/env python3
"""
Setup tracked changes infrastructure for unpacked Word documents.
Usage: python setup_redlines.py unpacked_dir/
"""

import random
import re
import sys
from pathlib import Path

# XML namespaces
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def generate_rsid():
    """Generate random 8-character hex RSID."""
    return "".join(random.choices("0123456789ABCDEF", k=8))


def create_people_xml():
    """Create people.xml with Claude author."""
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:people xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml">
  <w15:person w15:author="Claude">
    <w15:presenceInfo w15:providerId="None" w15:userId="Claude"/>
  </w15:person>
</w15:people>"""


def update_people_xml(file_path):
    """Create or update people.xml to include Claude author."""
    if file_path.exists():
        # For existing files, use text manipulation to preserve formatting
        content = file_path.read_text(encoding="utf-8")

        # Check if Claude already exists
        if 'w15:author="Claude"' in content or 'author="Claude"' in content:
            return

        # Add Claude person element before closing tag
        claude_entry = """  <w15:person w15:author="Claude">
    <w15:presenceInfo w15:providerId="None" w15:userId="Claude"/>
  </w15:person>"""
        content = re.sub(r"(</w15:people>)", f"{claude_entry}\n\\1", content)
        file_path.write_text(content, encoding="utf-8")
    else:
        # Create new people.xml
        file_path.write_text(create_people_xml(), encoding="utf-8")


def add_content_type(file_path):
    """Add people.xml content type to [Content_Types].xml if not already present."""
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if people.xml already exists
    if "/word/people.xml" in content:
        return

    # Find the closing tag and insert before it
    override_entry = '  <Override PartName="/word/people.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.people+xml" />'

    # Insert before </Types> tag, preserving namespace prefix if present
    content = re.sub(r"(</\w*:?Types>)", f"{override_entry}\n\\1", content)

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def add_relationship(file_path):
    """Add people.xml relationship to document.xml.rels if not already present."""
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if people.xml relationship already exists
    if 'Target="people.xml"' in content:
        return

    # Extract the namespace prefix if present
    prefix_match = re.search(r"<(\w+):Relationships", content)
    prefix = f"{prefix_match.group(1)}:" if prefix_match else ""

    # Find max relationship ID
    id_matches = re.findall(r'Id="rId(\d+)"', content)
    max_id = max((int(id_str) for id_str in id_matches), default=0)
    next_id = max_id + 1

    # Create the relationship entry (use Microsoft 2011 people relationship type)
    rel_entry = f'  <{prefix}Relationship Id="rId{next_id}" Type="http://schemas.microsoft.com/office/2011/relationships/people" Target="people.xml" />'

    # Insert before closing tag
    content = re.sub(r"(</" + prefix + r"Relationships>)", f"{rel_entry}\n\\1", content)

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def enable_tracking(file_path, rsid):
    """Enable track revisions and add RSID to settings.xml.

    Places elements per OOXML schema order:
    - trackRevisions: early (before defaultTabStop)
    - rsids: late (after compat)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Get namespace prefix (usually 'w')
    settings_match = re.search(r"<(\w+):settings", content)
    prefix = settings_match.group(1) if settings_match else "w"

    # Add trackRevisions if not present (goes early in sequence)
    if f"<{prefix}:trackRevisions" not in content:
        # Try insertion points in preference order
        for pattern, replacement in [
            (f"(  <{prefix}:documentProtection)", f"  <{prefix}:trackRevisions/>\n\\1"),
            (f"(  <{prefix}:defaultTabStop)", f"  <{prefix}:trackRevisions/>\n\\1"),
            (f"(<{prefix}:settings[^>]*>)", f"\\1\n  <{prefix}:trackRevisions/>"),
        ]:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content, count=1)
                break

    # Build rsids section
    rsids = f'''  <{prefix}:rsids>
    <{prefix}:rsidRoot {prefix}:val="{rsid}"/>
    <{prefix}:rsid {prefix}:val="{rsid}"/>
  </{prefix}:rsids>
'''

    # Add rsids if not present (goes late, after compat)
    if f"<{prefix}:rsids>" not in content:
        # Try insertion points in preference order
        for pattern, replacement in [
            (f"(  </{prefix}:compat>\n)", f"\\1{rsids}"),  # After compat closing tag
            (
                f"(  <{prefix}:clrSchemeMapping)",
                f"{rsids}\\1",
            ),  # Before clrSchemeMapping
            (f"(</{prefix}:settings>)", f"{rsids}\\1"),  # Before settings closing tag
        ]:
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, replacement, content, count=1)
                break
    elif f'{prefix}:val="{rsid}"' not in content:
        # Add to existing rsids section
        content = re.sub(
            f"(</{prefix}:rsids>)",
            f'    <{prefix}:rsid {prefix}:val="{rsid}"/>\n  \\1',
            content,
            count=1,
        )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def setup_redlines(unpacked_dir):
    """Set up tracked changes infrastructure in unpacked directory."""
    unpacked_path = Path(unpacked_dir)

    if not unpacked_path.exists() or not unpacked_path.is_dir():
        raise ValueError(f"Directory not found: {unpacked_dir}")

    rsid = generate_rsid()

    # Create or update word/people.xml
    people_file = unpacked_path / "word" / "people.xml"
    update_people_xml(people_file)

    # Update XML files
    add_content_type(unpacked_path / "[Content_Types].xml")
    add_relationship(unpacked_path / "word" / "_rels" / "document.xml.rels")
    enable_tracking(unpacked_path / "word" / "settings.xml", rsid)

    print(f"✓ Setup complete in: {unpacked_dir}")
    print(f"✓ RSID: {rsid}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_redlines.py unpacked_dir/")
        sys.exit(1)

    unpacked_dir = sys.argv[1]

    try:
        setup_redlines(unpacked_dir)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
