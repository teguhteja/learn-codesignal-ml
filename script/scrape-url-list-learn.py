"""Web scraper for CodeSignal course structure.

This script fetches and parses course information from a CodeSignal URL using Playwright.
"""

import argparse
import json
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def _iter_next_f_payloads(html_content):
    """Yield the unescaped string payloads pushed via Next.js's self.__next_f.push(...)."""
    pattern = re.compile(r'self\.__next_f\.push\(\[\d+,\s*"((?:[^"\\]|\\.)*)"\]\)')
    for raw in pattern.findall(html_content):
        try:
            yield json.loads('"' + raw + '"')
        except (json.JSONDecodeError, ValueError):
            continue


def _extract_json_array_after_key(text, key):
    """Return the balanced `[...]` substring following `"key":` in text, string-aware."""
    marker = f'"{key}":['
    idx = text.find(marker)
    if idx == -1:
        return None

    start = idx + len(marker) - 1  # position of the opening '['
    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None


def extract_course_units(html_content):
    """Extract the course's unit/practice list from the embedded Next.js RSC JSON payload.

    CodeSignal course pages embed the full course structure as JSON inside
    `self.__next_f.push([...])` script tags. This is far more robust than scraping
    the rendered accordion DOM, whose CSS classes/attributes change over time.
    """
    for payload in _iter_next_f_payloads(html_content):
        if '"units":[' not in payload:
            continue
        array_text = _extract_json_array_after_key(payload, "units")
        if not array_text:
            continue
        try:
            units = json.loads(array_text)
        except json.JSONDecodeError:
            continue
        if units:
            return units
    return None


def units_json_to_lines(units):
    """Convert the parsed units JSON into the same flat line format the DOM parser produces."""
    lines = []
    for unit in sorted(units, key=lambda u: u.get("position", 0)):
        lines.append(f"Unit {unit.get('position')}")

        practices = unit.get("practices") or []
        lines.append(f"{len(practices)} practices")

        minutes = unit.get("minutesToComplete")
        if minutes is not None:
            lines.append(f"{minutes} min")

        title = unit.get("title")
        if title:
            lines.append(title)

        for practice in sorted(practices, key=lambda p: p.get("position", 0)):
            practice_title = practice.get("title")
            if practice_title:
                lines.append(practice_title)

    return lines


def parse_course_from_dom(html_content):
    """Fallback: parse course structure from the rendered accordion DOM."""
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
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_selector("h1", timeout=30000)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_timeout(1500)

        html_content = page.content()

        units = extract_course_units(html_content)
        if units:
            browser.close()
            return units_json_to_lines(units)

        # Fall back to expanding accordions and scraping the rendered DOM.
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

    return parse_course_from_dom(html_content)


def main():
    try:
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

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
