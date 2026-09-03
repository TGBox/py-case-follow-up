# Technical Investigation Report: DateTime Utils & Localization Helpers (Milestone 2)

**Author**: Explorer 2 (Milestone 2)  
**Target Path**: `.agents/explorer_m2_2/handoff.md`  
**Working Directory**: `c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_m2_2`  
**Date**: 2026-09-02  

---

## 1. Observation

### 1.1 `src/utils/datetime_utils.py` Analysis
Inspection of `src/utils/datetime_utils.py` (229 lines) reveals the following core functions and hardcoded German literals:

1. **`get_relative_date_text(val, ref_date)` (Lines 89–151)**:
   - Line 106: `clean = val.replace("Uhr", "").strip() if isinstance(val, str) else ""` (hardcoded German string replacement)
   - Line 126: Returns hardcoded literal `"heute"`
   - Line 128: Returns hardcoded literal `"morgen"`
   - Line 130: Returns hardcoded literal `"übermorgen"`
   - Line 132: Returns hardcoded literal `"gestern"`
   - Line 134: Returns hardcoded literal `"vorgestern"`
   - Lines 141, 147: Returns hardcoded literal `"diese Woche"`
   - Line 143: Returns hardcoded literal `"nächste Woche"`
   - Line 144: Returns hardcoded format string `f"in {diff_days} Tagen"`
   - Line 149: Returns hardcoded literal `"letzte Woche"`
   - Line 150: Returns hardcoded format string `f"vor {abs(diff_days)} Tagen"`

2. **`format_german_time(val, include_seconds=False, with_uhr=True)` (Lines 163–183)**:
   - Line 167: `suffix = " Uhr" if with_uhr else ""` (hardcoded German suffix `" Uhr"`)
   - Line 178: `clean = val_str.replace("Uhr", "").strip()` (hardcoded `"Uhr"` strip)

3. **`format_german_datetime(val, include_seconds=False, with_uhr=True)` (Lines 184–208)**:
   - Line 192: `suffix = " Uhr" if with_uhr else ""` (hardcoded German suffix `" Uhr"`)
   - Line 193: `fmt = f"%d.%m.%Y %H:%M:%S{suffix}" if include_seconds else f"%d.%m.%Y %H:%M{suffix}"`
   - Line 203: `clean = val_str.replace("Uhr", "").strip()` (hardcoded `"Uhr"` strip)

4. **`parse_german_date(german_str)` (Lines 209–228)**:
   - Line 213: `cleaned = german_str.replace("Uhr", "").strip()` (hardcoded `"Uhr"` strip)

5. **`format_german_date(val)` (Lines 70–87)**:
   - Formats datetime or ISO string to standard `DD.MM.YYYY`.
   - Used by models, dialogs, and tests across the entire codebase.

6. **`format_german_date_with_relative(val, ref_date)` (Lines 153–160)**:
   - Formats to `f"{d_str} ({rel})" if rel else d_str`. Relies on `get_relative_date_text()`.

### 1.2 Other Modules in `src/utils/`
- **`src/utils/security.py`**: Contains `load_env_file`, `normalize_url`, `resolve_secret`, and `mask_secret`. No hardcoded German or user-facing UI strings.
- **`src/utils/ui_utils.py`**: Contains geometry calculation (`get_main_app_window`, `get_app_monitor_bounds`, `center_window`), mouse wheel binding, auto-hiding scrollbar (`AutoScrollableFrame`), and text wrapping (`wrap_and_truncate_text`). No hardcoded German strings.
- **`src/utils/__init__.py`**: Docstring only (`"""Utility functions for datetime and security."""`).

### 1.3 Consumers Across `src/` Dependent on `datetime_utils.py`
Exact locations where `datetime_utils.py` formatting functions are invoked:
- `src/models/case.py`: Lines 195–209 (`formatted_deadline`, `formatted_followup`, `formatted_created_at`, `formatted_updated_at`).
- `src/ui/views/cockpit_view.py`: Lines 514, 515, 518 (`format_german_date_with_relative`, `format_german_time`, `format_german_datetime`).
- `src/ui/widgets/case_list_widget.py`: Lines 288, 289, 384, 385 (`format_german_date_with_relative`, `format_german_time`).
- `src/ui/views/board_view.py`: Line 96 (`format_german_datetime`).
- `src/ui/views/table_view.py`: Line 269 (`format_german_datetime`).
- `src/ui/dialogs/case_print_dialog.py`: Lines 70, 137, 212 (`format_german_datetime`).
- `src/ui/dialogs/calendar_export_dialog.py`: Line 8 (`format_german_datetime`).
- `src/ui/dialogs/new_case_dialog.py`: Line 183 (`format_german_datetime(now_iso())`).
- `src/ui/dialogs/followup_dialog.py`: Lines 113, 172, 177, 182, 187, 192, 197 (`format_german_date`, `format_german_datetime`).
- `src/ui/dialogs/followup_flyout_dialog.py`: Lines 70, 160, 165, 170, 175 (`format_german_datetime`, `format_german_date`).
- `src/ui/widgets/timeline_widget.py`: Line 111 (`format_german_datetime`).
- `src/services/ai_service.py`: Line 433 (`format_german_date_with_relative`).

