"""Web scraper for CodeSignal course structure.

This script fetches and parses course information from a CodeSignal URL using Playwright.
"""

import argparse
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def parse_course_from_html(html_content):
    """Parse course structure from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    accordions = soup.find_all('div', attrs={'data-headlessui-state': True})

    for accordion in accordions:
        unit_header = accordion.find('div', class_=lambda x: x and 'text-h-2xs' in x)
        if not unit_header:
            continue

        unit_text = unit_header.get_text(strip=True)
        unit_text = re.sub(r'<!--.*?-->', '', unit_text).strip()

        unit_match = re.search(r'Unit\s*(\d+)', unit_text, re.IGNORECASE)
        if unit_match:
            results.append(f"Unit {unit_match.group(1)}")

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

            practice_names = accordion.find_all('div', class_=lambda x: x and 'text-theme-strong' in x and 'text-xs' in x)
            for name_div in practice_names:
                name_text = name_div.get_text(strip=True)
                if name_text and 'Unit' not in name_text and len(name_text) > 5:
                    results.append(name_text)

    return results


def scrape_course(url):
    """Scrape course structure from URL using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Loading: {url}")
        page.goto(url, wait_until='networkidle', timeout=60000)

        # Expand all collapsed accordions
        page.wait_for_timeout(1000)
        accordions = page.query_selector_all('[data-headlessui-state]')
        print(f"Found {len(accordions)} accordion elements")
        for accordion in accordions:
            state = accordion.get_attribute('data-headlessui-state')
            if not state or 'open' not in state:
                try:
                    accordion.click()
                    page.wait_for_timeout(300)
                except Exception:
                    pass

        page.wait_for_timeout(500)
        html_content = page.content()
        browser.close()

    return parse_course_from_html(html_content)


def main():
    parser = argparse.ArgumentParser(
        prog="scrape-url-list-learn.py",
        description="Scrape a CodeSignal course page and save the unit/lesson list into a text file.",
        epilog=(
            "Example:\n"
            "  python scrape-url-list-learn.py "
            "\"course/0.txt\" "
            "\"https://codesignal.com/learn/courses/exploring-workflows-with-claude\""
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "output_file",
        help="Path to the output text file, e.g. course/0.txt",
    )
    parser.add_argument(
        "course_url",
        help="CodeSignal course URL to scrape",
    )

    args = parser.parse_args()

    output_file = args.output_file
    url = args.course_url

    content = scrape_course(url)

    if not content:
        print("No course content found. The page structure may have changed.")
        sys.exit(1)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in content:
            f.write(f"{line}\n")

    print(f"Output saved to: {output_path}")
    print(f"Total lines: {len(content)}")


if __name__ == "__main__":
    main()
