---
name: release-checklist
description: Keeps a running list of things that only matter at release (third-party services and SDKs, API keys and secrets, bundle/team/app IDs, domains and URLs, entitlements, privacy and store requirements, placeholders to replace), and shows it on request. Record an entry whenever the work you are doing introduces one of these, without being asked. Show the list when the user runs /release-checklist or asks "what's left before release", "what have we added so far", or "release todo".
---

# Release checklist

While building, many things are fine as placeholders but must be real by release: a Sentry DSN, a Google client ID, a production domain, an App Store Connect record. They get forgotten because nothing breaks until the end. This skill keeps them in one file in the project, one entry per thing, tagged with the iteration that introduced it.

The checklist is `docs/release-checklist.md` in the project (create it, and `docs/`, on the first entry). Commit it with the work that adds an entry.

## Record (background, without being asked)

When a change introduces, or starts depending on, any of these, add an entry in the same change:

| Category | Examples |
|---|---|
| Third-party services | Analytics, crash reporting, auth providers, payments, push, ad networks, backend accounts |
| Secrets and keys | API keys, DSNs, client secrets, signing keys, certificates, provisioning profiles |
| IDs | Bundle ID, team ID, app group, keychain group, APNs, OAuth client IDs, product IDs, store app IDs |
| Domains and URLs | Production API base URL, associated domains, universal links, deep-link scheme, privacy policy, terms, support URL |
| Accounts and compliance | App Store Connect or Play Console records, privacy labels, data-safety forms, tracking consent, export compliance, review notes, test accounts for reviewers |
| Capabilities | Entitlements, background modes, permission usage strings |
| Placeholders | Dev or staging values, fake IDs, `TODO`s, debug-only switches that must change or be removed |

Rules:

- **Never write a secret value** into the file. Write its name and where it goes (`SENTRY_DSN` in `Config/Production.xcconfig`), and where to get it.
- One line per thing, imperative, saying what the user must do: "Create the production Sentry project and set `SENTRY_DSN`".
- Check for an existing entry first. Update it instead of adding a duplicate.
- Say where the placeholder lives in the code (file or config key), so it can be found and replaced.
- Add the entry, then tell the user in your summary: "Added to release checklist: ...". Do not stop to ask first.
- When the user says an item is done, tick it (`[x]`). Remove an item only if the thing was removed from the project.

Entry format (categories are `##` headings; keep them in the order of the table above, and add one only when needed):

```markdown
# Release checklist

## Third-party services

- [ ] **Sentry**: create the production project and set `SENTRY_DSN` in `Config/Production.xcconfig` (dev uses a placeholder). _Added: feature/crash-reporting · 2026-11-02_

## Domains and URLs

- [ ] **Privacy policy URL**: host the policy and replace `https://example.com/privacy` in `Settings/AboutView.swift`. _Added: feature/settings · 2026-11-03_
```

`Added:` is the iteration: the current branch name (or task id) and today's date. It is what lets the list be shown by iteration.

## Show (`/release-checklist`)

Run the bundled script from the project root. It is `scripts/summary.py` in this skill's directory.

```bash
python3 <this skill's directory>/scripts/summary.py            # open items, grouped by iteration
python3 <this skill's directory>/scripts/summary.py --all      # include done items
python3 <this skill's directory>/scripts/summary.py docs/release-checklist.md   # another path
```

Then present it to the user as is, in iteration order, and add:

- the total open and done,
- which open items block the first release most (anything with secrets, IDs or accounts that need lead time, such as store records or domain DNS),
- an offer to tick items or open any of them in detail.

If the file does not exist, say so and offer to scan the project for placeholders and third-party usage to seed it. Showing the list changes nothing; only recording and ticking do.