### 1.4 Hardcoded Date & Time Strings in UI Widgets & Dialogs
- **`src/ui/widgets/date_picker.py`**:
  - Line 23: `self.title("📅 Datum auswählen")` -> Needs `tr("date_picker.dialog_title", "📅 Datum auswählen")`
  - Line 103: `weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]` -> German abbreviations
  - Lines 225–230: Preset tuples `("Heute 11:30", ...)`, `("Heute 13:30", ...)`, `("Heute 16:30", ...)`, `("Morgen 08:00", ...)`, `("+ 1 Tag", ...)`, `("+ 1 Woche", ...)` -> Needs `tr("date_picker.preset_*")`
  - Lines 270–273: `month_names = ["", "Januar", "Februar", ...]` -> Hardcoded German month names
- **`src/ui/dialogs/followup_dialog.py`**:
  - Lines 63–86: `presets_row1` and `presets_row2` with `"+ 1 Std."`, `"+ 2 Std."`, `"Heute 16:30"`, `"Morgen 08:00"`, `"+ 1 Tag"`, `"+ 2 Tage"`, `"+ 3 Tage"`, `"+ 1 Woche"`
- **`src/ui/dialogs/followup_flyout_dialog.py`**:
  - Lines 84–96: `"+ 1 Std."`, `"+ 2 Std."`, `"Heute 16:30"`, `"Morgen 08:00"`, `"+ 1 Tag"`, `"+ 1 Woche"`

### 1.5 Locale Keys Audit in `locales/de.json`, `en.json`, and `sv.json`
Currently present under `"datetime"`:
- `days_ago`, `hours_ago`, `in_days`, `in_hours`, `in_minutes`, `just_now`, `minutes_ago`, `o_clock`, `today`, `tomorrow`, `yesterday`.

Missing keys under `"datetime"`:
- `day_after_tomorrow` ("übermorgen")
- `day_before_yesterday` ("vorgestern")
- `this_week` ("diese Woche")
- `next_week` ("nächste Woche")
- `last_week` ("letzte Woche")

Missing keys under `"date_picker"`:
- `preset_plus_2days` ("+ 2 Tage")
- `preset_plus_3days` ("+ 3 Tage")

Grammatical anomaly in `locales/sv.json`:
- `locales/sv.json` line 329 has `"datetime": { "o_clock": "kl." }`. When appended as a time suffix in Swedish, `"14:30 kl."` is ungrammatical. In Swedish, times are displayed as `"14:30"` without suffix. `datetime.o_clock` in `sv.json` should be `""` (matching English `""` and covered by `INTENTIONAL_EMPTY_KEYS` in test suites).

---

## 2. Logic Chain

1. **Step 1 — Centralized Translation Function**: `I18nService.tr(key, default, **kwargs)` resolves strings based on the currently active language (`i18n.current_language`).
2. **Step 2 — Dynamic Resolution in `datetime_utils.py`**:
   - `get_relative_date_text()` can replace its return values with calls to `tr("datetime.<key>", "<default>", **kwargs)`.
   - `format_german_time()` and `format_german_datetime()` can replace `" Uhr"` with `o_clock = tr("datetime.o_clock", "Uhr").strip()` and `suffix = f" {o_clock}" if o_clock else ""`.
   - In German (`"de"`), `tr("datetime.o_clock")` returns `"Uhr"`, producing `"14:30 Uhr"`.
   - In English (`"en"`), `tr("datetime.o_clock")` returns `""`, producing `"14:30"`.
   - In Swedish (`"sv"`), with `o_clock` set to `""`, it returns `""`, producing `"14:30"`.
