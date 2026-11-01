#!/usr/bin/env python3
"""Read-only project status for any repo: git, open PRs and issues, Task Master
tags, checklists and ADRs. Detects what exists and skips the rest. Changes nothing.

Used by the `where-are-we` skill. Run it from anywhere inside a repo.
"""
import json
import re
import subprocess
from pathlib import Path


def run(*cmd, cwd=None):
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


ROOT = Path(run("git", "rev-parse", "--show-toplevel") or ".").resolve()


def git(*args):
    return run("git", *args, cwd=ROOT)


def header():
    print(f"# {ROOT.name}  ({ROOT})")
    docs = [n for n in ("CLAUDE.md", "AGENTS.md", "README.md", "ROADMAP.md", "TODO.md", "CHANGELOG.md") if (ROOT / n).exists()]
    print(f"- guidance and planning files found: {', '.join(docs) or 'none'}")


def git_section():
    if not git("rev-parse", "--git-dir"):
        print("\n## Git\n- not a git repository")
        return
    print("\n## Git")
    branch = git("branch", "--show-current") or "(detached)"
    print(f"- branch: {branch}")
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream:
        ahead_behind = git("rev-list", "--left-right", "--count", f"HEAD...{upstream}").split()
        if len(ahead_behind) == 2:
            print(f"- vs {upstream}: {ahead_behind[0]} ahead, {ahead_behind[1]} behind")
    else:
        print("- no upstream (branch not pushed)")
    dirty = git("status", "--porcelain").splitlines()
    print(f"- working tree: {f'{len(dirty)} changed file(s)' if dirty else 'clean'}")
    stash = git("stash", "list").splitlines()
    if stash:
        print(f"- stashes: {len(stash)}")
    tag = git("describe", "--tags", "--abbrev=0")
    if tag:
        tag_date = git("log", "-1", "--format=%cI", tag)
        since = git("rev-list", "--count", "HEAD", f"--since={tag_date}") if tag_date else "?"
        print(f"- last tag: {tag} (about {since} commit(s) on this branch since it was tagged)")
    branches = [b for b in git("branch", "--format=%(refname:short)").splitlines() if b not in {"main", "master", "develop", branch}]
    if branches:
        print(f"- other local branches ({len(branches)}): {', '.join(branches[:12])}{' ...' if len(branches) > 12 else ''}")
    recent = git("log", "-8", "--format=%h %ad %s", "--date=short")
    print("- recent commits:")
    for line in recent.splitlines():
        print(f"  - {line}")


def github_section():
    if not run("gh", "--version"):
        return
    prs = run("gh", "pr", "list", "--state", "open", "--limit", "15", "--json", "number,title,headRefName,baseRefName,isDraft",
              "--template", "{{range .}}#{{.number}} {{.title}} ({{.headRefName}} -> {{.baseRefName}}){{if .isDraft}} [draft]{{end}}\n{{end}}", cwd=ROOT)
    issues = run("gh", "issue", "list", "--state", "open", "--limit", "10", "--json", "number,title",
                 "--template", "{{range .}}#{{.number}} {{.title}}\n{{end}}", cwd=ROOT)
    if not prs and not issues:
        print("\n## GitHub\n- no open PRs or issues (or gh is not set up for this repo)")
        return
    print("\n## GitHub")
    for label, text in (("open PRs", prs), ("open issues (first 10)", issues)):
        print(f"- {label}:" + ("" if text else " none"))
        for line in text.splitlines():
            print(f"  - {line}")


def taskmaster_section():
    path = ROOT / ".taskmaster/tasks/tasks.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text())
    except ValueError:
        print("\n## Task Master\n- tasks.json is not valid JSON")
        return
    if "tasks" in data:  # untagged format
        data = {"(no tag)": data}
    print("\n## Task Master (tag: done/total, other statuses). Tags the project docs call stale should be ignored.")
    ready, deferred = [], []
    for tag, body in data.items():
        if not isinstance(body, dict) or "tasks" not in body:
            continue
        tasks = body["tasks"]
        counts = {}
        for t in tasks:
            counts[t.get("status", "?")] = counts.get(t.get("status", "?"), 0) + 1
        done = counts.get("done", 0)
        others = ", ".join(f"{s} {n}" for s, n in sorted(counts.items()) if s != "done")
        complete = done + counts.get("cancelled", 0) == len(tasks)
        print(f"- {tag}: {done}/{len(tasks)}{' COMPLETE' if complete else ''}{f' ({others})' if others else ''}")
        finished = {t["id"] for t in tasks if t.get("status") in {"done", "cancelled"}}
        taken = 0
        for t in tasks:
            st = t.get("status")
            if st == "in-progress":
                ready.append(f"[IN PROGRESS] {tag}/{t['id']}: {t['title']}")
            elif st == "pending" and taken < 3 and not [d for d in t.get("dependencies", []) if d not in finished]:
                ready.append(f"[READY] {tag}/{t['id']}: {t['title']}")
                taken += 1
            elif st == "deferred":
                deferred.append(f"{tag}/{t['id']}: {t['title']}")
    print("\n### In progress, and ready to start (dependencies met; first 3 per tag)")
    for r in ready:
        print(f"- {r}")
    if deferred:
        print(f"\n### Deferred ({len(deferred)})")
        for d in deferred:
            print(f"- {d}")


def checklist_section():
    candidates = [p for pat in ("TODO.md", "ROADMAP.md", "docs/**/checklist*.md", "docs/**/*roadmap*.md", "docs/**/todo*.md")
                  for p in ROOT.glob(pat)]
    seen = []
    for p in candidates:
        if p in seen or "node_modules" in p.parts:
            continue
        seen.append(p)
        section, counts = "(top)", {}
        for line in p.read_text(errors="ignore").splitlines():
            m = re.match(r"#{1,3} (.+)", line)
            if m:
                section = m.group(1)
            elif re.match(r"\s*- \[ \]", line):
                counts.setdefault(section, [0, 0])[0] += 1
                counts[section][1] += 1
            elif re.match(r"\s*- \[[xX]\]", line):
                counts.setdefault(section, [0, 0])[1] += 1
        if counts:
            print(f"\n## {p.relative_to(ROOT)} (open of total per section)")
            for s, (o, t) in counts.items():
                print(f"- {s}: {o} open of {t}")


def adr_section():
    for d in ("docs/adr", "docs/decisions", "adr", "docs/architecture/decisions"):
        files = sorted((ROOT / d).glob("0*.md")) if (ROOT / d).is_dir() else []
        if files:
            print(f"\n## Decision records: {len(files)} in {d}/, latest: {files[-1].stem}")
            return


def changelog_section():
    p = ROOT / "CHANGELOG.md"
    if not p.exists():
        return
    text = p.read_text(errors="ignore")
    m = re.search(r"## \[?Unreleased\]?.*?\n(.*?)(?=\n## |\Z)", text, re.S | re.I)
    if m and m.group(1).strip():
        print(f"\n## CHANGELOG Unreleased: {len([l for l in m.group(1).splitlines() if l.strip().startswith('-')])} entries")


if __name__ == "__main__":
    header()
    git_section()
    github_section()
    taskmaster_section()
    checklist_section()
    adr_section()
    changelog_section()
