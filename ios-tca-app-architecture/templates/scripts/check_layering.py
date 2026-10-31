#!/usr/bin/env python3
"""Fail when a package breaks the module layering rules.

Layers (by location under Packages/):
  base        Core, Common            -> may depend on nothing local
  commonui    CommonUI                -> Common
  module      other root packages     -> Core, Common
  feature     Features/<Name>         -> Core, Common, modules
  featureui   Features/<Name>UI       -> its own feature, Core, Common, CommonUI
  CommonTesting is allowed everywhere as a dependency but only listed in test targets (review by eye).

Also fails when:
  * a FeatureUI has no matching Feature package
  * Core, Common or a Feature imports SwiftUI/UIKit/AppKit (Features also may not import CommonUI)
  * a dependency cycle exists

Usage: python3 -I scripts/check_layering.py [repo_root]
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
packages_dir = root / "Packages"
ui_frameworks = {"SwiftUI", "UIKit", "AppKit"}


def layer_of(package_dir: Path) -> str:
    name = package_dir.name
    if name in ("Core", "Common"):
        return "base"
    if name == "CommonUI":
        return "commonui"
    if name == "CommonTesting":
        return "testing"
    if package_dir.parent.name == "Features":
        return "featureui" if name.endswith("UI") else "feature"
    return "module"


allowed = {
    "base": set(),
    "commonui": {"base"},
    "module": {"base"},
    "feature": {"base", "module"},
    "featureui": {"base", "commonui"},
    "testing": {"base", "module"},
}

packages = {p.parent.name: p.parent for p in packages_dir.glob("**/Package.swift")
            if ".build" not in p.parts and "checkouts" not in p.parts}
errors: list[str] = []
edges: dict[str, set[str]] = {}

for name, directory in packages.items():
    layer = layer_of(directory)
    manifest = (directory / "Package.swift").read_text(encoding="utf-8")
    deps = set()
    for relative in re.findall(r'\.package\(\s*path:\s*"([^"]+)"', manifest):
        target = (directory / relative).resolve().name
        if target in packages:
            deps.add(target)
    edges[name] = deps

    for dep in deps:
        dep_layer = layer_of(packages[dep])
        if dep_layer == "testing":
            continue
        is_own_feature = layer == "featureui" and dep == name.removesuffix("UI")
        if dep_layer not in allowed[layer] and not is_own_feature:
            errors.append(f"{name} ({layer}) must not depend on {dep} ({dep_layer})")

    if layer == "featureui" and name.removesuffix("UI") not in packages:
        errors.append(f"{name} has no logic module named {name.removesuffix('UI')}")

    if layer in ("base", "feature"):
        forbidden = set(ui_frameworks) | ({"CommonUI", f"{name}UI"} if layer == "feature" else set())
        for swift_file in (directory / "Sources").rglob("*.swift"):
            for imported in re.findall(r"^\s*import\s+(\w+)", swift_file.read_text(encoding="utf-8"), re.M):
                if imported in forbidden:
                    errors.append(f"{swift_file.relative_to(root)}: {name} ({layer}) imports {imported}")


def find_cycle() -> list[str] | None:
    visiting, done = [], set()

    def visit(node: str):
        if node in done:
            return None
        if node in visiting:
            return visiting[visiting.index(node):] + [node]
        visiting.append(node)
        for nxt in sorted(edges.get(node, ())):
            cycle = visit(nxt)
            if cycle:
                return cycle
        visiting.pop()
        done.add(node)
        return None

    for node in sorted(edges):
        cycle = visit(node)
        if cycle:
            return cycle
    return None


cycle = find_cycle()
if cycle:
    errors.append("dependency cycle: " + " -> ".join(cycle))

if errors:
    print("Layering violations:")
    print("\n".join(f"  - {e}" for e in errors))
    sys.exit(1)
print(f"Layering OK ({len(packages)} packages).")
