# TCA conventions

Target: swift-composable-architecture 1.x with the Observation-based API (`@Reducer`, `@ObservableState`). Pin an exact minor version in each `Package.swift` (`.upToNextMinor`), and use the same version in every package.

## Where things live

| Thing | Module |
|---|---|
| Model shared across features (`UserProfile`) | Core |
| Reducer, State, Action, dependency **protocol**, its `DependencyKey`, live implementation | Feature |
| Test/stub implementations of the protocol | Feature test target (or a `FeatureTesting` target if shared) |
| `StoreOf<Reducer>`-driven views | FeatureUI |
| Adapter to the outside world used by many features (networking, auth) | its own root module; Feature depends on the protocol only |

Feature never imports SwiftUI or its own UI module. FeatureUI never contains domain rules.

## Reducer shape

- `@Reducer public struct <Name>Reducer` (keep the `Feature` suffix only for module names that collide with system types, e.g. `CalendarFeature`).
- `@ObservableState public struct State: Equatable`. Model screen status as one enum (`idle / loading / loaded / failed`), not parallel booleans.
- `public enum Action`: user intents first (`task`, `retryTapped`), then effect results (`loadSucceeded`, `loadFailed`), then child/delegate actions. Name by what happened, not what to do.
- Effects only through `@Dependency`. No singletons, no `Date()`, `UUID()`, `Task.sleep` directly: use `\.date`, `\.uuid`, `\.continuousClock`.
- Dependencies are **protocols** (`any ProfileLoading`), registered with a `DependencyKey` enum and a `DependencyValues` accessor. `testValue` is a failing implementation that calls `reportIssue` so an un-stubbed call fails the test.

## Composition

- Parent embeds child with `Scope(state: \.child, action: \.child) { ChildReducer() }`.
- Child talks to parent only through `Action.delegate(Delegate)`; the parent handles `.child(.delegate(...))`.
- Optional/modal child: `@Presents var child: ChildReducer.State?` with `.ifLet(\.$child, action: \.child)`.
- Multi-screen flows: `StackState<Path.State>` with `@Reducer enum Path`. Use tree-based `@Presents` for sheets, alerts, dialogs.
- Compose behavior by combining small reducers and dependency protocols. Never subclass a reducer or a view.

## Views

- `public struct <Name>View: View` holds `let store: StoreOf<<Name>Reducer>`; read state directly (`store.viewState`), send with `store.send(.retryTapped)`. Bindable state uses `@Bindable var store`.
- Switch on the status enum in a `@ViewBuilder` private property per case.
- Start loading with `.task { await store.send(.task).finish() }`.
- Every control gets an accessibility label/identifier; identifiers are what acceptance tests use.

## Testing

- Reducer tests: Swift Testing + `TestStore`, `@MainActor`, override dependencies in `withDependencies`.
- Exhaustive by default; call `store.exhaustivity = .off` only for integration-style parent tests, and say why in the test name.
- Snapshot tests drive a real `Store` with a fixed `initialState` and `withDependencies` stubs. They never hit the network, clock or disk.
- Tag-free naming convention is the contract with the test plans: snapshot suites end in `SnapshotTests`; critical UI journeys end in `CriticalJourneyTests`.
