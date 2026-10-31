// swift-tools-version: 6.2
// Packages/Features/__Feature__UI/Package.swift  (SwiftUI views; unit + snapshot tests)
import PackageDescription

let package = Package(
    name: "__Feature__UI",
    platforms: [.iOS(.v26), .macOS(.v26)],
    products: [
        .library(name: "__Feature__UI", targets: ["__Feature__UI"]),
    ],
    dependencies: [
        .package(url: "https://github.com/pointfreeco/swift-composable-architecture", .upToNextMinor(from: "1.17.0")),
        .package(url: "https://github.com/pointfreeco/swift-snapshot-testing", .upToNextMinor(from: "1.18.0")),
        .package(path: "../__Feature__"),
        .package(path: "../../Core"),
        .package(path: "../../CommonUI"),
        .package(path: "../../CommonTesting"),
    ],
    targets: [
        .target(
            name: "__Feature__UI",
            dependencies: [
                "__Feature__",
                .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
                .product(name: "Core", package: "Core"),
                .product(name: "CommonUI", package: "CommonUI"),
            ]
        ),
        .testTarget(
            name: "__Feature__UITests",   // unit tests at root, snapshot tests in Snapshots/
            dependencies: [
                "__Feature__UI",
                .product(name: "SnapshotTesting", package: "swift-snapshot-testing"),
                .product(name: "CommonTesting", package: "CommonTesting"),
            ],
            exclude: ["Snapshots/__Snapshots__"]
        ),
    ]
)
