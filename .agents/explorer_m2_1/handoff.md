# Milestone 2 Technical Investigation Report: System Constants & Enums Localization

## 1. Observation

Direct code inspection of `src/constants.py`, `src/enums.py`, `src/services/i18n_service.py`, `src/utils/datetime_utils.py`, and `locales/*.json` revealed the following exact facts and line locations:

### 1.1 `src/constants.py`
- **Lines 13–23**: `DISPLAY_CHANNEL_NAMES` is defined as a static Python `dict` with German strings (`"Telefon (Eingang)"`, `"Interne Notiz"`, etc.) before `LocalizedDict` is declared.
- **Lines 25–36**: `DISPLAY_ACTOR_NAMES` is defined as a static Python `dict` with German strings (`"Support / Hotline"`, `"Entwicklung"`, `"Technik"`, `"Kunde"`, etc.).
- **Lines 38–43**: `DISPLAY_LAYOUT_NAMES` is defined as a static Python `dict` (`"Cockpit (Hauptansicht)"`, `"Kanban-Board (Zuständigkeiten)"`, etc.).
- **Lines 45–51**: `DISPLAY_BOARD_COLUMN_NAMES` is defined as a static Python `dict` (`"Neu"`, `"Aktion erforderlich"`, `"Warten auf zuständige Stelle"`, `"In Bearbeitung"`, `"Erledigt"`).
- **Lines 56–76**: `LocalizedDict` is defined in `constants.py`. It overrides `__getitem__` and `get`, but does NOT override `.values()` or `.items()`.
  - In `src/ui/views/cockpit_layout_builders.py:221`: `self.actor_combo = ctk.CTkOptionMenu(..., values=list(ACTOR_DISPLAY.values()), ...)` calls `.values()`, which on standard dict returns static unlocalized strings.
- **Lines 79–107**: `DIALOG_TITLES` is wrapped with `LocalizedDict("dialog_titles", {...})` (27 dialog keys).
- **Lines 110–112**: `DIALOG_HEADERS` is wrapped with `LocalizedDict("dialog_headers", {...})`.
- **Lines 115–145**: Menu dropdown options are provided via functions `get_localized_menu_options_stammdaten()`, `get_localized_menu_options_vorlagen()`, `get_localized_menu_options_datenaustausch()`.
- **Lines 148–171**: `UI_BUTTON_TEXTS` is wrapped with `LocalizedDict("ui_buttons", {...})`.
- **Lines 174–188**: `STATUS_MESSAGES` is wrapped with `LocalizedDict("status_messages", {...})`.
- **Lines 191–210**: `VALIDATION_MESSAGES` is a static Python `dict` with 18 validation messages (`"snippet_id_required"`, `"customer_id_required"`, `"timeline_timestamp_required"`, `"username_required"`, etc.) used across `src/models/case.py`, `src/models/customer.py`, `src/models/profile.py`, `src/models/schema.py`, and `src/models/snippet.py`. None of these 18 keys exist in `locales/de.json`, `locales/en.json`, or `locales/sv.json`.
- **Lines 571–585**: `HOTKEY_ACTION_LABELS` is a list of tuples `[("new_case", "Neuer Fall:"), ...]`. The 13 keys match keys in `locales/*.json` under `"hotkey_actions"`.
- **Lines 587–603**: Hotkey recorder and macro UI strings (`HOTKEY_RECORDER_TITLE`, `STATUS_SHORTCUT_CONFLICT`, `LABEL_APP_SHORTCUTS_HEADER`, `TOAST_SNIPPET_MACRO_TITLE`, etc.) are hardcoded string constants.

