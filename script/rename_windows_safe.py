#!/usr/bin/env python3
"""
Rename files and folders to be safe on Windows file systems.

Unsafe characters replaced:  : < > | " * ? \\ /  (in basename only)
Trailing spaces/dots removed.
Windows reserved names (CON, NUL, COM1...) get a _ suffix.

Usage:
    python rename_windows_safe.py [--execute] <dir> [<dir> ...]

    --execute   Actually rename. Default is dry-run (shows what would change).
"""

import os
import re
import sys
import argparse
from pathlib import Path

# Windows reserved filenames (case-insensitive, with or without extension)
RESERVED = re.compile(
    r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..+)?$',
    re.IGNORECASE,
)

# Characters forbidden in Windows path components
# \ / are path separators on Windows — skip replacing / since it can't appear
# in Linux filenames either; only handle the rest.
REPLACEMENTS = [
    (': ',  ' - '),   # "Lesson 1: Intro"       → "Lesson 1 - Intro"
    (':-',  ' - '),   # "Name:-Sub"              → "Name - Sub"
    ('-:',  ' - '),   # "Name-:Sub"              → "Name - Sub"
    (':',   ' - '),   # remaining bare colons
    ('<',   '('),
    ('>',   ')'),
    ('|',   '-'),
    ('"',   "'"),
    ('*',   '_'),
    ('?',   '_'),
    ('\\',  '-'),
]


def make_safe(name: str) -> str:
    result = name
    for bad, good in REPLACEMENTS:
        result = result.replace(bad, good)

    # Collapse multiple spaces/dashes that replacements can create
    result = re.sub(r'  +', ' ', result)
    result = re.sub(r'--+', '-', result)
    result = result.strip()

    # Windows forbids names ending with space or dot
    result = result.rstrip('. ')

    # Handle reserved names
    if RESERVED.match(result):
        stem, *ext = result.rsplit('.', 1)
        result = stem + '_' + ('.' + ext[0] if ext else '')

    return result


def collect_renames(root: str) -> list[tuple[Path, Path]]:
    """Walk bottom-up and collect (old_path, new_path) pairs that need renaming."""
    renames = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        entries = [(f, False) for f in filenames] + [(d, True) for d in dirnames]
        for name, is_dir in entries:
            safe = make_safe(name)
            if safe == name:
                continue
            old = Path(dirpath) / name
            new = Path(dirpath) / safe
            renames.append((old, new))
    return renames


def run(dirs: list[str], execute: bool) -> None:
    all_renames: list[tuple[Path, Path]] = []
    for d in dirs:
        if not os.path.isdir(d):
            print(f"[skip] not a directory: {d}")
            continue
        all_renames.extend(collect_renames(d))

    if not all_renames:
        print("Nothing to rename — all names are already Windows-safe.")
        return

    mode = "EXECUTE" if execute else "DRY-RUN"
    print(f"[{mode}] {len(all_renames)} rename(s) found:\n")

    conflicts = 0
    done = 0
    skipped = 0

    for old, new in all_renames:
        rel_old = old.relative_to(Path(dirs[0]).parent) if len(dirs) == 1 else old
        print(f"  {old.name!r}")
        print(f"  → {new.name!r}")
        print(f"     ({old.parent})")

        if execute:
            if new.exists() and new != old:
                print(f"  [CONFLICT] target already exists, skipping\n")
                conflicts += 1
                continue
            try:
                old.rename(new)
                done += 1
                print(f"  [OK]\n")
            except OSError as e:
                print(f"  [ERROR] {e}\n")
                skipped += 1
        else:
            print()

    if execute:
        print(f"\nDone: {done} renamed, {skipped} errors, {conflicts} conflicts skipped.")
    else:
        print(f"\nDry-run complete. Run with --execute to apply {len(all_renames)} rename(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--execute', action='store_true', help='Apply renames (default: dry-run)')
    parser.add_argument('dirs', nargs='+', help='Directories to process')
    args = parser.parse_args()
    run(args.dirs, args.execute)


if __name__ == '__main__':
    main()
