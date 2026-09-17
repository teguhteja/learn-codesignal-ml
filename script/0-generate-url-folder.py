"""End-to-end CodeSignal learning path scraper: URL in, notebooks out.

Given a CodeSignal learning path URL, this orchestrates the three-step manual
workflow (documented in script/info.log) into a single command:

1. Scrape the path page -> create one folder per course, each with a
   placeholder 0.txt (course title/lessons/practices/URL), reusing
   scrape-path-url-folder.py.
2. For each course, scrape its unit/lesson/practice list and overwrite that
   course's 0.txt with it, reusing scrape-url-list-learn.py.
3. Generate one .ipynb per lesson from each course's 0.txt, reusing
   generate-ipynb.py.

Usage:
    python script/0-generate-url-folder.py "https://codesignal.com/learn/paths/..." -o .
"""

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_sibling_module(filename, module_name):
    """Load one of the other hyphenated scripts in this folder as a module."""
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_path(path_url, output_folder):
    scrape_path = _load_sibling_module("scrape-path-url-folder.py", "_scrape_path_url_folder")
    scrape_course = _load_sibling_module("scrape-url-list-learn.py", "_scrape_url_list_learn")
    generate_ipynb = _load_sibling_module("generate-ipynb.py", "_generate_ipynb")

    print(f"Scraping path: {path_url}")
    path_data = scrape_path.scrape_path_page(path_url)
    print(f"Path: {path_data['path_title']}")
    print(f"Courses found: {len(path_data['courses'])}")

    result_folder = scrape_path.create_course_structure(output_folder, path_data)
    print(f"\nStructure created in: {result_folder}")

    for course in path_data["courses"]:
        course_folder = result_folder / course["folder"]
        txt_path = course_folder / "0.txt"

        print(f"\n=== Course {course['course_num']}: {course['title']} ===")
        print(f"Scraping units: {course['url']}")
        lines = scrape_course.scrape_course(course["url"])
        if not lines:
            print(f"  WARNING: no unit content found for {course['url']}, skipping notebook generation for this course.")
            continue

        with open(txt_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(f"{line}\n")
        print(f"  Wrote {len(lines)} lines to {txt_path}")

        generate_ipynb.generate_notebooks(str(txt_path))

    print("\nDone.")
    return result_folder


def main():
    try:
        parser = argparse.ArgumentParser(
            prog="0-generate-url-folder.py",
            description=(
                "Scrape a CodeSignal learning path end-to-end: create course folders, "
                "scrape each course's unit/lesson list into 0.txt, then generate the "
                ".ipynb notebooks for every lesson."
            ),
        )
        parser.add_argument(
            "path_url",
            help="Path URL, e.g. https://codesignal.com/learn/paths/cpp-programming-for-beginners",
        )
        parser.add_argument(
            "-o",
            "--output",
            dest="output_folder",
            default=".",
            help="Output folder where the path directory will be created (default: current directory).",
        )

        args = parser.parse_args()
        generate_path(args.path_url, args.output_folder)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