### 1.2 `src/enums.py`
- **Lines 4–57**: Enum classes (`UrgencyLevel`, `BoardColumn`, `Actor`, `FieldType`, `SyncMode`, `TargetType`, `Channel`, `LayoutMode`) inherit from `StrEnum`.
- **Lines 66–69**: Aliases `CHANNEL_DISPLAY = DISPLAY_CHANNEL_NAMES`, `ACTOR_DISPLAY = DISPLAY_ACTOR_NAMES`, `LAYOUT_DISPLAY = DISPLAY_LAYOUT_NAMES`, `BOARD_COLUMN_DISPLAY = DISPLAY_BOARD_COLUMN_NAMES`.
- **Lines 72–109**: Helper functions `get_channel_display()`, `get_actor_display()`, `get_layout_display()`, `get_board_column_display()` dynamically call `tr(...)` with key mappings (`"channels.phone"`, `"actors.support_team"`, `"layouts.cockpit"`, etc.).
- **Lines 111–130**: Reverse lookups `get_actor_val_from_display()`, `get_channel_val_from_display()`, `get_layout_val_from_display()`.

### 1.3 `src/services/i18n_service.py`
- `I18nService` implements dynamic language switching with listener registration and a 4-step fallback chain (`current_language` -> `"de"` -> `default` -> `key`).
- `LocalizedDict` is currently in `src/constants.py` rather than `src/services/i18n_service.py`.

### 1.4 `src/utils/datetime_utils.py`
- **Lines 89–151**: `get_relative_date_text()` hardcodes German relative date strings (`"heute"`, `"morgen"`, `"übermorgen"`, `"gestern"`, `"vorgestern"`, `"diese Woche"`, `"nächste Woche"`, `"letzte Woche"`, `"in X Tagen"`, `"vor X Tagen"`).
- `locales/de.json`, `en.json`, `sv.json` already have `"datetime"` sections with `today`, `tomorrow`, `yesterday`, `in_days`, `days_ago`, `o_clock`, but lack keys for `day_after_tomorrow`, `day_before_yesterday`, `this_week`, `next_week`, `last_week`.

---

## 2. Logic Chain

1. **Dynamic Resolution without Module Reloading**:
   When UI components (such as `CTkOptionMenu` or table headers) read `DISPLAY_*` constants at runtime or during UI refresh events, static dictionary lookups return the initial language unless wrapped in a dict proxy (`LocalizedDict`).
   Wrapping `DISPLAY_BOARD_COLUMN_NAMES`, `DISPLAY_ACTOR_NAMES`, `DISPLAY_CHANNEL_NAMES`, `DISPLAY_LAYOUT_NAMES`, and `VALIDATION_MESSAGES` with `LocalizedDict` ensures `d[k]`, `d.get(k)`, `d.values()`, and `d.items()` evaluate `tr(f"{prefix}.{k}")` on every access.

2. **Dict Interface Completeness**:
   In `src/ui/views/cockpit_layout_builders.py:221`, `list(ACTOR_DISPLAY.values())` is used to populate dropdown options. For `LocalizedDict` to return translated values, `.values()` must be implemented as `[self[k] for k in self.keys()]`, and `.items()` as `[(k, self[k]) for k in self.keys()]`.

3. **Key Parity in Locale Files**:
   For `LocalizedDict("actors", ...)` and `LocalizedDict("channels", ...)` to resolve uppercase enum keys directly (e.g. `ACTOR_DISPLAY[Actor.DEVELOPMENT]`), the uppercase keys (`DEVELOPMENT`, `SUPPORT`, `TECH`, `CUSTOMER`, `PHONE_INBOUND`, etc.) must exist in `locales/de.json`, `locales/en.json`, and `locales/sv.json`.
   Likewise, `VALIDATION_MESSAGES` contains 18 keys that must be added to all 3 locale files under `"validation_messages"`.

4. **Preserving Backward Compatibility & Existing Tests**:
   Tests in `tests/test_dynamic_language_switch.py`, `tests/test_translation_parity_and_quality.py`, `tests/test_ast_i18n_scanner.py`, and `tests/test_e2e_multilingual_workflows.py` already assert exact translations for `DIALOG_TITLES`, `UI_BUTTON_TEXTS`, `STATUS_MESSAGES`, `COL_TITLE_MAP`, and enum helpers across DE, EN, and SV. Providing default fallbacks in `LocalizedDict` ensures that if a key is accessed before i18n is initialized, it safely returns the German default string.

