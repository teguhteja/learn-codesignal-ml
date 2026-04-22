import os
import re
import sys


def slugify(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^A-Za-z0-9]+", "-", text)  # spaces/symbols -> hyphen
    return text.strip("-")


def create_folder_with_file(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    number = 1
    for i, line in enumerate(lines):
        # Detect "Course 1", "Course 2", etc.
        if re.match(r"^Course\s+\d+$", line) and i + 1 < len(lines):
            title = lines[i + 1]
            folder_name = f"{number}.{slugify(title)}"
            os.makedirs(folder_name, exist_ok=True)
            print(f"Folder '{folder_name}' created successfully.")
            number += 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_folder.py <file_name>")
    else:
        file_name = sys.argv[1]
        create_folder_with_file(file_name)