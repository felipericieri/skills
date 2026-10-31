# Networking, Persistence and Connectivity

Modeled on Imontour (`Packages/Modules/Networking`, `Packages/Features/Persistence`, `docs/features/connectivity.md`, ADR-0014/0015). In Imontour, Networking and Persistence are built and tested; Connectivity is specified but not built, and the decision of how a signed-in person edits offline is still open. Treat the connectivity section as the default design, tune its numbers on a device, and write the offline-editing ADR before building on it.

## Which modules a project gets

| Project has | Modules |
|---|---|
| Talks to an HTTP API | `Networking` (Modules layer) |
| Saves data on the device (any offline use) | `Persistence` (Feature layer, no UI pair) + `DocumentStore` / `KeyValueStore` in Common |
| Both, and must behave sensibly without a network | plus `Connectivity` (Modules), `Connection` + `ConnectionUI` (Feature pair), banner in CommonUI |

Persistence and any other logic-only module with no screens is the one exception to "every feature has two modules".

## Networking (Modules layer)

Domain-neutral transport to one API. It knows nothing about the app's models. Package at `Packages/Networking`, depends on nothing local.

| Piece | Role |
|---|---|
| `HTTPTransport` (protocol, `Sendable`) | The one network call: `send(URLRequest) async throws -> (Data, HTTPURLResponse)`. `URLSessionTransport` is the live adapter. Tests inject a stub, so nothing touches the network. |
| `APIRequest` / `APIResponse` | Value types: method, absolute path, query, headers, body, `requiresAuth` (false for public endpoints). Helpers for JSON bodies and header lookup (case-insensitive, ETag unquoted). |
| `APIClient` (struct) | Builds the URL, adds `Authorization: Bearer`, maps every non-success status to an `APIError`, returns `APIResponse`. Typed calls are built on top of `send`. |
| `AccessTokenProvider` (protocol) | Supplies the token; the App implements it on the sign-in session. `accessToken(afterRejecting:)` offers a fresher one after a `401`. |
| `APIError` | Closed enum callers switch over: `notSignedIn`, `unauthorized`, `authUnavailable` (503), `notFound`, `conflict`, `preconditionFailed(currentRevision:)`, `preconditionRequired`, `rejected(code:message:)`, `payloadTooLarge`, `server(status:code:message:)`, `network(URLError.Code)`, `invalidResponse`. |
| `APICoding` | One encoder/decoder pair with the API's date format (fractional-second ISO 8601, unknown fields ignored). Nothing else builds a `JSONDecoder` for the API. |

Rules:
- **One `401` retry, authenticated calls only,** with a different token from the provider; a second `401` or no better token throws `unauthorized`. A request refused before any handler runs can't be applied twice.
- **`503` on an authenticated call is not a sign-out.** It means the token couldn't be checked: report it as unavailable and keep the session.
- **Cancellation is not a failure.** Propagate `CancellationError`; never map it to `network`.
- The transport never retries writes. Retry policy lives in the connectivity section below.
- **Typed domain calls do not live in Networking.** A protocol such as `TripsAPI` (list/create/get/replace/delete) and its `Remote...` implementation over `APIClient` live in the Feature module that owns that data (`Persistence` in Imontour), alongside the wire DTOs. Core types are not `Codable`; the DTO owns the wire format.
- **Optimistic concurrency** when documents are replaced whole: `revision` as `ETag`, `PUT` with `If-Match`, `412` returns `currentRevision`, the client decides how to merge. Never last-write-wins across devices.
- **The contract wins.** Keep a pinned copy of the API's `openapi.yaml` in `docs/api/`, never edit it, and add a drift-check script. Tolerate open-ended values (unknown enum strings must not fail decoding); compare `UUID`s, not strings.
- Base URL, anon keys and other public client values come from xcconfig through the generated Info.plist; the App builds `APIClient` at the composition root. Empty config means the feature is off, not a crash.

TCA wiring: the Feature declares the typed protocol (`TripsAPI`) with a `DependencyKey`; `liveValue` is built by the App, `testValue` is failing (`reportIssue`). Reducers map `APIError` to the feature's own error type in the effect (see `concurrency-localization-errors.md`); they never switch on `APIError` in `State`.

Tests: Networking is tested against a stub transport (queue of replies, records requests). Write the stub as an `actor`, not a lock-based `@unchecked Sendable` class. Cover: status to error mapping, header/ETag handling, coding with and without fractional seconds, the `401` retry (once, only with a different token), `503` not signing out.

## Persistence (Feature layer)

Only for apps that keep data on the device. First decide, in an ADR, which of these the app is: online-only (no Persistence module), local-only (this section), or a local cache or sync of remote data (this section plus the offline ADR below).

Split:
- **Common:** `DocumentStore` protocol (`load`, `save` atomic, `remove`, `moveAside`) with `FileDocumentStore` and `InMemoryDocumentStore`; `KeyValueStore` protocol with `UserDefaultsKeyValueStore` and in-memory. Small settings and flags go through `KeyValueStore`, never `UserDefaults` directly. The App builds the stores.
- **Persistence:** the versioned DTO (`schemaVersion`), mapping to and from Core, the load policy, autosave. Imports Core and Common, no SwiftUI.

