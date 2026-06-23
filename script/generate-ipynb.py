"""Generate Jupyter notebooks from text file structure.

This script converts a text file with course structure into individual .ipynb files.
Each "Unit X" becomes a separate notebook.

Usage:
    python generate-ipynb.py <input_file>
"""

import sys
import json
import re
from pathlib import Path


def sanitize_filename_component(name):
    name = name.strip()
    name = re.sub(r'[<>:"/\\\\|?*]', '-', name)
    name = re.sub(r'[\x00-\x1f]', '-', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.rstrip('. ')

    if not name:
        return "untitled"

    upper = name.upper()
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if upper in reserved:
        return f"_{name}"

    return name


def should_skip_line(line):
    """Check if line should be skipped (contains practices, min, or Preview)."""
    line = line.strip()
    if re.search(r'\d+\s*practices?', line, re.IGNORECASE):
        return True
    if re.search(r'\d+\s*min', line, re.IGNORECASE):
        return True
    if re.search(r'^[Pp]review$', line):
        return True
    return False


def create_notebook(lines):
    """Create notebook JSON structure."""
    return {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    }


def add_markdown_cell(notebook, content, heading_level=None):
    """Add a markdown cell to the notebook."""
    if heading_level:
        content = f"{'#' * heading_level} {content}"
    
    cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [content]
    }
    notebook["cells"].append(cell)


def finish_notebook(current_file, last_line):
    """Finish and save the current notebook."""
    if current_file and last_line:
        # Load existing notebook
        with open(current_file, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Add the last line as a heading
        add_markdown_cell(notebook, last_line, heading_level=2)
        
        # Save the notebook
        with open(current_file, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=4)
        
        print(f"Generated notebook: {current_file}")


def generate_notebooks(input_file):
    """Generate notebooks from input file."""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    
    output_dir = input_path.parent
    current_file = None
    lesson_started = False
    last_line = ""

    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check if the line starts with "Unit"
        if line.startswith("Unit"):
            # Finish the previous notebook if any
            if current_file and last_line:
                finish_notebook(current_file, last_line)
                current_file = None
            
            # Extract unit number
            unit_match = re.search(r'\d+', line)
            if not unit_match:
                continue
            unit_number = unit_match.group()
            
            # Find the next valid line (skip practices, min, preview)
            next_valid_line = ""
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if next_line and not should_skip_line(next_line):
                    next_valid_line = next_line
                    break
            
            # Create filename: Unit number + next valid line
            if next_valid_line:
                safe_name = sanitize_filename_component(next_valid_line).replace(" ", "-")
                filename = f"{unit_number}.{safe_name}.ipynb"
            else:
                filename = f"{unit_number}.ipynb"
            
            current_file = output_dir / filename
            
            # Create new notebook
            notebook = create_notebook(lines)
            
            # Add the lesson name as heading 1
            add_markdown_cell(notebook, line, heading_level=1)
            
            # Save initial notebook
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=4)
            
            lesson_started = True
            last_line = ""
            
        elif should_skip_line(line):
            # Skip this line
            continue
            
        elif not line or line.isspace():
            # Skip empty lines
            continue
            
        elif lesson_started and current_file:
            # Check if this is the actual last content line
            is_last_content_line = True
            for k in range(i + 1, len(lines)):
                next_line = lines[k].strip()
                if next_line and not next_line.startswith("Unit"):
                    is_last_content_line = False
                    break
            
            if is_last_content_line:
                # Store as potential last line
                last_line = line
            else:
                # Add as heading now
                with open(current_file, 'r', encoding='utf-8') as f:
                    notebook = json.load(f)
                
                add_markdown_cell(notebook, line, heading_level=2)
                
                with open(current_file, 'w', encoding='utf-8') as f:
                    json.dump(notebook, f, indent=4)
                
                last_line = line
    
    # Finish the last notebook
    if current_file and last_line:
        finish_notebook(current_file, last_line)


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-ipynb.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    generate_notebooks(input_file)


if __name__ == "__main__":
    main()
