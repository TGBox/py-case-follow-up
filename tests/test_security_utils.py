"""Tests for security utilities: .env loading, URL normalization, secret resolution, and masking."""

import os
from pathlib import Path
from utils.security import load_env_file, mask_secret, normalize_url, resolve_secret


def test_load_env_file(tmp_path: Path, monkeypatch):
    """Verify load_env_file loads variables, strips quotes, and ignores comments."""
    # 1. Non-existent file and directory (exception branch)
    load_env_file(tmp_path / "does_not_exist.env")
    # Passing directory instead of file triggers read exception handled by except block
    load_env_file(tmp_path)

    # 2. None path (cwd fallback)
    monkeypatch.chdir(tmp_path)
    load_env_file(None)

    # 3. Create real .env file with various formats
    env_content = (
        "# Comment line\n"
        "\n"
        "INVALID_LINE_NO_EQUALS\n"
        "=VALUE_WITHOUT_KEY\n"
        "TEST_KEY_PLAIN=simple_value\n"
        "TEST_KEY_DQUOTES=\"double_quoted\"\n"
        "TEST_KEY_SQUOTES='single_quoted'\n"
        "  TEST_KEY_SPACES  =   spaced_value   \n"
        "EMPTY_KEY=\n"
    )
    env_file = tmp_path / ".env"
    env_file.write_text(env_content, encoding="utf-8")

    load_env_file(env_file)

    assert os.environ.get("TEST_KEY_PLAIN") == "simple_value"
    assert os.environ.get("TEST_KEY_DQUOTES") == "double_quoted"
    assert os.environ.get("TEST_KEY_SQUOTES") == "single_quoted"
    assert os.environ.get("TEST_KEY_SPACES") == "spaced_value"
    assert os.environ.get("EMPTY_KEY") == ""


def test_normalize_url():
    """Verify normalize_url strips markdown link format and trailing slashes."""
    assert normalize_url("") == ""
    assert normalize_url("   ") == ""
    assert normalize_url(None) == ""  # type: ignore

    # Markdown format
    assert normalize_url("[BookStack](https://wiki.intern.lan/api/)") == "https://wiki.intern.lan/api"
    assert normalize_url("[Dokumentation](http://localhost:8080)") == "http://localhost:8080"

    # Regular URLs with trailing slashes
    assert normalize_url("https://support.praxis.de/") == "https://support.praxis.de"
    assert normalize_url("https://support.praxis.de///") == "https://support.praxis.de"
    assert normalize_url("http://192.168.1.100:8000/api") == "http://192.168.1.100:8000/api"


def test_resolve_secret(monkeypatch):
    """Verify resolve_secret returns direct strings or reads from environment variables."""
    assert resolve_secret("") == ""

    # Direct literal
    assert resolve_secret("plain_secret_value") == "plain_secret_value"

    # ENV_ prefix where variable exists
    monkeypatch.setenv("MY_OLLAMA_KEY", "secret_ollama_123")
    assert resolve_secret("ENV_MY_OLLAMA_KEY") == "secret_ollama_123"

    # ENV_ prefix where key is set with ENV_ prefix itself
    monkeypatch.setenv("ENV_FULL_KEY", "secret_full_456")
    assert resolve_secret("ENV_FULL_KEY") == "secret_full_456"

    # ENV_ prefix not in environment
    assert resolve_secret("ENV_NON_EXISTENT") == ""


def test_mask_secret():
    """Verify mask_secret masks secrets safely."""
    assert mask_secret("") == "<EMPTY>"
    assert mask_secret(None) == "<EMPTY>"  # type: ignore
    assert mask_secret("a") == "****"
    assert mask_secret("ab") == "****"
    assert mask_secret("abcd") == "****"
    assert mask_secret("12345") == "12****45"
    assert mask_secret("super_secret_token_value_99") == "su****99"