---

## 3. Caveats

1. **Case Sensitivity in Enums vs Locales**:
   Some locale sections historically use lowercase keys (`actors.dev`, `channels.phone`), while enums use uppercase (`Actor.DEVELOPMENT`, `Channel.PHONE_INBOUND`). `LocalizedDict` should implement fallback normalization (`key`, `key.lower()`, `key.upper()`) and locale files should include direct uppercase enum keys to ensure 100% seamless lookups.
2. **Seed and Model Validation Invariants**:
   Model validation methods (`Case.validate()`, `Customer.validate()`, `Snippet.validate()`, etc.) return strings from `VALIDATION_MESSAGES`. Tests checking `len(errors) == 3` will continue to pass seamlessly because error list lengths are invariant to the translated string content.
3. **No Direct Source Modification during Investigation**:
   In accordance with the Explorer archetype, this report provides concrete code diffs and recommendations without modifying source files.

---

## 4. Conclusion & Implementation Recommendations

### 4.1 Recommended `LocalizedDict` Architecture (in `src/services/i18n_service.py` & `src/constants.py`)

```python
class LocalizedDict(dict):
    """Dictionary proxy that dynamically translates keys using I18nService."""
    def __init__(self, prefix: str, initial_dict: dict[str, str]):
        super().__init__(initial_dict)
        self._prefix = prefix

    def __getitem__(self, key: str) -> str:
        default = super().get(key, key)
        try:
            from services.i18n_service import tr
            res = tr(f"{self._prefix}.{key}", default=default)
            if res == default and isinstance(key, str):
                # Try lowercase / uppercase fallback
                alt_key = key.lower() if key.isupper() else key.upper()
                res = tr(f"{self._prefix}.{alt_key}", default=default)
            return res
        except Exception:
            return default

    def get(self, key: str, default: Any = None) -> Any:
        try:
            from services.i18n_service import tr
            fallback = super().get(key, default)
            res = tr(f"{self._prefix}.{key}", default=fallback if fallback is not None else key)
            if res == fallback and isinstance(key, str):
                alt_key = key.lower() if key.isupper() else key.upper()
                res = tr(f"{self._prefix}.{alt_key}", default=fallback if fallback is not None else key)
            return res
        except Exception:
            return super().get(key, default)

    def values(self):
        return [self[k] for k in self.keys()]

    def items(self):
        return [(k, self[k]) for k in self.keys()]
```

### 4.2 Required Changes in `src/constants.py`

1. **Move `LocalizedDict` definition to the top of `src/constants.py`** (or import from `services.i18n_service`).
2. **Wrap Core Constants with `LocalizedDict`**:
   - `DISPLAY_CHANNEL_NAMES = LocalizedDict("channels", {...})` (lines 13–23)
   - `DISPLAY_ACTOR_NAMES = LocalizedDict("actors", {...})` (lines 25–36)
   - `DISPLAY_LAYOUT_NAMES = LocalizedDict("layouts", {...})` (lines 38–43)
   - `DISPLAY_BOARD_COLUMN_NAMES = LocalizedDict("board_columns", {...})` (lines 45–51)
   - `VALIDATION_MESSAGES = LocalizedDict("validation_messages", {...})` (lines 191–210)
3. **Hotkey Action Labels**:
   - Provide `HOTKEY_ACTION_LABELS_MAP = LocalizedDict("hotkey_actions", dict(HOTKEY_ACTION_LABELS))`
   - Provide `get_localized_hotkey_action_labels() -> list[tuple[str, str]]`

### 4.3 Required Changes in `src/enums.py`

Update `get_channel_display()`, `get_actor_display()`, `get_layout_display()`, and `get_board_column_display()` to directly utilize `CHANNEL_DISPLAY`, `ACTOR_DISPLAY`, `LAYOUT_DISPLAY`, and `BOARD_COLUMN_DISPLAY` dynamic lookups.

