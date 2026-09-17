"""Tests for Git hooks configuration and pre-push hook integrity."""

from pathlib import Path


def test_pre_push_hook_exists_and_configured():
    """Verify that .githooks/pre-push exists, is non-empty, and contains exe build and pytest commands."""
    project_root = Path(__file__).resolve().parent.parent
    hook_path = project_root / ".githooks" / "pre-push"

    assert hook_path.exists(), ".githooks/pre-push must exist in repository"
    content = hook_path.read_text(encoding="utf-8")

    # Verify building the exe via spec file
    assert "pyinstaller" in content.lower()
    assert "py-case-follow-up.spec" in content

    # Verify static typecheck via pyright
    assert "pyright" in content

    # Verify running tests
    assert "pytest" in content

    # Verify build step occurs before typecheck and test execution step
    build_idx = content.find("uv run pyinstaller")
    typecheck_idx = content.find("uvx pyright")
    test_idx = content.find("uv run pytest")
    assert build_idx != -1 and typecheck_idx != -1 and test_idx != -1
    assert build_idx < typecheck_idx < test_idx, "Executable build, typecheck, and test execution must follow proper order"
