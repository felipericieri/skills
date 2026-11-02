---
name: task-claim
description: Use before starting a tracked task (Task Master, issue, ticket) when other chats, subagents or worktrees may work in the same git clone, or when handing tasks to subagents. Claims the task in a lock shared by all worktrees so two agents never take the same one. Also use to list who holds what, or to release a claim.
---

# Task claim lock

A task's status in a tracker file (e.g. Task Master `tasks.json`) is per branch: an "in-progress" mark is invisible to other chats, subagents and worktrees until it merges. This skill adds a machine-local lock that every worktree of the clone sees at once. Claims live in the repo's shared git directory and are never pushed.

The script is `scripts/claim-task.sh` in this skill's directory (call it `CLAIM`). `<scope>` groups ids (a Task Master tag, `gh` for issue numbers); `<id>` is the task id. If the project ships its own copy (e.g. `scripts/claim-task.sh`), use that one.

## Steps

1. **Before picking a task:** `CLAIM list`. Skip anything held.
2. **Before starting one:** `CLAIM claim <scope> <id> --owner <chat-or-agent-name>`. Exit 1 means someone else holds it: pick another, don't override.
3. **When the PR is open or the work is dropped:** `CLAIM release <scope> <id> --owner <same name>`.

## Rules

- Always pass a distinct `--owner`. The holder is owner + branch; two chats on one branch with the default owner look like the same holder and both succeed.
- A claim over 24 hours old shows `STALE`. Never take it over silently: ask the user, then `release --force`.
- Subagents: the brief must say to claim and release, or the parent claims for them with `--owner <agent> --branch <their branch>`.
- Not covered: cloud sessions and other machines don't see the claims. The tracker's own "next task" doesn't read them, so run `list` first.
- Prove the lock works: `CLAIM --self-test`.

## Adding it to a project

One line in the project's CLAUDE.md: "Claim a task with the task-claim skill before starting it; release it when the PR is open." For a hard guarantee rather than a model choice, add a PreToolUse hook that runs `check` before the tracker's set-status call.