### 4.4 Required Changes in `src/utils/datetime_utils.py`

Update `get_relative_date_text()` to use `tr(...)` calls:
- `"heute"` -> `tr("datetime.today", "heute")`
- `"morgen"` -> `tr("datetime.tomorrow", "morgen")`
- `"übermorgen"` -> `tr("datetime.day_after_tomorrow", "übermorgen")`
- `"gestern"` -> `tr("datetime.yesterday", "gestern")`
- `"vorgestern"` -> `tr("datetime.day_before_yesterday", "vorgestern")`
- `"diese Woche"` -> `tr("datetime.this_week", "diese Woche")`
- `"nächste Woche"` -> `tr("datetime.next_week", "nächste Woche")`
- `"letzte Woche"` -> `tr("datetime.last_week", "letzte Woche")`
- `f"in {diff_days} Tagen"` -> `tr("datetime.in_days", f"in {diff_days} Tagen", diff_days=diff_days)`
- `f"vor {abs(diff_days)} Tagen"` -> `tr("datetime.days_ago", f"vor {abs(diff_days)} Tagen", diff_days=abs(diff_days))`

### 4.5 Required Locale Keys in `locales/de.json`, `en.json`, `sv.json`

Add the following synchronized sections and keys to `locales/de.json`, `locales/en.json`, `locales/sv.json`:

1. **`validation_messages`**: 18 keys (`snippet_id_required`, `contact_name_required`, `customer_id_required`, `practice_name_required`, `timeline_timestamp_required`, `timeline_author_required`, `schema_id_required`, `title_required`, `username_required`, `name_required`, `field_id_required`, `label_required`, `schema_id_caps_required`, `display_name_required`, etc.).
2. **`actors`**: Uppercase keys (`SUPPORT`, `HOTLINE`, `DEVELOPMENT`, `TECH`, `CUSTOMER`, `DATA_SUPPORT`, `DATA_HOTLINE`, `DATA_DEVELOPMENT`, `DATA_TECH`, `DATA_CUSTOMER`).
3. **`channels`**: Uppercase keys (`INTERNAL_NOTE`, `EMAIL`, `DEV_TICKET`, `OTHER`, `PHONE_INBOUND`, `PHONE_OUTBOUND`, `EMAIL_IN`, `EMAIL_OUT`).
4. **`layouts`**: Uppercase keys (`COCKPIT`, `BOARD`, `TABLE`, `ANALYTICS`).
5. **`datetime`**: Relative date keys (`day_after_tomorrow`, `day_before_yesterday`, `this_week`, `next_week`, `last_week`).
6. **`shortcuts`**: UI headers and messages (`app_shortcuts_header`, `snippet_shortcuts_header`, `no_snippets`, `snippet_shortcut_field`, `toast_macro_title`, `toast_no_focus`, `conflict`, `conflict_generic`).

---

## 5. Verification Method

To independently verify these recommendations during Milestone 2 implementation:

1. **Run dynamic language switch test suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests\test_dynamic_language_switch.py
   ```
2. **Run translation parity and token validation test suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests\test_translation_parity_and_quality.py
   ```
3. **Run relative date & datetime utils test suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests\test_datetime_utils.py tests\test_followup_and_relative_dates.py
   ```
4. **Run AST i18n scanner and E2E workflow test suites**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests\test_ast_i18n_scanner.py tests\test_e2e_multilingual_workflows.py
   ```
5. **Inspect `src/constants.py` and `src/enums.py`**:
   Verify that `DISPLAY_BOARD_COLUMN_NAMES`, `DISPLAY_ACTOR_NAMES`, `DISPLAY_CHANNEL_NAMES`, `DISPLAY_LAYOUT_NAMES`, and `VALIDATION_MESSAGES` are instances of `LocalizedDict`.
