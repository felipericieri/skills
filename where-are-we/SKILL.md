---
name: where-are-we
description: Bird's-eye view of any project to pick up where the last chat left off: what is done, in flight, planned and blocked, plus a few suggested next steps. Use at the start of a chat, or when the user asks "where are we", "what's next", "what's left" or "catch me up". Works in any repo. Read-only.
---

# Where are we?

Give the user a one-screen picture of the project they are in and two or three candidates for what to do next. This skill changes nothing: no commits, no task status changes, no branches, no files.

## 1. Gather the facts

Run the bundled script from inside the repo. It detects what the project has (git, `gh` PRs and issues, Task Master tags, checklists such as `TODO.md`, `ROADMAP.md` and `docs/**/checklist*.md`, decision records, the changelog's Unreleased section) and skips the rest. It reads files directly, so it works even when MCP servers are down.

```bash
python3 ~/.claude/skills/where-are-we/status.py
```

If it prints little, the project keeps its plan elsewhere (an issue tracker, a notes file, a README section). Look for it in the files listed under "guidance and planning files found" before saying there is no plan.

## 2. Read the project's own rules for what blocks work

Numbers come from the script. The reasons things are blocked or off limits come from the project's guidance, so read what exists: `CLAUDE.md`, `AGENTS.md`, and the memory index already in your context (`MEMORY.md`). Look for:

- gates (an ADR or decision that must exist before something is built),
- things the user deferred or told you not to decide (vendors, scope),
- the working agreement (branching, who merges), which governs how a chosen next step starts,
- tags or sections the docs call stale; leave those out of the report.

Never treat a "ready" task as settled just because its dependencies are met. Open a task's details only for the two or three candidates you are about to suggest.

## 3. Report

Keep it to one screen, in this shape:

**Done**: finished areas, one line.
**In flight**: in-progress tasks, open PRs, unmerged branches, uncommitted changes, stashes.
**Planned**: remaining areas as `done/total` with a few words on what each is and whether it is blocked (and by what).
**Unreleased**: what is merged since the last tag, and any release checklist items still open.
**Next, my suggestion**: two or three options, best first. For each: the task or issue, why now (what it unblocks), what it touches, roughly how big. Say which one you would pick and why. End by asking which to take.

If the user picks one, start it the way the project's working agreement says (usually a new branch from the integration branch, and the task marked in progress).

## Optional

If the user asks for a page they can share, publish the same content as a private Artifact. Do not do so unasked.
