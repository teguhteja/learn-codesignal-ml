"""Web scraper for CodeSignal course structure.

This script parses course information from a local HTML file.

Usage:
    python codesignal_scraper.py --local output.md output.txt
"""

import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup


def parse_local_html(html_path):
    """Parse course structure from local HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Find the course title
    title = soup.find('div', class_=re.compile(r'text-h-2xl'))
    if title:
        results.append(title.get_text(strip=True))
    
    # Parse the structure more carefully using BeautifulSoup
    accordions = soup.find_all('div', attrs={'data-headlessui-state': True})
    
    for accordion in accordions:
        # Find unit header within this accordion - skip if None
        unit_header = accordion.find('div', class_=lambda x: x and 'text-h-2xs' in x)
        if not unit_header:
            continue
            
        unit_text = unit_header.get_text(strip=True)
        # Clean up HTML comments
        unit_text = re.sub(r'<!--.*?-->', '', unit_text).strip()
        
        # Extract unit number
        unit_match = re.search(r'Unit\s*(\d+)', unit_text, re.IGNORECASE)
        if unit_match:
            results.append(f"Unit {unit_match.group(1)}")
            
            # Find practice count - look for text-2xs class divs
            practice_divs = accordion.find_all('div', class_=lambda x: x and 'text-2xs' in x)
            for div in practice_divs:
                text = div.get_text(strip=True)
                if text and 'practices' in text.lower():
                    # Extract the number
                    num_match = re.search(r'(\d+)\s*practices?', text, re.IGNORECASE)
                    if num_match:
                        results.append(f"{num_match.group(1)} practices")
                        break
            
            # Find time - look for divs with min
            for div in practice_divs:
                text = div.get_text(strip=True)
                if text and 'min' in text.lower():
                    # Extract the number
                    num_match = re.search(r'(\d+)\s*min', text, re.IGNORECASE)
                    if num_match:
                        results.append(f"{num_match.group(1)} min")
                        break
            
            # Find practice names - look for divs with text-theme-strong text-xs class
            practice_names = accordion.find_all('div', class_=lambda x: x and 'text-theme-strong' in x and 'text-xs' in x)
            for name_div in practice_names:
                name_text = name_div.get_text(strip=True)
                if name_text and 'Unit' not in name_text and len(name_text) > 5:
                    results.append(name_text)
    
    return results


def main():
    if len(sys.argv) < 4 or sys.argv[1] != '--local':
        print("Usage: python codesignal_scraper.py --local <html_file> <output_file>")
        sys.exit(1)
    
    html_file = sys.argv[2]
    output_path = Path(sys.argv[3])
    
    print(f"Parsing local file: {html_file}")
    content = parse_local_html(html_file)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in content:
            f.write(f"{line}\n")
    
    print(f"Output saved to: {output_path}")
    print(f"Total lines: {len(content)}")


if __name__ == "__main__":
    main()