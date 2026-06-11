"""Web scraper for CodeSignal course structure.

This script parses course information from a local HTML file.

Usage:
    python codesignal_scraper.py --local output.md <course_url> output.txt

Example:
    python codesignal_scraper.py --local output.md "https://codesignal.com/learn/courses/exploring-workflows-with-claude" output.txt
"""

import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup


def parse_course_from_html(html_path, course_url=None):
    """Parse course structure from local HTML file.

    Args:
        html_path: Path to the HTML file
        course_url: Optional course URL to filter specific course content
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Find all accordions (course detail sections)
    accordions = soup.find_all('div', attrs={'data-headlessui-state': True})

    for accordion in accordions:
        # Check if this accordion is related to the specified course URL
        if course_url:
            # Find links in this accordion
            links = accordion.find_all('a', href=True)
            course_links = [a for a in links if course_url.split('/')[-1] in a.get('href', '')]
            if not course_links:
                continue

        # Find unit header within this accordion
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

            # Find practice count and time from text-2xs class divs
            practice_divs = accordion.find_all('div', class_=lambda x: x and 'text-2xs' in x)

            for div in practice_divs:
                text = div.get_text(strip=True)
                if 'practices' in text.lower():
                    num_match = re.search(r'(\d+)\s*practices?', text, re.IGNORECASE)
                    if num_match:
                        results.append(f"{num_match.group(1)} practices")
                        break

            for div in practice_divs:
                text = div.get_text(strip=True)
                if 'min' in text.lower():
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
        print("Usage: python codesignal_scraper.py --local <html_file> <course_url> <output_file>")
        print("\nExample:")
        print('  python codesignal_scraper.py --local output.md "https://codesignal.com/learn/courses/exploring-workflows-with-claude" output.txt')
        sys.exit(1)

    html_file = sys.argv[2]
    course_url = sys.argv[3] if len(sys.argv) > 4 else None
    output_path = Path(sys.argv[-1])

    print(f"Parsing local file: {html_file}")
    if course_url:
        print(f"Course URL: {course_url}")

    content = parse_course_from_html(html_file, course_url)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in content:
            f.write(f"{line}\n")

    print(f"Output saved to: {output_path}")
    print(f"Total lines: {len(content)}")


if __name__ == "__main__":
    main()