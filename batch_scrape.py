import asyncio
import re
from icon_scraper import CorrectedFlaticonScraper

async def main():
    # Read keywords.md
    with open('keywords.md', 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.startswith('- [ ] '):
            keyword = line[6:].strip()
            print(f"Processing keyword: {keyword}")
            
            scraper = CorrectedFlaticonScraper()
            try:
                success = await scraper.scrape_and_download(keyword)
                if success:
                    lines[i] = f'- [x] {keyword}'
                    # Write back the updated content
                    with open('keywords.md', 'w') as f:
                        f.write('\n'.join(lines))
                    print(f"Marked {keyword} as done")
                else:
                    print(f"Skipped {keyword} (no icons or failed)")
            except Exception as e:
                print(f"Error processing {keyword}: {e}")
            finally:
                await scraper.close()

if __name__ == '__main__':
    asyncio.run(main())