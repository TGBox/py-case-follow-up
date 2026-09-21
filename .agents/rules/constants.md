---
trigger: always_on
---

# Constants & Design Tokens Rule

1. **No Magic Numbers**:
   - All numerical values, UI dimensions, paddings, margins, spacings, corner radii, and font sizes must be defined as centralized constants or design tokens in `src/constants.py` (e.g., `PADDING_*`, `CORNER_RADIUS_*`, `SPACING_*`, `DIALOG_DIMENSIONS`, etc.).
   - All timeouts, intervals, polling frequencies, retry limits, thresholds, and buffer limits must reside in `src/constants.py`.

2. **No Hardcoded Internal Strings**:
   - Technical identifiers, system file names, regex patterns, fallback keys, and supported extensions must be imported from `src/constants.py`.

3. **User-Visible Strings**:
   - All user-facing strings (labels, button texts, headers, dialog titles, notifications, tooltips, error messages) must not be hardcoded in Python code. They must be resolved via `tr("section.key", "Default")` and present in all three locale files (`locales/de.json`, `locales/en.json`, `locales/sv.json`) with 100% leaf-key parity.
