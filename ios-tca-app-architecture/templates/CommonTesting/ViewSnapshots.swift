#if os(iOS)
import SnapshotTesting
import SwiftUI
import UIKit

/// The one configuration every snapshot is recorded and verified on: an iPhone-13-sized layout, rendered
/// by the iPhone 18 Pro simulator (iOS 27). Change it only on purpose and re-record everything.
public let snapshotDevice = ViewImageConfig.iPhone13

/// Asserts a snapshot of a SwiftUI view, in the shared configuration.
///
/// Name tests after the state they show (`func emptyTrip()`): the image file takes the test's name.
/// Pass `dark` or `large` to cover dark mode and an accessibility Dynamic Type size.
/// Pass `fitting` for a small component: it is rendered at its own size and not on a full screen.
@MainActor
public func assertViewSnapshot<V: View>(
    of view: V,
    named name: String? = nil,
    dark: Bool = false,
    large: Bool = false,
    fitting: Bool = false,
    fileID: StaticString = #fileID,
    file: StaticString = #filePath,
    testName: String = #function,
    line: UInt = #line
) {
    var traits: [UITraitCollection] = []
    if dark { traits.append(UITraitCollection(userInterfaceStyle: .dark)) }
    if large { traits.append(UITraitCollection(preferredContentSizeCategory: .accessibilityExtraLarge)) }

    assertSnapshot(
        of: view,
        as: .image(
            precision: 0.99,
            perceptualPrecision: 0.98,
            layout: fitting ? .sizeThatFits : .device(config: snapshotDevice),
            traits: UITraitCollection(traitsFrom: traits)
        ),
        named: name,
        fileID: fileID,
        file: file,
        testName: testName,
        line: line
    )
}
#endif
