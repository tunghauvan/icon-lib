import os
import re
from pathlib import Path

def cleanup_icons_md():
    libs_dir = Path(__file__).parent / 'libs'
    downloads_dir = Path(__file__).parent / 'downloads' / 'icon'
    md_path = libs_dir / 'icons.md'

    if not md_path.exists():
        print("icons.md not found.")
        return

    with open(md_path, 'r') as f:
        content = f.read()

    # Split into sections
    sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)

    new_sections = []
    for section in sections:
        if not section.strip():
            continue

        lines = section.split('\n')
        header = lines[0]  # ## Keyword Icons
        metadata = lines[1:3]  # Generated: ... and empty line
        table_header = lines[3:6]  # | Icon | Name | Type | etc.

        # Find the table rows
        table_rows = []
        summary_start = -1
        for i, line in enumerate(lines[6:], start=6):
            if line.startswith('### Summary'):
                summary_start = i
                break
            if line.startswith('| <a href='):
                table_rows.append(line)

        if summary_start == -1:
            new_sections.append(section)
            continue

        # Filter rows where file exists
        filtered_rows = []
        for row in table_rows:
            # Extract file path from href
            match = re.search(r'href="([^"]*)"', row)
            if match:
                rel_path = match.group(1)
                # Remove ../ to get relative to root
                if rel_path.startswith('../'):
                    rel_path = rel_path[3:]
                full_path = Path(__file__).parent / rel_path
                if full_path.exists():
                    filtered_rows.append(row)
                else:
                    print(f"Removing missing file: {full_path}")

        # Update summary
        total_icons = len(filtered_rows)
        png_count = sum(1 for row in filtered_rows if 'PNG' in row)

        summary_lines = lines[summary_start:]
        new_summary = []
        for line in summary_lines:
            if '- Total icons:' in line:
                new_summary.append(f"- Total icons: {total_icons}")
            elif '- PNG downloaded:' in line:
                new_summary.append(f"- PNG downloaded: {png_count}")
            else:
                new_summary.append(line)

        # Rebuild section
        new_section = '\n'.join([header] + metadata + table_header + filtered_rows + [''] + new_summary)
        new_sections.append(new_section)

    # Write back
    new_content = '\n'.join(new_sections).strip()
    with open(md_path, 'w') as f:
        f.write(new_content)

    print("Cleanup complete. icons.md updated.")

if __name__ == '__main__':
    cleanup_icons_md()