# Adversarial Challenge Report — Milestone 2: System Constants, Enums, DateTime Utils, and Seed Services

## Verdict: REQUEST_CHANGES

---

## 1. Observation

1. **`LocalizedDict` Casing Fallback Bug in `src/services/i18n_service.py`**:
   - `LocalizedDict.__getitem__` (lines 128-137) and `LocalizedDict.get` (lines 139-148) use the following logic:
     ```python
     def __getitem__(self, key: str) -> str:
         default = super().get(key, str(key))
         try:
             res = tr(f"{self._prefix}.{key}", default=default)
             if res == default and isinstance(key, str):
                 alt_key = key.lower() if key.isupper() else key.upper()
                 res = tr(f"{self._prefix}.{alt_key}", default=default)
             return res
         except Exception:
             return default
     ```
   - When looking up `DISPLAY_ACTOR_NAMES["DATA_SUPPORT"]`:
     - Initial dict default: `"Data-AL Support / Hotline"`.
     - `locales/de.json` has `"actors.DATA_SUPPORT": "Data-AL Support / Hotline"`.
     - `tr("actors.DATA_SUPPORT", default=default)` returns `"Data-AL Support / Hotline"`.
     - Because `res == default` evaluates to `True`, `LocalizedDict` falsely assumes the key was not found and falls through to `tr("actors.data_support", default=default)`.
     - `locales/de.json` (and `en.json`, `sv.json`) contains `"actors.data_support": "Support"`.
     - `DISPLAY_ACTOR_NAMES["DATA_SUPPORT"]` returns `"Support"` instead of `"Data-AL Support / Hotline"` across all 3 languages.
   - Affected keys verified empirically:
     - `DISPLAY_ACTOR_NAMES["DATA_SUPPORT"]` -> returns `"Support"` (expected `"Data-AL Support / Hotline"`).
     - `DISPLAY_ACTOR_NAMES["DATA_HOTLINE"]` -> returns `"Hotline"` (expected `"Data-AL Hotline"`).
     - `DISPLAY_ACTOR_NAMES["DATA_DEVELOPMENT"]` -> returns `"Entwicklung"` (expected `"Data-AL Entwicklung"` in DE).
     - `DISPLAY_ACTOR_NAMES["DATA_TECH"]` -> returns `"Technik"` (expected `"Data-AL Technik"` in DE).
     - `DISPLAY_ACTOR_NAMES["DATA_CUSTOMER"]` -> returns `"Kunde"` (expected `"Data-AL Kunde"` in DE).
     - `DISPLAY_LAYOUT_NAMES["TABLE"]` -> returns `"Tabelle & Details (Sortiermatrix)"` (expected `"Tabelle & Details (Sortier-Matrix)"` in DE).

2. **`get_relative_date_text` Verification in `src/utils/datetime_utils.py`**:
   - Tested across all specified relative date targets in German (`de`), English (`en`), and Swedish (`sv`):
     - `yesterday` (-1 day): `"gestern"` (DE), `"yesterday"` (EN), `"igår"` (SV) -> **PASS**
     - `today` (0 days): `"heute"` (DE), `"today"` (EN), `"idag"` (SV) -> **PASS**
     - `tomorrow` (+1 day): `"morgen"` (DE), `"tomorrow"` (EN), `"imorgon"` (SV) -> **PASS**
     - `day_before_yesterday` (-2 days): `"vorgestern"` (DE), `"day before yesterday"` (EN), `"i förrgår"` (SV) -> **PASS**
     - `day_after_tomorrow` (+2 days): `"übermorgen"` (DE), `"day after tomorrow"` (EN), `"i övermorgon"` (SV) -> **PASS**
     - `this_week` (same ISO week, diff > 2 or < -2): `"diese Woche"` (DE), `"this week"` (EN), `"denna vecka"` (SV) -> **PASS**
     - `next_week` (ISO week + 1): `"nächste Woche"` (DE), `"next week"` (EN), `"nästa vecka"` (SV) -> **PASS**
     - `last_week` (ISO week - 1): `"letzte Woche"` (DE), `"last week"` (EN), `"förra veckan"` (SV) -> **PASS**
     - ISO calendar year boundaries (e.g. week 52/53 to week 1 transitions) -> **PASS**

