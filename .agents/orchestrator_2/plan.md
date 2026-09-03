# Plan: Multi-Language Translation & Localization

## Objective
Execute full i18n implementation and verification according to ORIGINAL_REQUEST.md:
1. **Milestone 1 Gate**: Verify locale key parity, format tokens, natural translations in EN and SV.
2. **Milestone 2**: System, Constants, Enums, Utils, and Seed Services localization with dynamic `LocalizedDict` proxies.
3. **Milestone 3**: UI Views & Widgets string extraction to `tr(...)`.
4. **Milestone 4**: UI Dialogs string extraction to `tr(...)`.
5. **Milestone 5**: Dynamic Language Switching runtime integration across all views/dialogs without restart.
6. **Milestone 6**: Full test suite pass (`.venv\Scripts\python.exe -m pytest`) & AST verification.

## Execution Strategy
- Standard dispatch loop: Explorers -> Worker -> Reviewers -> Challengers -> Auditor -> Gate check.
- Update `GATE_STATUS.md` and `PROJECT.md` at each step.
