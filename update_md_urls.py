import re
from pathlib import Path

def update_md_urls():
    md_path = Path(__file__).parent / 'libs' / 'icons.md'

    if not md_path.exists():
        print("icons.md not found.")
        return

    with open(md_path, 'r') as f:
        content = f.read()

    # Replace relative paths with GitHub raw URLs
    # Pattern: href="../downloads/icon/keyword/filename" -> href="https://raw.githubusercontent.com/tunghauvan/icon-lib/refs/heads/master/downloads/icon/keyword/filename"
    # Same for src

    updated_content = re.sub(
        r'href="\.\./downloads/icon/([^"]*)"',
        r'href="https://raw.githubusercontent.com/tunghauvan/icon-lib/refs/heads/master/downloads/icon/\1"',
        content
    )

    updated_content = re.sub(
        r'src="\.\./downloads/icon/([^"]*)"',
        r'src="https://raw.githubusercontent.com/tunghauvan/icon-lib/refs/heads/master/downloads/icon/\1"',
        updated_content
    )

    with open(md_path, 'w') as f:
        f.write(updated_content)

    print("icons.md URLs updated to public GitHub links.")

if __name__ == '__main__':
    update_md_urls()