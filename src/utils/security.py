import os
import re


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
        return os.environ.get(env_var_name, "")
    
    return secret_ref


def mask_secret(secret_val: str) -> str:
    """Masks secret value for logging purposes."""
    if not secret_val:
        return "<EMPTY>"
    if len(secret_val) <= 4:
        return "****"
    return secret_val[:2] + "****" + secret_val[-2:]