Rules:
- **One source of truth per fact.** No second copy of the same data in UserDefaults or a cache.
- **Derived values are never stored.** Totals, counts and dates the model can compute are recomputed by Core on load.
- **Core types are not `Codable`.** The DTO is. Store calendar-independent values (ISO date strings), so a time-zone change doesn't shift data.
- **Never silently overwrite or delete a file.** Load policy: missing file means empty state, no error. Unreadable, or a `schemaVersion` newer than the app: move it aside as `<name>.corrupt-<UTC timestamp>.json`, start empty, never overwrite the copy. Older version: migrate forward through a chain (`[from: migration]`), each step covered by a committed fixture test.
- **Writes are atomic** (a crash mid-save leaves the old file). Saving an empty state removes the file.
- **Autosave:** an `actor` that debounces (about 1 s; one write of the latest state per burst), exposes `trigger(_:)` and `flush()`, and flushes when the app leaves the foreground. A failed write stays pending, goes to `ErrorReporter`, and is retried on the next change or flush; it never throws into the caller. Drive the debounce with `\.continuousClock` so tests don't sleep.
- UI tests run against an in-memory store (`-uitest`); a `-uitest-store <name>` flag uses a file store so a test can relaunch.

### Offline editing: decide before building

When data also lives on a server, the answer to "can the person keep editing offline?" changes the architecture, so it gets its own ADR before any sync work. The choices to weigh:

1. **Online-only:** no local cache; offline shows the connectivity banner and disables writes. Simplest.
2. **Local cache, server wins:** read offline, write only online.
3. **Local-first with an outbox:** edits are saved locally and sent through one save path (one write at a time, `If-Match` revision), retried when the connection returns, with a conflict flow on `412`.

Also decide: how existing local data moves into a new account (upload first, retire the local file **only after** the upload succeeded, keep everything on failure), and what happens when the account already has data. Until the ADR exists, don't extend or remove the existing local persistence.

## Connectivity (default strategy)

One app-wide connection state, one indicator, and a request policy. Features say only what needs the network.

**Two signals, kept separate:**
- *Device connection:* is there a network path (`NWPathMonitor`; works on iOS, iPadOS, macOS; no permission). Instant and cheap, but only a hint: a captive portal or a down API still looks online.
- *Service reachability:* do our services answer. The truth, but only known after a try.
- **Never refuse a request on the monitor's word.** Try it with short timeouts and feed the outcome back.

**States:**

| State | Meaning | Banner |
|---|---|---|
| Online | A path exists and services answered recently, or nothing has been tried | None; after a recovery, a brief "Back online" |
| Offline | The monitor reports no usable path | "You're offline" |
| Service unreachable | Online, but a request to our services timed out, couldn't connect, or got a `503` | "Can't reach <App> right now" |
| Limited | Low Data Mode or expensive path | None; hold back large uploads and background refreshes |

Rules:
- Offline comes from the monitor alone. Service unreachable comes only from request outcomes while the monitor says online. A success clears it, and so does the monitor going offline and back.
- Show the banner only after about 2 s in a bad state (blips never show); "Back online" for about 3 s. These and the ~15 s request timeout and two read retries are starting values: tune on a device.
- A `4xx`, a conflict, or a `5xx` other than `503` means the service answered: not a connectivity problem. A cancelled request is not one either.

**Request policy:**
- Every network adapter (Networking, Authentication, Geocoding...) classifies failures the same way (offline, timed out, cannot connect, other) and reports each outcome through one protocol that the connection state listens to.
- Short timeouts, `waitsForConnectivity` off, so the person gets an answer quickly.
- `GET`s retry by themselves: a couple of times with short backoff, and once more when the connection returns.
- Writes are never retried by the transport (apart from the one `401` retry). They go through the app's single save path, which retries when the state returns to online, so a reconnect can never double-save.

**Per-feature behavior** (each feature states what it needs, in one shared way): sign-in buttons that need the network are disabled with the reason while any offline-capable choice (such as guest mode) still works; search keeps the typed text and says it needs a connection; forms keep the draft; map tiles that are blank are explained by the banner; purely local features (reminders) say nothing.

**Layering:**

| Piece | Layer |
|---|---|
| `ConnectionStatus`, monitoring protocol, outcome-reporting protocol, a fake | Common (+ CommonTesting) |
| `NWPathMonitor` adapter | `Connectivity` (Modules), imports Common only |
| Failure classification and outcome reports | Networking and other HTTP adapters |
| Connection state machine (pure, injected clock) | `Connection` (Feature), a `@Reducer` at the root store |
| Environment value / observable model | `ConnectionUI` (FeatureUI) |
| The banner component | CommonUI, used once at the root: below the status bar on iPhone, top of content on iPad and Mac; never covers controls, never dismissible |
| Building the monitor, store and root overlay; debug flags | App |

**Banner requirements:** announced to VoiceOver ("You're offline", "Back online"), respects Reduce Motion, theme tokens only, correct at the largest Dynamic Type; one preview and one snapshot per state.

**Testing:** the state machine is unit-tested with a `TestClock` (delay shown, blip hidden, recovery, `4xx` ignored, `503` unreachable). Debug builds can fake both signals (`-uitest-offline`, `-uitest-service-down`) so acceptance tests cover every state without touching the network.
