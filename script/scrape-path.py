"""Scrape CodeSignal learning path and generate course folders with notebooks.

This script:
1. Scrapes a CodeSignal learning path page to get course information
2. Creates folders with course names (with sequence number prefix)
3. Generates .ipynb files for each course

Usage:
    python scrape_path.py "https://codesignal.com/learn/paths/..." --output .
"""

import argparse
import sys
import re
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def parse_html_content(html_content):
    """Parse course list from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    courses = []
    
    # Find the path title
    title = soup.find('h1', class_=re.compile(r'text-h-xl|text-h-2xl'))
    if title:
        path_title = title.get_text(strip=True)
    else:
        path_title = "Unknown Path"
    
    # Find all course cards - look for the specific card structure
    course_cards = soup.find_all('div', class_=lambda x: x and 'rounded-8' in x and 'bg-white' in x)
    
    for card in course_cards:
        # Find the course number label
        course_num = ""
        num_label = card.find('div', class_=lambda x: x and 'font-medium' in x and 'text-theme-light' in x and 'text-sm' in x)
        if num_label:
            num_text = num_label.get_text(strip=True)
            match = re.search(r'Course\s*(\d+)', num_text)
            if match:
                course_num = match.group(1)
        
        # Find course title
        course_title = ""
        for div in card.find_all('div', class_=re.compile(r'text-h-sm|text-h-md')):
            text = div.get_text(strip=True)
            if text and len(text) > 10 and 'Course' not in text and 'lessons' not in text.lower():
                course_title = text
                break
        
        if not course_title:
            continue
        
        # Find URL link
        link = card.find('a', href=re.compile(r'/learn/courses/'))
        if not link:
            continue
        
        href = link.get('href', '')
        course_url = f"https://codesignal.com{href}" if href.startswith('/') else href
        
        # Find lessons and practices counts
        lessons_count = "0"
        practices_count = "0"
        
        all_text = card.get_text()
        
        lessons_match = re.search(r'(\d+)\s*lessons?', all_text)
        if lessons_match:
            lessons_count = lessons_match.group(1)
        
        practices_match = re.search(r'(\d+)\s*practices?', all_text)
        if practices_match:
            practices_count = practices_match.group(1)
        
        # Find description
        description = ""
        desc_divs = card.find_all('div', class_=lambda x: x and 'text-theme' in x and 'text-xs' in x)
        for desc in desc_divs:
            text = desc.get_text(strip=True)
            if len(text) > 50:
                description = text
                break
        
        # Create folder name with sequence number and dash-separated
        folder_name = f"{course_num}.{course_title.replace(' ', '-')}"
        folder_name = re.sub(r'[^0-9a-zA-Z\-\.]', '', folder_name)
        
        courses.append({
            'title': course_title,
            'url': course_url,
            'folder': folder_name,
            'course_num': course_num,
            'lessons': lessons_count,
            'practices': practices_count,
            'description': description
        })
    
    return {
        'path_title': path_title,
        'courses': courses
    }


def scrape_path_page(url):
    """Scrape course list from a CodeSignal learning path page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1000)
        html_content = page.content()
        browser.close()

    return parse_html_content(html_content)


def create_course_structure(base_path, path_data):
    """Create folder structure and generate notebooks for each course."""
    base = Path(base_path)
    
    path_folder_name = path_data['path_title'].replace(" ", "-")
    path_folder = base / path_folder_name
    path_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"Path folder: {path_folder}")
    
    for i, course in enumerate(path_data['courses']):
        course_folder = path_folder / course['folder']
        course_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\n  Course {course['course_num']}: {course['title']}")
        print(f"    Folder: {course['folder']}")
        print(f"    URL: {course['url']}")
        print(f"    Lessons: {course['lessons']}, Practices: {course['practices']}")
        
        # Create 0.txt with course info
        info_file = course_folder / "0.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"Course {course['course_num']}\n")
            f.write(f"{course['title']}\n")
            f.write(f"{course['lessons']} lessons\n")
            f.write(f"{course['practices']} practices\n")
            if course['description']:
                f.write(f"\n{course['description']}\n")
            f.write(f"\nURL: {course['url']}\n")
    
    return path_folder


def main():
    try:
        parser = argparse.ArgumentParser(
            prog="scrape-path.py",
            description="Scrape a CodeSignal learning path (or parse a saved HTML file) and create course folders.",
        )
        parser.add_argument(
            "path_url",
            help="Path URL, e.g. https://codesignal.com/learn/paths/building-effective-agents-claude-python",
        )
        parser.add_argument(
            "-o",
            "--output",
            dest="output_folder",
            default=".",
            help="Output folder where the path directory will be created (default: current directory).",
        )

        args = parser.parse_args()

        print(f"Scraping: {args.path_url}")
        path_data = scrape_path_page(args.path_url)
        
        print(f"\nPath: {path_data['path_title']}")
        print(f"Courses found: {len(path_data['courses'])}")
        
        for course in path_data['courses']:
            print(f"\n  Course {course['course_num']}. {course['title']}")
            print(f"     Lessons: {course['lessons']}, Practices: {course['practices']}")
            print(f"     URL: {course['url']}")
        
        result_folder = create_course_structure(args.output_folder, path_data)
        print(f"\nStructure created in: {result_folder}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
