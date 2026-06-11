#!/usr/bin/env python3
import os
import sys

def rename_spaces_to_dashes(directory_path="."):
    """
    Rename files and folders by replacing spaces with dashes

    Args:
        directory_path: Path to directory to process (default: current directory)
    """
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist")
        return

    renamed_count = 0

    # Walk through directory tree (bottom-up to handle nested folders first)
    for root, dirs, files in os.walk(directory_path, topdown=False):
        # Process files first
        for filename in files:
            if ' ' in filename:
                old_path = os.path.join(root, filename)
                new_filename = filename.replace(' ', '-')
                new_path = os.path.join(root, new_filename)

                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed file: '{filename}' -> '{new_filename}'")
                    renamed_count += 1
                except OSError as e:
                    print(f"Error renaming file '{filename}': {e}")

        # Process directories
        for dirname in dirs:
            if ' ' in dirname:
                old_path = os.path.join(root, dirname)
                new_dirname = dirname.replace(' ', '-')
                new_path = os.path.join(root, new_dirname)

                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed folder: '{dirname}' -> '{new_dirname}'")
                    renamed_count += 1
                except OSError as e:
                    print(f"Error renaming folder '{dirname}': {e}")

    print(f"\nTotal items renamed: {renamed_count}")

if __name__ == "__main__":
    # Get directory path from command line argument or use current directory
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"Processing directory: {os.path.abspath(target_dir)}")
    print("Replacing spaces with dashes in file and folder names...\n")

    rename_spaces_to_dashes(target_dir)