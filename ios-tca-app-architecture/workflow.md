# Workflow defaults

These are defaults. If the project's `CLAUDE.md` says otherwise (branching, who merges, commit scopes), the project wins.

## Before finishing any change

1. `python3 -I scripts/check_layering.py` and `bash scripts/check-theme-usage.sh` pass (copy both from `templates/scripts/`).
2. Unit tests for the touched packages pass (`swift test` inside the package, or the Unit Suite plan). Run only what the change covers.
3. State which tests are affected and updated: unit (reducers, clients, pure logic), snapshot (any view or CommonUI component change), acceptance (any changed flow, identifier or copy). "Checked, nothing needs updating" is a valid answer; skipping the check is not.
4. Snapshot and acceptance tests are written and updated but not run. Say so in the summary, so the user knows to run them.
5. README.md, CLAUDE.md and `project.yml` reflect the change if setup, commands, layout, environments or status changed.

## Git

- One task, one branch, named `<type>/<slug>` (`feature/`, `fix/`, `chore/`). Never work on the default branch.
- Conventional Commits: `<type>(<scope>): <imperative summary, 72 chars max>`. Scope is a module or layer name. Types: feat, fix, refactor, test, docs, chore, build, ci.
- A bug fix starts with a test that fails for that bug.
- One logical change per commit, with its tests.
- Open a pull request for review. Merging, tagging and releasing happen only when the user says so.

## PR description

Layer of each module touched; tests added or updated; which suites were run (unit only) and which were not (snapshot, acceptance); snapshots re-recorded and why, if any.
