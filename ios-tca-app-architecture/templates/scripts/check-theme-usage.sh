#!/usr/bin/env bash
# Fails when a FeatureUI view uses literal colors, fonts, paddings, spacing, radii or fixed frames
# instead of the Theme. PreviewSupport.swift and #Preview lines are exempt. CommonUI defines the tokens,
# so it is not scanned.
set -uo pipefail
cd "$(dirname "$0")/.."

pattern='Color\(red:|Color\(white:|\.padding\([0-9]|\.padding\(\.[a-zA-Z]+, *[0-9]|spacing: *[1-9]|cornerRadius: *[0-9]|\.shadow\(|\.font\(|\.foregroundStyle\(\.(white|black|secondary|primary|tertiary|tint|orange|red|green|blue|gray)\b|\.frame\((width|height|minWidth|minHeight|maxWidth|maxHeight): *[0-9]|\.frame\([0-9]'

found="$(grep -rnE "$pattern" Packages/Features/*UI/Sources --include='*.swift' \
    | grep -v 'PreviewSupport.swift' | grep -v '#Preview' | grep -vE '^[^:]+:[0-9]+:\s*//' || true)"

if [[ -n "$found" ]]; then
    echo "Literal design values found. Use the Theme (colors, fonts, spacing, radius, shadows, sizes):"
    echo "$found"
    exit 1
fi
echo "No literal design values in FeatureUI sources."
