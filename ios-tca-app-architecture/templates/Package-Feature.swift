// swift-tools-version: 6.2
// Packages/Features/__Feature__/Package.swift  (the logic module: reducer, clients, no SwiftUI)
import PackageDescription

let package = Package(
    name: "__Feature__",
    platforms: [.iOS(.v26), .macOS(.v26)],
    products: [
        .library(name: "__Feature__", targets: ["__Feature__"]),
    ],
    dependencies: [
        .package(url: "https://github.com/pointfreeco/swift-composable-architecture", .upToNextMinor(from: "1.17.0")),
        .package(path: "../../Core"),
        .package(path: "../../CommonTesting"),
    ],
    targets: [
        .target(
            name: "__Feature__",
            dependencies: [
                .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
                .product(name: "Core", package: "Core"),
            ]
        ),
        .testTarget(
            name: "__Feature__Tests",
            dependencies: [
                "__Feature__",
                .product(name: "CommonTesting", package: "CommonTesting"),
            ]
        ),
    ]
)
