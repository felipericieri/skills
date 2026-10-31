# Concurrency, localization and error handling

## Concurrency (Swift 6 language mode everywhere)

Goal: structured concurrency only. No stray `Task {}`.

- Use `async`/`await`. No completion handlers, no Combine for new code.
- **Data is `Sendable` by construction.** Models are structs/enums with `Sendable` members. Don't add locks or `@unchecked Sendable`; if the compiler complains, fix the design.
- **Shared mutable state lives in an actor** (caches, session stores, in-flight request tracking). Not a class with a lock, not a `Sendable` class with `var`s.
- UI-facing types are `@MainActor`. Prefer `defaultIsolation(MainActor.self)` for app and FeatureUI targets (Swift 6.2, in `swiftSettings`); Feature, Core, Common and adapter modules stay `nonisolated` by default.
- Dependency protocols are `Sendable` and have `async` requirements. Implementations are a struct (stateless) or an actor (stateful).
- **Tasks:**
  - Reducers: effects only via `.run { send in ... }`. Cancellable work gets a `CancelID` and `.cancellable(id:cancelInFlight:)`.
  - Views: `.task { }` / `.task(id:)` ties work to the view lifecycle. Never `Task { }` in a `body` or button action; send an action instead.
  - `Task {}` is allowed only at a true sync-to-async boundary (an `AppDelegate` callback, a delegate method) with a one-line reason in the name or a call-site comment. `Task.detached` is banned.
  - Parallel work: `async let` or `withThrowingTaskGroup`, never an array of `Task`s.
- Time comes from `\.continuousClock`, never `Task.sleep` or `DispatchQueue.main.asyncAfter`. Randomness and dates from `\.uuid` / `\.date`.
- Respect cancellation: let `CancellationError` propagate; in reducers ignore it explicitly (`catch is CancellationError {}`), don't turn it into a user-visible failure.
- Tests: reducers with `TestStore` and a `TestClock`; no `sleep` in tests.

## Localization

- **String Catalogs** (`Localizable.xcstrings`), one per module that shows text: each FeatureUI owns its strings, CommonUI owns shared ones. Reach them only through the module's Strings enum (below).
- Keys are semantic and namespaced (`feature.screen.element`), never the English sentence. English (`en`) is the development language and the source of truth for comments to translators.
- **Strings live in one place per module: a `<Module>Strings` enum in `<Module>Strings.swift`** (`CalendarStrings`, `CommonStrings`; drop the `Feature`/`UI` suffix). Call sites never contain a key literal.
  - Constants are `static let` of `LocalizedStringResource`, not `String`: a `String` is resolved once and ignores the SwiftUI locale, so locale/RTL snapshots would show the wrong language. Strings with arguments are `static func` returning `LocalizedStringResource` (the argument is part of the sentence, so plurals and word order stay in the catalog).
  - Group related strings in nested enums (`CalendarStrings.Summary.title`). Each module has one internal `bundle` helper (`.atURL(Bundle.module.bundleURL)`) used by every entry.
  - Views use them directly (`Text(CalendarStrings.title)`, `.accessibilityLabel(CalendarStrings.Day.label(dayNumber))`). Where a plain `String` is unavoidable, convert at the edge with `String(localized: resource)`.
  - The String Catalog sits beside the enum; keys are written once, in the enum. FeatureUI owns its strings; strings shared by more than one feature are in `CommonStrings` (CommonUI).
  - A unit test per Strings enum checks the English catalog has a non-empty value for every entry.

  ```swift
  enum CalendarStrings {
      static let title = LocalizedStringResource("calendar.title", bundle: bundle)

      enum Summary {
          static let empty = LocalizedStringResource("calendar.summary.empty", bundle: bundle)
          static func days(_ count: Int) -> LocalizedStringResource {
              LocalizedStringResource("calendar.summary.days \(count)", bundle: bundle)
          }
      }

      private static let bundle = LocalizedStringResource.BundleDescription.atURL(Bundle.module.bundleURL)
  }
  ```
- **No user-facing strings in Feature, Core or Common.** They return typed values (errors, enums); the FeatureUI maps them to text. Exception: a `LocalizedStringResource` carried in a model when the text is data.
- Never concatenate or interpolate pieces of sentences. One key per sentence, with arguments (`%@`, `%lld`). Plurals and gender via catalog variations, not `if count == 1`.
- Dates, numbers, currency, durations, lists: `FormatStyle` / formatters from Common, using the environment locale. No hand-built `DateFormatter` strings in views.
- Accessibility labels and hints are localized like any other text.
- Build settings in `Shared.xcconfig`: `LOCALIZATION_PREFERS_STRING_CATALOGS = YES`, `SWIFT_EMIT_LOC_STRINGS = YES` (set on packages too via the package's catalog).
- Layout must survive long text and right-to-left. Screens get one snapshot with `\.layoutDirection = .rightToLeft` plus a long-locale one (e.g. German), alongside dark and large-text.
- Ship `en` first; add languages by adding catalog columns, not code.

## Error handling

- **Typed errors per module.** Each Feature or adapter exposes an `enum <Name>Error: Error, Equatable, Sendable`. Use typed throws (`throws(ProfileLoadingError)`) at module boundaries where it keeps call sites exhaustive.
- **Map at the boundary.** The adapter (networking, storage, auth) converts `URLError`, `DecodingError`, SDK errors into the module's domain error. Reducers never see foreign error types.
- **State, not `Error` values.** Reducer state stores a failure case (`.failed(ProfileLoadingError)`), keeping `State: Equatable`. Actions carry the domain error, not `any Error`.
- **No silent failure.** `try?` and empty `catch {}` are banned unless the line says why the failure is irrelevant. Unexpected errors go to the error reporter.
- **Reporting:** a small `ErrorReporter` protocol in Common (`report(_ error:, context:)` with non-sensitive numbers, flags and enum-like strings only), TCA dependency, `NoOpErrorReporter` default. Logging through `os.Logger` with privacy annotations; never log user data unredacted.
- **Presenting (FeatureUI):**
  - Screen-level load failures: the status enum has a `failed` case rendered by a CommonUI component with message + Retry button (`StateView`: loading / empty / failed(retry)). Offline is its own case, not a generic failure.
  - Action failures (save, delete): TCA `AlertState`, destructive/irreversible ones ask confirmation first.
  - Each domain error maps to a localized message and, where possible, a recovery action. Messages say what happened and what to do, never a raw `localizedDescription`.
- **Tests:** every error mapping gets a unit test; every reducer failure path gets a `TestStore` test; each `failed` state gets a snapshot.
