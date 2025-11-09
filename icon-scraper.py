import asyncio
import argparse
import os
import re
from datetime import datetime

from playwright.async_api import async_playwright
import requests
from PIL import Image


class CorrectedFlaticonScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.download_dir = os.path.join(os.path.dirname(__file__), 'downloads')
        self.icon_dir = None
        self.libs_dir = os.path.join(os.path.dirname(__file__), 'libs')

    async def initialize(self):
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.icon_dir, exist_ok=True)
        os.makedirs(self.libs_dir, exist_ok=True)

        print('🚀 Flaticon Icon Scraper - CORRECTED VERSION\n')
        print('📍 Now capturing REAL direct download URLs!\n')

        self.playwright = await async_playwright().start()
        headless = os.getenv('PLAYWRIGHT_HEADLESS', 'false').lower() == 'true'
        self.browser = await self.playwright.chromium.launch(headless=headless, slow_mo=100)
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})

        print('✓ Browser initialized\n')

    async def search_icons(self, keyword):
        search_url = f"https://www.flaticon.com/search?word={keyword}"
        print(f'🔍 Searching for: "{keyword}"\n')

        try:
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=120000)
            await self.page.wait_for_timeout(5000)
            
            # Check if we have any free-icon links
            icon_count = await self.page.locator('a[href*="free-icon"]').count()
            if icon_count == 0:
                print('❌ No free icons found for this keyword!\n')
                return False
            
            await self.page.wait_for_selector('a[href*="free-icon"]', timeout=30000)
            print('✓ Search results loaded\n')
            return True
        except Exception as e:
            print(f'❌ Search failed: {str(e)}\n')
            return False

    async def extract_icon_data(self, max_icons=10):
        print(f'📊 Extracting icon information (max: {max_icons})...\n')

        icons = await self.page.evaluate(f'''
() => {{
    const iconLinks = document.querySelectorAll('a[href*="free-icon"]');
    const iconData = [];
    for (let i = 0; i < Math.min(iconLinks.length, {max_icons}); i++) {{
        const link = iconLinks[i];
        const img = link.querySelector('img');
        if (link && img) {{
            iconData.push({{
                title: img.alt || 'Untitled',
                url: link.href,
                thumbnailUrl: img.src,
                index: i + 1
            }});
        }}
    }}
    return iconData;
}}
''')

        print(f'✓ Found {len(icons)} icons\n')
        return icons

    async def get_direct_download_urls(self, icon_url, icon_title):
        print(f'  📍 Fetching download URLs for: {icon_title}')

        try:
            await self.page.goto(icon_url, wait_until='domcontentloaded', timeout=60000)
            await self.page.wait_for_timeout(2000)

            download_data = await self.page.evaluate(r'''
() => {
    const data = {
        png: null,
        sizes: {}
    };
    const mainImages = Array.from(document.querySelectorAll('img'))
        .filter(img => img.src && img.src.includes('cdn-icons-png.flaticon.com'));
    if (mainImages.length > 0) {
        const pngUrl = mainImages[0].src;
        data.png = pngUrl;
        const match = pngUrl.match(/flaticon\.com\/(\d+)\//);
        if (match) {
            data.sizes.current = match[1];
        }
    }
    return data;
}
''')

            print(f'    ✓ PNG: {"✓ DIRECT URL" if download_data["png"] else "❌ Not found"}')
            if download_data["png"]:
                print(f'    └─ PNG URL: {download_data["png"][:80]}...')

            return download_data

        except Exception as e:
            print(f'    ✗ Error: {str(e)}')
            return {"png": None}

    def download_file(self, url, file_path):
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            f.write(response.content)

    async def download_icon(self, icon, index):
        downloads = []

        if icon.get('downloadLinks', {}).get('png'):
            png_file_name = f"{index + 1}_{re.sub(r'[^a-zA-Z0-9]', '_', icon['title'])}.png"
            png_path = os.path.join(self.icon_dir, png_file_name)

            try:
                self.download_file(icon['downloadLinks']['png'], png_path)
                # Resize to 128x128 to save disk space
                img = Image.open(png_path)
                img = img.resize((128, 128), Image.Resampling.LANCZOS)
                img.save(png_path)
                downloads.append(f"PNG: {png_file_name}")
                print(f'    ✓ PNG downloaded and resized: {png_file_name}')
            except Exception as e:
                print(f'    ✗ PNG failed: {str(e)}')

        return downloads

    async def scrape_and_download(self, keyword, max_icons=10):
        print(f"{'─'*70}")
        print(f'🎯 STARTING SCRAPE FOR: {keyword.upper()}')
        print(f"{'─'*70}\n")
        
        self.icon_dir = os.path.join(self.download_dir, 'icon', keyword)
        
        try:
            await self.initialize()
            search_success = await self.search_icons(keyword)
            
            if not search_success:
                print(f"{'─'*70}")
                print(f'⏭️  SKIPPING: {keyword} (no icons found)')
                print(f"{'─'*70}\n")
                return False
            
            icons = await self.extract_icon_data(max_icons)

            if not icons:
                print(f"{'─'*70}")
                print(f'⏭️  SKIPPING: {keyword} (no icons extracted)')
                print(f"{'─'*70}\n")
                return False

            # Only create directories if we have icons
            os.makedirs(self.icon_dir, exist_ok=True)

            print(f"{'─'*70}")
            print('\n🔗 Fetching REAL download URLs...\n')
            print(f"{'─'*70}\n")

            for i, icon in enumerate(icons):
                print(f'[{i + 1}/{len(icons)}] Processing...')
                download_data = await self.get_direct_download_urls(icon['url'], icon['title'])
                icon['downloadLinks'] = download_data
                downloaded_files = await self.download_icon(icon, i)
                icon['downloadedFiles'] = downloaded_files
                await self.page.wait_for_timeout(800)

            print(f"\n{'─'*70}")

            markdown_content = self.generate_markdown(keyword, icons)
            self.update_markdown_file(keyword, markdown_content)
            
            print(f'✓ Markdown log updated: libs/icons.md\n')

            print(f"{'─'*70}")
            print('\n✅ SCRAPING COMPLETE!\n')
            print(f'📁 Icons downloaded to: {self.icon_dir}\n')
            print('Summary:')
            print(f'  • Total icons: {len(icons)}')
            png_count = sum(1 for i in icons if i.get('downloadedFiles') and any('PNG' in f for f in i['downloadedFiles']))
            print(f'  • PNG downloaded: {png_count}')
            print(f'\n📋 Check libs/icons.md for download log\n')
            print(f"{'─'*70}\n")
            
            return True

        except Exception as e:
            print(f'❌ Error scraping {keyword}: {str(e)}')
            return False

    def generate_markdown(self, keyword, icons):
        markdown = f"## {keyword.capitalize()} Icons\n\n"
        markdown += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown += "### Downloaded Icons\n\n"
        markdown += "Below are the downloaded icons. Click a thumbnail to open the full-size image.\n\n"
        markdown += "| Icon | Name | Type |\n"
        markdown += "| ----:| ----- | ---- |\n"

        for icon in icons:
            if icon.get('downloadedFiles'):
                for file in icon['downloadedFiles']:
                    format_, filename = file.split(': ')
                    filename = filename.strip()
                    saved_path = f"https://raw.githubusercontent.com/tunghauvan/icon-lib/refs/heads/master/downloads/icon/{keyword}/{filename}"
                    file_type = format_.strip().upper()
                    markdown += f"| <a href=\"{saved_path}\"><img src=\"{saved_path}\" alt=\"{icon['title']}\" width=\"32\" height=\"32\"></a> | {filename} | {file_type} |\n"

        markdown += "### Summary\n\n"
        markdown += f"- Total icons: {len(icons)}\n"
        png_count = sum(1 for i in icons if i.get('downloadedFiles') and any('PNG' in f for f in i['downloadedFiles']))
        markdown += f"- PNG downloaded: {png_count}\n\n"
        markdown += "---\n\n"

        return markdown

    def update_markdown_file(self, keyword, content):
        md_path = os.path.join(self.libs_dir, 'icons.md')
        
        # If file doesn't exist, create with header
        if not os.path.exists(md_path):
            with open(md_path, 'w') as f:
                f.write("# All Icons\n\n")
                f.write(content)
            return
        
        # Read current content
        with open(md_path, 'r') as f:
            current_content = f.read()
        
        section_header = f"## {keyword.capitalize()} Icons\n\n"
        section_end = "\n---\n\n"
        
        # Find the start of the section
        start_idx = current_content.find(section_header)
        if start_idx != -1:
            # Find the end of the section (next --- or end)
            end_idx = current_content.find(section_end, start_idx)
            if end_idx == -1:
                end_idx = len(current_content)
            else:
                end_idx += len(section_end)
            
            # Replace the section
            new_content = current_content[:start_idx] + content + current_content[end_idx:]
        else:
            # Append new section
            if not current_content.endswith('\n'):
                current_content += '\n'
            new_content = current_content + content
        
        # Write back
        with open(md_path, 'w') as f:
            f.write(new_content)

    async def close(self):
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            print('🔒 Browser closed\n')


async def main():
    parser = argparse.ArgumentParser(description='Flaticon Icon Scraper')
    parser.add_argument('keyword', help='Search keyword for icons')
    parser.add_argument('--max-icons', type=int, default=10, help='Maximum number of icons to download')
    args = parser.parse_args()

    scraper = CorrectedFlaticonScraper()
    try:
        await scraper.scrape_and_download(args.keyword, args.max_icons)
    except Exception as e:
        print(f'Fatal error: {str(e)}')
    finally:
        await scraper.close()


if __name__ == '__main__':
    asyncio.run(main())