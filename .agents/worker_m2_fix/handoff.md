# Handoff Report: Milestone 2 LocalizedDict False Fallback Remediation

## 1. Observation
- In `src/services/i18n_service.py` (prior to fix), `LocalizedDict.__getitem__` and `LocalizedDict.get` determined whether a translation was missing by testing `if res == default:` and `if res == fallback:`.
- In `locales/de.json`, `en.json`, and `sv.json`, translations for keys such as `actors.DATA_SUPPORT` (`"Data-AL Support / Hotline"`), `actors.DATA_HOTLINE` (`"Data-AL Hotline"`), `actors.DATA_DEVELOPMENT` (`"Data-AL Entwicklung"`), `actors.DATA_TECH` (`"Data-AL Technik"`), `actors.DATA_CUSTOMER` (`"Data-AL Kunde"`), and `layouts.TABLE` (`"Tabelle & Details (Sortier-Matrix)"`) are identical to the default values specified in the `LocalizedDict` initial dictionary in `src/constants.py`.
- Because `res == default` evaluated to `True`, `LocalizedDict` falsely inferred that the key was missing from the active locale and triggered the secondary fallback: `alt_key = key.lower() if key.isupper() else key.upper()`.
- For `DISPLAY_ACTOR_NAMES["DATA_SUPPORT"]`, this caused a second lookup for `"actors.data_support"`, which resolved to `"Support"` instead of `"Data-AL Support / Hotline"`. Similarly, `DATA_HOTLINE` fell through to `"Hotline"`, `DATA_DEVELOPMENT` to `"Entwicklung"`, `DATA_TECH` to `"Technik"`, `DATA_CUSTOMER` to `"Kunde"`, and `DISPLAY_LAYOUT_NAMES["TABLE"]` to `"Tabelle & Details (Sortiermatrix)"`.

## 2. Logic Chain
1. A unique sentinel object `_SENTINEL = object()` was defined in `src/services/i18n_service.py`.
2. `I18nService.tr` was updated so that when a translation key is not found in either the active language or German, `tr` returns the passed `default` object unchanged (rather than converting non-string sentinels via `str()`).
3. In `LocalizedDict.__getitem__` and `LocalizedDict.get`, lookups now pass `default=_SENTINEL`.
4. Only when `res is _SENTINEL` (indicating that the primary key does not exist in any loaded locale) does `LocalizedDict` attempt the alternative-cased key lookup (`alt_key = key.lower() if key.isupper() else key.upper()`, also with `default=_SENTINEL`).
5. If the translation exists—even when identical to the default dictionary value—`res` is a non-sentinel string and is returned immediately without triggering the fallback.
6. When neither key variation exists in the translations, `LocalizedDict` returns the original dictionary default value or caller-provided fallback.

## 3. Caveats
- No caveats. The sentinel pattern is backward compatible with all existing dictionary proxy accesses (`d[k]`, `d.get(k)`, `d.values()`, `d.items()`, and iteration).

## 4. Conclusion
- The issue where `LocalizedDict` falsely triggered fallback resolution on matching translations is resolved.
- Looking up all keys in `DISPLAY_ACTOR_NAMES`, `DISPLAY_LAYOUT_NAMES`, `DISPLAY_CHANNEL_NAMES`, and `DISPLAY_BOARD_COLUMN_NAMES` in DE, EN, and SV now returns full, uncorrupted, and untruncated translations.
- All 80 Milestone 2 tests and all 436 tests across the entire application pass without errors or regressions.

## 5. Verification Method
1. Run Milestone 2 specific test suites:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_m2_constants_enums_datetime.py tests/test_dynamic_language_switch.py tests/test_translation_parity_and_quality.py tests/test_adversarial_m2_seed_snippet_stress.py -v
   ```
2. Verify all display constants across languages directly:
   ```powershell
   .venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from constants import DISPLAY_ACTOR_NAMES, DISPLAY_LAYOUT_NAMES, DISPLAY_CHANNEL_NAMES, DISPLAY_BOARD_COLUMN_NAMES; from services.i18n_service import get_i18n; [setattr(get_i18n(), 'current_language', lang) or print(f'=== {lang} ===') or [print(k, DISPLAY_ACTOR_NAMES[k]) for k in DISPLAY_ACTOR_NAMES] for lang in ['de', 'en', 'sv']]"
   ```
3. Run complete project test suite:
   ```powershell
   .venv\Scripts\python.exe -m pytest
   ```
