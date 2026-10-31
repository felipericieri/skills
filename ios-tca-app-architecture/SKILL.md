---
name: ios-tca-app-architecture
description: Use when creating a new iOS/iPadOS/macOS SwiftUI app or feature, adding modules, writing Swift code, async/concurrency code, user-facing strings, error handling, tests, test plans, xcconfig/XcodeGen setup, or design-system (Theme, spacing, radius) code in a project that uses The Composable Architecture (TCA)
---

# iOS App Architecture (TCA, modular, XcodeGen)

## Overview

Every iOS project follows one shape: TCA features split into `Feature` + `FeatureUI` modules, a `Core` and a `Common`/`CommonUI` base, a themed design system, XcodeGen + xcconfig, and a fixed test strategy. Composition over inheritance, always. Depend on protocols, not implementations, wherever TCA allows it (dependency clients).

**Violating the letter of these rules is violating the spirit.**

## Always green: no change breaks the app

At the end of every iteration (every task, commit and PR) all of these hold:

- The app **builds and launches** for each supported platform (iOS Simulator on iPhone 18 Pro, macOS), and the person can still use what worked before.
- **Everything compiles, tests included:** snapshot and acceptance targets must build even though they are not run. Use `xcodebuild build-for-testing` (or the test plan's build step) so a change that breaks a snapshot or UI test target is caught without running it.
- **Unit tests pass** for every package the change touches, and for any package that depends on one it touched.
- The layering and theme scripts pass.

How to keep iterations small enough to stay green:

- Slice work vertically so each step is shippable: a new feature is wired into the app in the same change that introduces it, or hidden behind a flag/unreachable entry point, never half-connected.
- Change a protocol, model or API in compatible steps: add the new, migrate callers, remove the old. Don't leave callers broken "until the next task".
- Never comment out, skip or delete a failing test to get green. Fix the code, or fix the test with an explanation.
- Persisted data and API contracts stay readable: a new schema version ships with its migration and fixture test in the same change.
- If a change has no visible effect yet, say so and name the first step that will show on screen. The app still launches.
- If you can't make it green, stop and report what is red and why. Don't hand over a broken tree.

## Testing rules (read first)

- Unit tests: **Swift Testing**. Snapshot tests: **Point-Free `swift-snapshot-testing`**. Journeys: **XCUITest acceptance tests**, when the app has user journeys.
- **Never run acceptance or snapshot tests to verify your changes.** They are run manually. Verify with unit tests only (`swift test` in the package, or the Unit Suite plan).
- **Only exception:** recording snapshots. Then run only the affected snapshot tests, on **iPhone 18 Pro**. Snapshot default device is always iPhone 18 Pro.
- Still write/update snapshot and acceptance tests with every change that touches UI or a journey. Not running them is not skipping them.
- Every project has unit and snapshot tests. A feature without tests is not done.
- `Feature` module: unit tests (reducers via `TestStore`, clients, pure logic). `FeatureUI` module: unit tests (view-level state/mapping) **and** snapshot tests (every screen and state, large Dynamic Type, dark mode).
- Snapshot files live in `Snapshots/`, named `<Subject>SnapshotTests`; unit tests at the test target root, `<Subject>Tests`.

### Test plans (create all five, in `Config/TestPlans/` or project root)

| Plan | Contains |
|---|---|
| Full Suite | all unit + snapshot tests |
| Unit Suite | all unit tests |
| Snapshot Suite | all snapshot tests |
| Acceptance Suite | all UI tests |
| Release Suite | critical-journey UI tests + all unit + all snapshot tests |

Declare them in `project.yml` (`schemes.<name>.test.testPlans`). Don't hand-write them: copy `templates/scripts/generate-test-plans.py` to `scripts/` and run `python3 -I scripts/generate-test-plans.py`. It splits suites by name: snapshot suites end in `SnapshotTests`, critical UI journeys end in `CriticalJourneyTests`. Re-run when either is added or renamed.

## Supporting files (read when needed)

| File | Use for |
|---|---|
| `tca-conventions.md` | Reducer shape, dependencies as protocols, composition, navigation, view and test conventions |
| `example.md` | Complete Profile feature: model, reducer, client, unit test, view, snapshot test |
| `templates/project.yml`, `templates/Config/` | XcodeGen spec and xcconfig layout for a new app |
| `templates/Package-Feature.swift`, `templates/Package-FeatureUI.swift` | `Package.swift` for a new Feature / FeatureUI pair |
| `templates/CommonTesting/ViewSnapshots.swift` | Shared `assertViewSnapshot` helper (iPhone-13 layout, rendered on the iPhone 18 Pro simulator) |
| `templates/scripts/generate-test-plans.py` | Generates the five test plans |
| `templates/scripts/check_layering.py`, `check-theme-usage.sh` | Enforce module layering and Theme-only design values; copy to `scripts/` |
| `networking-persistence-connectivity.md` | Networking module, Persistence module, offline/connectivity strategy (from Imontour) |
| `concurrency-localization-errors.md` | Concurrency, localization and error-handling rules |
| `workflow.md` | Pre-finish checks, git and PR defaults (project `CLAUDE.md` overrides) |

Replace `__App__`, `__Feature__`, `__company__` placeholders and pin the TCA and snapshot-testing versions to the current minor when scaffolding.

## Modules

Every feature = **two modules**, in `Packages/Features/`:

- `Feature` – TCA reducer, state, actions, dependency clients (protocols + live/test values), domain logic. No SwiftUI.
- `FeatureUI` – SwiftUI views driven by `StoreOf<Feature>`. Depends on `Feature`, never the reverse.

If the name collides with a system type (`Calendar`, `Map`), suffix it: `CalendarFeature` / `CalendarFeatureUI`.

Other modules sit at the root of `Packages/`:

- **Core** – lowest level, importable anywhere, holds the app's core domain. Imports nothing from the project.
- **Common** – shared non-UI utilities (formatting, extensions, logging, storage/HTTP primitives).
- **CommonUI** – shared UI: `Theme`, default components, asset catalog. Depends on Common at most.
- Any other module (Networking, Authentication, Connectivity, ...) also lives at the root of `Packages/`. `Persistence` is a Feature-layer module with no UI pair (logic-only modules are the one exception to the two-module rule).

Dependencies point downward only: App → FeatureUI → Feature → Core/Common. No cycles.

## Platforms: iOS, iPadOS and macOS

Every feature works on all three unless its spec says otherwise.

- `Package.swift`: `platforms: [.iOS(.v26), .macOS(.v26)]`. Feature, Core and Common import no UIKit/AppKit. Platform-specific code lives only in FeatureUI/CommonUI (`#if os(...)` only where a view genuinely differs) or in an adapter module behind a protocol.
- Layout adapts to size class and window size (`NavigationSplitView`, `ViewThatFits`, adaptive grids); never `UIScreen` or fixed device sizes. Support pointer, keyboard and menu commands on iPad and Mac.
- Verify with unit tests plus a macOS compile check: `xcodebuild build -destination 'generic/platform=macOS'`. Snapshot tests are iOS-only (`#if os(iOS)`); screens with an adaptive layout also get an iPad snapshot.

## Concurrency, localization, errors

Read `concurrency-localization-errors.md` before writing async code, user-facing text or failure paths. Headlines: no unstructured `Task {}` (use `.run` and `.task`), data is `Sendable`, shared mutable state is an actor; strings live in one `<Module>Strings` enum per module (`LocalizedStringResource` constants, String Catalog beside it) and never in Feature/Core/Common; typed errors per module, mapped at the boundary and shown through a CommonUI state view.

## Networking, persistence, connectivity

If the app talks to an API, add a **Networking** module (Modules layer, domain-neutral transport: `HTTPTransport`, `APIClient`, closed `APIError`; typed domain calls live in the owning Feature). If it saves data on the device, add **Persistence** (Feature layer, no UI pair; `DocumentStore`/`KeyValueStore` in Common). If both and it must behave without a network, add the connectivity strategy: two signals (network path hint, request outcomes as truth), one root banner, never refuse a request on the monitor's word, reads retry and writes go through one save path. Offline editing for server data needs its own ADR first. Read `networking-persistence-connectivity.md` before building any of these.

## Folder structure

```
CLAUDE.md  README.md  project.yml      # top level; all three added to the Xcode project
Config/                                # xcconfigs + any config file
  Dev.xcconfig Staging.xcconfig Production.xcconfig Shared.xcconfig
  Dev/ Staging/ Production/            # per-env folders when several files per env (e.g. GoogleService-Info.plist)
  TestPlans/
<AppName>/                             # main target
  Supporting Files/                    # Info.plist, entitlements, ...
Packages/
  Features/                            # every Feature and FeatureUI
  Core/ Common/ CommonUI/ <others>/
```

## Project setup

- Prefer **XcodeGen**. Per-environment/scheme settings live in `Config/*.xcconfig`, never in target build settings (they override xcconfig).
- `project.yml` must list `CLAUDE.md`, `README.md` and `project.yml` itself as files (`sources` with `buildPhase: none`) so they show in Xcode.
- Generated `.xcodeproj` is gitignored; never hand-edit it.

## Code ordering inside every type

Order properties and methods by, in this priority:

1. `typealias` → `public` → `internal` → `private`
2. `weak` → strong
3. `static` → instance
4. `var` → `let`

Same for properties and methods. Add `// MARK: - Private methods` before private methods. One blank line between methods; properties may be grouped by nature.

Naming carries the meaning; comment only what a name cannot say. No lengthy comments.

## SwiftUI views

- Break views into subviews: a `private struct ...: View` when complex and used only in that file; its own file in the module when other screens use it; **CommonUI** when used across modules.
- CommonUI holds default app-wide components (buttons, rows, cards, empty/error states). Reuse before creating.
- Every view file ends with `#Preview`s (one per state) wrapped in `#if DEBUG`.

## CommonUI design system

**Theme** object holds colors, fonts, shadows; read via `@Environment(\.theme)`. Always provide **light and dark** themes. No literal colors, sizes, paddings or radii in views.

Spacing (`enum Spacing: CGFloat`), plus a `zero`:

| xxSmall | xSmall | small | standard | large | xLarge | xxLarge |
|---|---|---|---|---|---|---|
| 2 | 4 | 8 | **16** | 20 | 24 | 32 |

Everything else is a multiple of 4 (the user's xxSmall = 2 is the one deliberate exception). `Radius` uses the same pattern. Provide modifiers/initializers so call sites read by name: `.padding(.top, .small)`, `VStack(spacing: .standard)`, `.cornerRadius(.standard)`. **Reference:** `Packages/CommonUI/Sources/CommonUI/Theme/` in the Imontour project (`Spacing`, `Radius`, `Layout+Spacing`, `Theme`).

Assets: an asset catalog inside CommonUI with a singleton accessor (e.g. `CommonAssets.shared.image(.logo)`), so any module queries shared images/resources.

**Accessibility is mandatory:** every control is VoiceOver-navigable (labels, hints, traits, sensible order); text scales with Dynamic Type up to `.accessibility3`/xxxLarge via system fonts or scaled fonts; layouts must not break at that size (no fixed heights on text).

## Quick checklist for a new feature

1. `Feature` + `FeatureUI` packages under `Packages/Features/`, registered in `project.yml`.
2. Reducer with protocol-backed dependency clients; reducer tests with `TestStore` (Swift Testing).
3. Views using Theme tokens only; previews per state; VoiceOver + Dynamic Type checked.
4. Snapshot tests written (recorded only on iPhone 18 Pro, only when recording); acceptance test for any new journey.
5. Verified with unit tests only, plus the layering and theme scripts. Snapshot/acceptance left for the manual run. See `workflow.md`.

## Red flags

| Thought | Reality |
|---|---|
| "I'll run the snapshot tests to be sure" | Forbidden. Run unit tests; snapshots are manual unless recording. |
| "A base class avoids duplication" | Compose instead: protocols, small structs, reducers. |
| "Hardcode 10pt just here" | Add/choose a theme token. |
| "Small feature, one module is fine" | Always `Feature` + `FeatureUI`. |
| "Put the config in build settings" | xcconfig in `Config/`. |
| "It will compile again after the next task" | Every iteration builds, launches and passes its unit tests. Slice smaller or keep old and new side by side. |
| "I'll skip/comment out the failing test for now" | Never. Fix it, or stop and report. |
| "We're in a hurry / the user said hardcode it" | Use the nearest theme token, or add the missing token to CommonUI and tell the user. Hurry never waives the rules. |
| "I'll run the snapshot tests once to confirm they pass" | Reference images don't exist until recorded; recording is the only run allowed, on iPhone 18 Pro. |
| "The project's CLAUDE.md differs from this skill" | The project wins for folder names, git and merge rules; testing rules and theme rules still apply. |