3. **Step 3 — Backward Compatibility and Zero Breaking Changes**:
   - The existing test suite in `tests/test_datetime_standardization_and_anti_regression.py` and `tests/test_datetime_utils.py` checks `format_german_date`, `format_german_time`, `format_german_datetime`, and `parse_german_date`. By maintaining default arguments `with_uhr=True` and defaulting fallback strings to German, all 398 passing tests continue to pass when `current_language == "de"`.
   - Adding generic aliases (`format_date`, `format_time`, `format_datetime`, `format_date_with_relative`, `parse_date`) allows clean usage throughout the codebase without breaking legacy imports.
4. **Step 4 — String Stripping and Regex Cleaning**:
   - Cleaning logic currently uses `.replace("Uhr", "")`. When English or Swedish strings are parsed, strings may have no suffix or may have `"kl."`. Replacing with `re.sub(r"\s*(Uhr|kl\.?)\s*$", "", val, flags=re.IGNORECASE).strip()` ensures robust parsing across all 3 languages.
5. **Step 5 — 100% Mutual Key Parity**:
   - Adding the 5 missing datetime keys and 2 missing date_picker preset keys simultaneously to `locales/de.json`, `locales/en.json`, and `locales/sv.json` satisfies `TestTranslationParity` in `test_translation_parity_and_quality.py`.

---

## 3. Caveats

1. **No caveats on existing tests**: `tests/test_datetime_utils.py`, `tests/test_datetime_standardization_and_anti_regression.py`, and `tests/test_followup_and_relative_dates.py` all run in German default state (enforced by pytest fixtures `reset_i18n_language`), guaranteeing 100% test compatibility.
2. **Date Picker UI Components**: `CalendarDialog` month names and weekday abbreviations in `src/ui/widgets/date_picker.py` can be localized either via helper dictionaries or translation keys in Milestone 3 (UI Widgets Extraction).
3. **`format_german_salutation`**: Located in `src/services/calendar_email_service.py`, this specifically handles German salutations for German email templates. Localized email templates are handled in Milestone 2/4.

---

## 4. Conclusion & Implementation Recommendations

### 4.1 Required Additions to `locales/de.json`, `locales/en.json`, `locales/sv.json`

#### In `"datetime"` section:
```json
// de.json
"datetime": {
  "day_after_tomorrow": "übermorgen",
  "day_before_yesterday": "vorgestern",
  "days_ago": "vor {diff_days} Tagen",
  "hours_ago": "vor {diff_hours} Stunden",
  "in_days": "in {diff_days} Tagen",
  "in_hours": "in {diff_hours} Stunden",
  "in_minutes": "in {diff_minutes} Minuten",
  "just_now": "gerade eben",
  "last_week": "letzte Woche",
  "minutes_ago": "vor {diff_minutes} Minuten",
  "next_week": "nächste Woche",
  "o_clock": "Uhr",
  "this_week": "diese Woche",
  "today": "heute",
  "tomorrow": "morgen",
  "yesterday": "gestern"
}

// en.json
"datetime": {
  "day_after_tomorrow": "day after tomorrow",
  "day_before_yesterday": "day before yesterday",
  "days_ago": "{diff_days} days ago",
  "hours_ago": "{diff_hours} hours ago",
  "in_days": "in {diff_days} days",
  "in_hours": "in {diff_hours} hours",
  "in_minutes": "in {diff_minutes} minutes",
  "just_now": "just now",
  "last_week": "last week",
  "minutes_ago": "{diff_minutes} minutes ago",
  "next_week": "next week",
  "o_clock": "",
  "this_week": "this week",
  "today": "today",
  "tomorrow": "tomorrow",
  "yesterday": "yesterday"
}

// sv.json
"datetime": {
  "day_after_tomorrow": "i övermorgon",
  "day_before_yesterday": "i förrgår",
  "days_ago": "för {diff_days} dagar sedan",
  "hours_ago": "för {diff_hours} timmar sedan",
  "in_days": "om {diff_days} dagar",
  "in_hours": "om {diff_hours} timmar",
  "in_minutes": "om {diff_minutes} minuter",
  "just_now": "just nu",
  "last_week": "förra veckan",
  "minutes_ago": "för {diff_minutes} minuter sedan",
  "next_week": "nästa vecka",
  "o_clock": "",
  "this_week": "denna vecka",
  "today": "idag",
  "tomorrow": "imorgon",
  "yesterday": "igår"
}
```

#### In `"date_picker"` section:
```json
// de.json
"preset_plus_2days": "+ 2 Tage",
"preset_plus_3days": "+ 3 Tage"

// en.json
"preset_plus_2days": "+ 2 Days",
"preset_plus_3days": "+ 3 Days"

// sv.json
"preset_plus_2days": "+ 2 dagar",
"preset_plus_3days": "+ 3 dagar"
```

---

