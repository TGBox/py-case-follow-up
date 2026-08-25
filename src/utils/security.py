import os
import re
from pathlib import Path


def load_env_file(env_path: Path | str | None = None) -> None:
    """Loads environment variables from a .env file into os.environ if present."""
    if env_path is None:
        target_path = Path.cwd() / ".env"
    else:
        target_path = Path(env_path)

    if not target_path.exists():
        return

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key:
                    os.environ[key] = value
    except Exception:
        pass


def normalize_url(url_str: str) -> str:
    """Normalizes URL string, stripping markdown link wrappers if present."""
    if not url_str:
        return ""
    
    cleaned = url_str.strip()
    # Match markdown link pattern [text](url)
    md_match = re.match(r"^\[.*?\]\((https?://[^\s)]+)\)$", cleaned)
    if md_match:
        return md_match.group(1).rstrip("/")
    
    # Strip trailing slash
    return cleaned.rstrip("/")


def resolve_secret(secret_ref: str) -> str:
    """Resolves secret from environment variable if prefixed with ENV_,
    otherwise returns value directly. Never log the returned secret!
    """
    if not secret_ref:
        return ""
    
    if secret_ref.startswith("ENV_"):
        env_var_name = secret_ref[4:]
        val = os.environ.get(env_var_name, "") or os.environ.get(secret_ref, "")
        return val
    
    return secret_ref


def mask_secret(secret_val: str) -> str:
    """Masks secret value for logging purposes."""
    if not secret_val:
        return "<EMPTY>"
    if len(secret_val) <= 4:
        return "****"
    return secret_val[:2] + "****" + secret_val[-2:]
