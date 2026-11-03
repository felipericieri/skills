# Working in this repo

This repo holds Claude Code skills (one folder per skill, each with a `SKILL.md`). The `README.md` table and layout tree must list every skill.

## Git: never push from `main`

Before any commit or push, run `git branch --show-current` on its own and read the answer. Do not chain it with the commit or push.

- If the branch is `main` (or the default branch), create a feature branch first: `git checkout -b <type>/<slug>` (`feature/`, `fix/`, `chore/`). Never commit or push to `main`.
- Only push a feature branch. Changes reach `main` through a pull request that the user merges.
- Do not assume the branch is the one from earlier in the conversation. A merged PR can leave the checkout on `main`, and another chat may have switched it.
- Never force-push, and never rewrite `main`, without the user saying so.