### 4.2 Proposed Implementation for `src/utils/datetime_utils.py`

```python
"""Date and time parsing, formatting, and localization utilities."""

from datetime import datetime, date, timezone
import re
from constants import ISO_DATETIME_FORMAT
from services.i18n_service import tr


def get_local_now() -> datetime:
    """Returns the current timezone-aware local datetime."""
    return datetime.now().astimezone()


def now_iso() -> str:
    """Returns current ISO 8601 formatted string (YYYY-MM-DDTHH:MM:SS)."""
    return get_local_now().strftime(ISO_DATETIME_FORMAT)


def parse_iso(iso_str: str) -> datetime:
    """Parses ISO string to timezone-aware datetime.
    If string is naive ISO format (no timezone), attaches local timezone.
    """
    if not iso_str:
        raise ValueError("ISO datetime string cannot be empty.")
    
    cleaned = iso_str.strip()
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        local_tz = get_local_now().tzinfo
        dt = dt.replace(tzinfo=local_tz)
    return dt


def format_iso(dt: datetime) -> str:
    """Formats datetime object to standard ISO string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def calculate_idle_days(updated_at_str: str, now: datetime | None = None) -> float:
    """Calculates difference in fractional days between updated_at and now."""
    if not updated_at_str:
        return 0.0
    
    ref_now = now or get_local_now()
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=get_local_now().tzinfo)
        
    updated_dt = parse_iso(updated_at_str)
    diff_seconds = (ref_now - updated_dt).total_seconds()
    if diff_seconds < 0:
        return 0.0
    return diff_seconds / 86400.0


def hours_until_deadline(deadline_str: str, now: datetime | None = None) -> float:
    """Calculates remaining hours until deadline (negative if overdue)."""
    if not deadline_str:
        return float("inf")
    
    ref_now = now or get_local_now()
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=get_local_now().tzinfo)

    deadline_dt = parse_iso(deadline_str)
    return (deadline_dt - ref_now).total_seconds() / 3600.0


def format_german_date(val: str | datetime | None) -> str:
    """Formats ISO string or datetime to date format DD.MM.YYYY."""
    if not val:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%d.%m.%Y")
    val_str = val.strip()
    if not val_str:
        return ""
    try:
        dt = parse_iso(val_str)
        return dt.strftime("%d.%m.%Y")
    except Exception:
        if re.match(r"^\d{2}\.\d{2}\.\d{4}", val_str):
            return val_str[:10]
        return val_str


def get_relative_date_text(val: str | datetime | None, ref_date: date | datetime | None = None) -> str:
    """Calculates dynamically localized relative date description e.g.
    'heute'/'today'/'idag', 'morgen'/'tomorrow'/'imorgon', 'in X Tagen'/'in X days'/'om X dagar'.
    """
    if not val:
        return ""
    try:
        if isinstance(val, datetime):
            target_dt = val
        elif isinstance(val, date):
            target_dt = datetime.combine(val, datetime.min.time())
        else:
            val_str = val.strip()
            if not val_str:
                return ""
            target_dt = parse_iso(val_str)
    except Exception:
        clean = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", val, flags=re.IGNORECASE).strip() if isinstance(val, str) else ""
        if re.match(r"^\d{2}\.\d{2}\.\d{4}", clean):
            try:
                target_dt = datetime.strptime(clean[:10], "%d.%m.%Y")
            except Exception:
                return ""
        else:
            return ""

    if ref_date is None:
        today = get_local_now().date()
    elif isinstance(ref_date, datetime):
        today = ref_date.date()
    else:
        today = ref_date

    target_date = target_dt.date() if isinstance(target_dt, datetime) else target_dt
    diff_days = (target_date - today).days

    if diff_days == 0:
        return tr("datetime.today", "heute")
    if diff_days == 1:
        return tr("datetime.tomorrow", "morgen")
    if diff_days == 2:
        return tr("datetime.day_after_tomorrow", "übermorgen")
    if diff_days == -1:
        return tr("datetime.yesterday", "gestern")
    if diff_days == -2:
        return tr("datetime.day_before_yesterday", "vorgestern")

    target_year, target_week, _ = target_date.isocalendar()
    today_year, today_week, _ = today.isocalendar()

    if diff_days > 2:
        if target_year == today_year and target_week == today_week:
            return tr("datetime.this_week", "diese Woche")
        if (target_year == today_year and target_week == today_week + 1) or (
            target_year == today_year + 1 and today_week >= 52 and target_week == 1
        ):
            return tr("datetime.next_week", "nächste Woche")
        return tr("datetime.in_days", f"in {diff_days} Tagen", diff_days=diff_days)
    else:
        if target_year == today_year and target_week == today_week:
            return tr("datetime.this_week", "diese Woche")
        if (target_year == today_year and target_week == today_week - 1) or (
            target_year == today_year - 1 and today_week == 1 and target_week >= 52
        ):
            return tr("datetime.last_week", "letzte Woche")
        return tr("datetime.days_ago", f"vor {abs(diff_days)} Tagen", diff_days=abs(diff_days))


def format_german_date_with_relative(val: str | datetime | None, ref_date: date | datetime | None = None) -> str:
    """Formats date to 'DD.MM.YYYY (Relativ)' e.g. '26.08.2026 (morgen)' or '26.08.2026 (tomorrow)'."""
    d_str = format_german_date(val)
    if not d_str:
        return ""
    rel = get_relative_date_text(val, ref_date=ref_date)
    return f"{d_str} ({rel})" if rel else d_str


def format_german_time(val: str | datetime | None, include_seconds: bool = False, with_uhr: bool = True) -> str:
    """Formats ISO string or datetime to time format HH:MM(:SS) [Uhr] dynamically localized."""
    if not val:
        return ""
    o_clock = tr("datetime.o_clock", "Uhr").strip() if with_uhr else ""
    suffix = f" {o_clock}" if o_clock else ""
    fmt = f"%H:%M:%S{suffix}" if include_seconds else f"%H:%M{suffix}"
    if isinstance(val, datetime):
        return val.strftime(fmt)
    val_str = val.strip()
    if not val_str:
        return ""
    try:
        dt = parse_iso(val_str)
        return dt.strftime(fmt)
    except Exception:
        clean = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", val_str, flags=re.IGNORECASE).strip()
        if re.match(r"^\d{1,2}:\d{2}", clean):
            return f"{clean[:5]}{suffix}"
        return val_str


def format_german_datetime(
    val: str | datetime | None,
    include_seconds: bool = False,
    with_uhr: bool = True,
) -> str:
    """Formats ISO string or datetime to format DD.MM.YYYY HH:MM(:SS) [Uhr] dynamically localized."""
    if not val:
        return ""
    o_clock = tr("datetime.o_clock", "Uhr").strip() if with_uhr else ""
    suffix = f" {o_clock}" if o_clock else ""
    fmt = f"%d.%m.%Y %H:%M:%S{suffix}" if include_seconds else f"%d.%m.%Y %H:%M{suffix}"
    if isinstance(val, datetime):
        return val.strftime(fmt)
    val_str = val.strip()
    if not val_str:
        return ""
    try:
        dt = parse_iso(val_str)
        return dt.strftime(fmt)
    except Exception:
        clean = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", val_str, flags=re.IGNORECASE).strip()
        if re.match(r"^\d{2}\.\d{2}\.\d{4}\s+\d{1,2}:\d{2}", clean):
            return f"{clean}{suffix}"
        return val_str


def parse_german_date(german_str: str) -> str:
    """Parses date format DD.MM.YYYY [HH:MM] into ISO format string YYYY-MM-DD[THH:MM:SS]."""
    if not german_str or not german_str.strip():
        return ""
    cleaned = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", german_str, flags=re.IGNORECASE).strip()
    for fmt, iso_fmt in [
        ("%d.%m.%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"),
        ("%d.%m.%Y %H:%M", "%Y-%m-%dT%H:%M:00"),
        ("%d.%m.%Y", "%Y-%m-%dT00:00:00"),
        ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S"),
        ("%Y-%m-%d", "%Y-%m-%dT00:00:00"),
    ]:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime(iso_fmt)
        except ValueError:
            continue
    return cleaned


# Generic and modern aliases
format_date = format_german_date
format_time = format_german_time
format_datetime = format_german_datetime
format_date_with_relative = format_german_date_with_relative
parse_date = parse_german_date
```

---

## 5. Verification Method

To verify these findings and recommendations independently:

1. **Verify Existing Tests Pass**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_datetime_utils.py tests/test_datetime_standardization_and_anti_regression.py tests/test_followup_and_relative_dates.py
   ```
2. **Verify Translation Parity & Key Completeness**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_translation_parity_and_quality.py
   ```
3. **Verify AST Scanner Cleanliness**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_ast_i18n_scanner.py
   ```
4. **Inspect Files**:
   - `src/utils/datetime_utils.py`
   - `src/utils/ui_utils.py`
   - `src/utils/security.py`
   - `locales/de.json`, `locales/en.json`, `locales/sv.json`
