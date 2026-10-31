# Worked example: Profile feature

Modules: `Profile` (Feature) and `ProfileUI` (FeatureUI) in `Packages/Features/`, model in `Core`.
Token names (`theme.colors...`, `.standard`) follow CommonUI; adapt to the project's names.

## Core/UserProfile.swift

```swift
public struct UserProfile: Equatable, Sendable {
    public let name: String

    public init(name: String) {
        self.name = name
    }
}
```

## Profile/ProfileLoading.swift

```swift
import ComposableArchitecture
import Core

public protocol ProfileLoading: Sendable {
    func load() async throws -> UserProfile
}

public enum ProfileLoadingKey: DependencyKey {
    public static let liveValue: any ProfileLoading = RemoteProfileLoader()
    public static let testValue: any ProfileLoading = UnimplementedProfileLoader()
}

extension DependencyValues {
    public var profileLoader: any ProfileLoading {
        get { self[ProfileLoadingKey.self] }
        set { self[ProfileLoadingKey.self] = newValue }
    }
}

struct UnimplementedProfileLoader: ProfileLoading {
    func load() async throws -> UserProfile {
        reportIssue("ProfileLoading.load called without a stub")
        throw CancellationError()
    }
}
```

## Profile/ProfileReducer.swift

```swift
import ComposableArchitecture
import Core

@Reducer
public struct ProfileReducer {
    @ObservableState
    public struct State: Equatable {
        public enum ViewState: Equatable {
            case idle
            case loading
            case loaded(UserProfile)
            case failed
        }

        public var viewState: ViewState

        public init(viewState: ViewState = .idle) {
            self.viewState = viewState
        }
    }

    public enum Action {
        case task
        case retryTapped
        case loadSucceeded(UserProfile)
        case loadFailed
    }

    @Dependency(\.profileLoader) var profileLoader

    public init() {}

    public var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .task, .retryTapped:
                state.viewState = .loading
                return loadProfile()
            case .loadSucceeded(let profile):
                state.viewState = .loaded(profile)
                return .none
            case .loadFailed:
                state.viewState = .failed
                return .none
            }
        }
    }

    // MARK: - Private methods

    private func loadProfile() -> Effect<Action> {
        .run { send in
            do {
                await send(.loadSucceeded(try await profileLoader.load()))
            } catch {
                await send(.loadFailed)
            }
        }
    }
}
```

## Profile/Tests/ProfileReducerTests.swift (unit, Swift Testing)

```swift
import ComposableArchitecture
import Core
import Testing
@testable import Profile

@MainActor
struct ProfileReducerTests {
    @Test func loadsProfile() async {
        let profile = UserProfile(name: "Ada")
        let store = TestStore(initialState: ProfileReducer.State()) {
            ProfileReducer()
        } withDependencies: {
            $0.profileLoader = StubProfileLoader(result: .success(profile))
        }

        await store.send(.task) { $0.viewState = .loading }
        await store.receive(\.loadSucceeded) { $0.viewState = .loaded(profile) }
    }

    @Test func showsFailureThenRetries() async {
        let store = TestStore(initialState: ProfileReducer.State()) {
            ProfileReducer()
        } withDependencies: {
            $0.profileLoader = StubProfileLoader(result: .failure(StubError()))
        }

        await store.send(.task) { $0.viewState = .loading }
        await store.receive(\.loadFailed) { $0.viewState = .failed }
    }
}

private struct StubProfileLoader: ProfileLoading {
    let result: Result<UserProfile, any Error>

    func load() async throws -> UserProfile { try result.get() }
}

private struct StubError: Error {}
```

## ProfileUI/ProfileView.swift

```swift
import CommonUI
import ComposableArchitecture
import Core
import Profile
import SwiftUI

public struct ProfileView: View {
    let store: StoreOf<ProfileReducer>

    @Environment(\.theme) private var theme

    public init(store: StoreOf<ProfileReducer>) {
        self.store = store
    }

    public var body: some View {
        VStack(spacing: .standard) {
            content
        }
        .padding(.horizontal, .standard)
        .task { await store.send(.task).finish() }
    }

    @ViewBuilder
    private var content: some View {
        switch store.viewState {
        case .idle, .loading: ProgressView()
        case .loaded(let profile): loadedView(profile)
        case .failed: failedView
        }
    }

    private func loadedView(_ profile: UserProfile) -> some View {
        Text(profile.name)
            .themeFont(.title)
            .accessibilityIdentifier("profile.name")
    }

    private var failedView: some View {
        Button("Try again") { store.send(.retryTapped) }
            .accessibilityIdentifier("profile.retry")
    }
}

#if DEBUG
#Preview("Loaded") {
    ProfileView(store: Store(initialState: .init(viewState: .loaded(UserProfile(name: "Ada")))) {
        ProfileReducer()
    })
}

#Preview("Failed") {
    ProfileView(store: Store(initialState: .init(viewState: .failed)) { ProfileReducer() })
}
#endif
```

## ProfileUI/Tests/Snapshots/ProfileViewSnapshotTests.swift

One snapshot per state, plus dark and large Dynamic Type for screens. Reducer is a no-op stub so the task does not run effects.

```swift
#if os(iOS)
import CommonTesting
import ComposableArchitecture
import Core
import Testing
@testable import ProfileUI
@testable import Profile

@MainActor
struct ProfileViewSnapshotTests {
    @Test func loaded() {
        assertViewSnapshot(of: view(.loaded(UserProfile(name: "Ada"))))
    }

    @Test func loadedDark() {
        assertViewSnapshot(of: view(.loaded(UserProfile(name: "Ada"))), dark: true)
    }

    @Test func loadedLargeText() {
        assertViewSnapshot(of: view(.loaded(UserProfile(name: "Ada"))), large: true)
    }

    @Test func failed() {
        assertViewSnapshot(of: view(.failed))
    }

    private func view(_ state: ProfileReducer.State.ViewState) -> ProfileView {
        ProfileView(store: Store(initialState: .init(viewState: state)) {
            EmptyReducer()
        })
    }
}
#endif
```

Remember: write these, but do not run them to verify work. Run only to record, on iPhone 18 Pro.
