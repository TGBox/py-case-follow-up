# Orchestrator Plan

## Goal
Extract and translate all untranslated hardcoded strings across all application files in `src/` into English and Swedish, ensuring key parity across `locales/de.json`, `locales/en.json`, `locales/sv.json`, dynamic language switching support, AST verification, and 100% pytest pass rate.

## Phases

### Phase 0: Codebase Survey
- Spawn 3 parallel Explorers to survey:
  - Explorer 1 (Translation Infra & Locales): Current i18n architecture (`tr(...)`, language switcher, event bus, `locales/*.json` current keys, gaps, LocalizedDict).
  - Explorer 2 (Codebase String Inventory & Extraction Targets): All modules in `src/` (views, widgets, dialogs, constants, enums, schemas, seed cases) for hardcoded strings and dynamic reload hooks.
  - Explorer 3 (Test Infrastructure & Verification Tools): Existing pytest suite, AST scan capabilities, translation parity checker, and E2E test harness requirements.

### Phase 1: Decomposition & Global Index (PROJECT.md & TEST_INFRA.md)
- Synthesize findings into `PROJECT.md` (Architecture, Feature Inventory, Milestones, Interface Contracts, Code Layout)
- Establish E2E Testing Plan & Track (`TEST_INFRA.md`)

### Phase 2: Dual-Track Execution
- Track A: E2E Testing Track (Automated parity verification script/tests, AST string extraction scanner, runtime dynamic switching tests, and comprehensive test suite)
- Track B: Implementation Milestones (Infra & Locales, Constants/Enums/Schemas/Seed Data, UI Views/Widgets/Dialogs, Dynamic Language Switching Integration)
- Final Milestone: Pass 100% E2E test suite + adversarial coverage hardening

### Phase 3: Final Verification & Handover
- Complete gate verification (Reviewers, Challengers, Auditor)
- Full completion report to Sentinel