3. **Dynamic Language Switch Behavior**:
   - `DISPLAY_BOARD_COLUMN_NAMES` reflects language changes immediately (`"Neu"` -> `"New"` -> `"Nytt"`).
   - `DISPLAY_CHANNEL_NAMES` reflects language changes immediately (`"Eingehender Telefonanruf"` -> `"Inbound Phone Call"` -> `"Inkommande telefonsamtal"`).
   - `DISPLAY_ACTOR_NAMES` reflects language changes immediately for primary keys (`"SUPPORT"`, `"DEVELOPMENT"`, `"TECH"`, `"CUSTOMER"`), but `DATA_*` keys suffer from the casing clobbering bug identified above.

4. **Test Suite Execution**:
   - Milestone 2 targeted tests: `.venv\Scripts\python.exe -m pytest tests/test_m2_constants_enums_datetime.py tests/test_dynamic_language_switch.py -v` -> 23 passed in 1.57s.
   - Full repository test suite: 408 passed in 142.92s.

---

## 2. Logic Chain

1. *Observation*: The initial dictionary supplied to `LocalizedDict` contains default German strings.
2. *Observation*: In German (`locales/de.json`), the translated string for a key is often identical to the default German string.
3. *Observation*: `LocalizedDict` checks `if res == default:` to decide whether to attempt looking up `alt_key` (the lowercased or uppercased key name).
4. *Deduction*: When `res == default` is evaluated for any exact-match German translation (or matching fallback translation), it evaluates to `True`, falsely concluding that no translation exists for `key`.
5. *Deduction*: It then queries `alt_key` (`data_support`, `data_hotline`, etc.). Because distinct lowercase keys exist in the locale files with shorter values, `LocalizedDict` silently returns the lowercase translation instead of the correct uppercase translation.
6. *Conclusion*: `LocalizedDict` requires a deterministic missing-key detection mechanism (e.g., using a missing sentinel object or inspecting key existence in `I18nService`) so that casing fallback only occurs when the original key is genuinely absent from the translations.

---

## 3. Caveats

- All unit tests in `tests/test_m2_constants_enums_datetime.py` and `tests/test_dynamic_language_switch.py` currently pass because existing assertions only checked top-level keys like `NEW`, `ACTION_REQUIRED`, `SUPPORT`, `save`, `profile_saved`, etc., without checking `DATA_*` actor variants or compound layout keys.
- DateTime utils, SeedService, SeedCaseData, and SnippetService are well-formed, fully localized, and passed all edge cases across DE, EN, and SV.

---

## 4. Conclusion

Milestone 2 cannot be approved in its current state due to the false-positive casing fallback bug in `LocalizedDict` (`src/services/i18n_service.py`), which clobbers `DISPLAY_ACTOR_NAMES` `DATA_*` keys and `DISPLAY_LAYOUT_NAMES["TABLE"]`.

**Required Action for Worker**:
Fix `LocalizedDict.__getitem__` and `LocalizedDict.get` in `src/services/i18n_service.py` to check for key existence / use a sentinel object rather than `if res == default:`, ensuring exact-case matches are preserved when translations equal default values. Add a unit test verifying `DISPLAY_ACTOR_NAMES["DATA_SUPPORT"] == "Data-AL Support / Hotline"` across DE, EN, and SV.

---

## 5. Verification Method

Run the following command to reproduce the bug:
```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from services.i18n_service import get_i18n; from constants import DISPLAY_ACTOR_NAMES; i18n = get_i18n(); i18n.current_language = 'de'; print('Expected: Data-AL Support / Hotline'); print('Actual:', DISPLAY_ACTOR_NAMES['DATA_SUPPORT']); assert DISPLAY_ACTOR_NAMES['DATA_SUPPORT'] == 'Data-AL Support / Hotline'"
```
Expected after fix: Assertion succeeds across `de`, `en`, and `sv`.

Run test suites:
```powershell
.venv\Scripts\python.exe -m pytest tests/test_m2_constants_enums_datetime.py tests/test_dynamic_language_switch.py -v
```
