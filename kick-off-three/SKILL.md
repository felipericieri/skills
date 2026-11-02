---
name: kick-off-three
description: Use when the user wants to start several tasks at once ("kick off 3", "run the next tasks in parallel", "what can go in parallel?"). Runs the where-are-we picture, picks up to three ready tasks that are independent of each other, claims them with task-claim, and starts each one in its own worktree-isolated session or subagent.
---

# Kick off three

`where-are-we` says what is left. This skill turns that into up to three parallel starts. Default is 3; honour another number if the user gives one.

## Steps

1. **Get the picture.** Follow the `where-are-we` skill: run its `status.py`, read the project's guidance for gates and deferred decisions. Do not report the full one-screen summary; only keep the candidate list.
2. **Filter to startable tasks.** Drop anything that is:
   - blocked by a dependency, an ADR/decision that does not exist yet, or something the user deferred,
   - already in progress, on an open PR, or held (`task-claim` `list`),
   - too vague to brief without asking the user a question.
3. **Pick an independent set.** Choose up to N from the remainder so that, pairwise:
   - neither depends on the other (directly or through a shared prerequisite),
   - they do not touch the same files or modules (read each task's details to find out; when unsure, treat as overlapping),
   - neither must land in the same change as the other.

   If fewer than N pass, start fewer and say why the rest were left out. Never pad the set with a task that overlaps.
4. **Confirm once.** Show one line per task: id, title, what it touches, rough size, plus the ones you left out and why. Ask "start these?" and wait. This is the only question; do not ask per task.
5. **Claim, then start.** For each confirmed task:
   - `task-claim` `claim <scope> <id> --owner <short-name>`. Exit 1 means someone holds it: swap in the next candidate or drop it.
   - Start it in its own worktree off the integration branch, following the project's working agreement (branch naming, who merges). In the Claude desktop app use `start_session` (`initiation: "user_asked"`, `context: "fresh"`, own worktree); elsewhere use a background subagent with `isolation: "worktree"`.
   - Mark the task in progress the way the project does.
6. **Brief each one fully.** The brief names the task id and its details, the files/area it owns and that it must stay inside them, the project's branch and PR rules, what done looks like (tests green, PR open), and that it must `release` its claim when the PR is open or the work is dropped. A short brief that retells nothing is fine; a vague one is not.
7. **Report.** One line per started task with its session link or agent name. Say that nothing is merged: each result is on its own branch/PR, and it is the user's call to review and merge.

## Rules

- Read-only until step 4 is answered. Nothing is claimed, branched or marked before the user says yes.
- Never take a claim over silently; `STALE` claims go back to the user.
- Do not do the tasks in this session. This session only chooses, claims and launches.
- If the user names the tasks themselves, skip steps 2 and 3's selection but still run the overlap check and warn on conflicts.
