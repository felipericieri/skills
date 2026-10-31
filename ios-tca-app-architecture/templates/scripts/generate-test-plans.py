#!/usr/bin/env python3
"""Generate the five .xctestplan files from naming conventions.

Conventions it relies on:
  * snapshot suites end in `SnapshotTests`
  * critical UI journeys end in `CriticalJourneyTests`
  * package test targets live in Packages/**/Tests/<TargetName>/
  * the app's UI test target sources live in UITests/

Usage: python3 -I scripts/generate-test-plans.py [repo_root]
Re-run whenever a snapshot suite or a critical journey is added or renamed.
"""
import json
import re
import sys
from pathlib import Path

APP_PROJECT = "__App__.xcodeproj"
UI_TARGET = "__App__UITests"
UI_DIR = "UITests"

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
out = root / "Config" / "TestPlans"
suite_pattern = re.compile(r"\b(?:struct|final class|class)\s+(\w+(?:SnapshotTests|CriticalJourneyTests))\b")


def suites_in(directory: Path, suffix: str) -> list[str]:
    found = set()
    for swift_file in directory.rglob("*.swift"):
        for name in suite_pattern.findall(swift_file.read_text(encoding="utf-8")):
            if name.endswith(suffix):
                found.add(name)
    return sorted(found)


def package_targets() -> list[dict]:
    targets = []
    for tests_dir in sorted(root.glob("Packages/**/Tests")):
        package_dir = tests_dir.parent
        for target_dir in sorted(p for p in tests_dir.iterdir() if p.is_dir()):
            targets.append({
                "container": f"container:{package_dir.relative_to(root)}",
                "name": target_dir.name,
                "snapshots": suites_in(target_dir, "SnapshotTests"),
            })
    return targets


def entry(container: str, name: str, selected=None, skipped=None) -> dict:
    result = {"target": {"containerPath": container, "identifier": name, "name": name}}
    if selected:
        result["selectedTests"] = selected
    if skipped:
        result["skippedTests"] = skipped
    return result


def plan(test_targets: list[dict]) -> dict:
    return {
        "configurations": [{"id": "00000000-0000-0000-0000-000000000001", "name": "Default", "options": {}}],
        "defaultOptions": {},
        "testTargets": test_targets,
        "version": 1,
    }


def write(filename: str, content: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / filename).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


packages = package_targets()
ui_container = f"container:{APP_PROJECT}"
critical = suites_in(root / UI_DIR, "CriticalJourneyTests")

all_non_ui = [entry(p["container"], p["name"]) for p in packages]
unit_only = [entry(p["container"], p["name"], skipped=p["snapshots"]) for p in packages]
snapshot_only = [entry(p["container"], p["name"], selected=p["snapshots"]) for p in packages if p["snapshots"]]
ui_all = [entry(ui_container, UI_TARGET)]
ui_critical = [entry(ui_container, UI_TARGET, selected=critical)] if critical else []

write("FullSuite.xctestplan", plan(all_non_ui))
write("UnitSuite.xctestplan", plan(unit_only))
write("SnapshotSuite.xctestplan", plan(snapshot_only))
write("AcceptanceSuite.xctestplan", plan(ui_all))
write("ReleaseSuite.xctestplan", plan(all_non_ui + ui_critical))
print(f"{len(packages)} package test targets, {sum(len(p['snapshots']) for p in packages)} snapshot suites, {len(critical)} critical journeys")
