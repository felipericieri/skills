#!/usr/bin/env python3
"""Show docs/release-checklist.md grouped by the iteration that added each item.

Usage: summary.py [--all] [path]
  --all   include items already ticked
  path    checklist file (default: docs/release-checklist.md)
"""
import re
import sys
from pathlib import Path

ITEM = re.compile(r"^- \[( |x|X)\] (.*)$")
ADDED = re.compile(r"_Added:\s*(.*?)\s*·\s*(\d{4}-\d{2}-\d{2})\s*_\s*$")


def parse(text):
    items, category = [], "Uncategorised"
    for line in text.splitlines():
        if line.startswith("## "):
            category = line[3:].strip()
            continue
        m = ITEM.match(line)
        if not m:
            continue
        body = m.group(2)
        a = ADDED.search(body)
        iteration, date = (a.group(1), a.group(2)) if a else ("unknown", "")
        if a:
            body = body[: a.start()].rstrip()
        items.append(
            {"done": m.group(1) != " ", "text": body, "category": category,
             "iteration": iteration, "date": date, "order": len(items)}
        )
    return items


def main(argv):
    show_all = "--all" in argv
    paths = [a for a in argv if not a.startswith("--")]
    path = Path(paths[0] if paths else "docs/release-checklist.md")
    if not path.is_file():
        print(f"No checklist at {path}.")
        return 1

    items = parse(path.read_text())
    open_n = sum(not i["done"] for i in items)
    print(f"{path}: {open_n} open, {len(items) - open_n} done\n")

    shown = [i for i in items if show_all or not i["done"]]
    groups = {}
    for i in shown:
        groups.setdefault((i["date"], i["iteration"]), []).append(i)

    if not groups:
        print("Nothing open.")
        return 0
    for (date, iteration), group in sorted(groups.items(), key=lambda kv: (kv[0][0] or "9999", kv[1][0]["order"])):
        print(f"{iteration}  {date}".rstrip())
        for i in sorted(group, key=lambda i: i["order"]):
            print(f"  [{'x' if i['done'] else ' '}] ({i['category']}) {i['text']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
