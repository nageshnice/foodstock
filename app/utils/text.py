import re
import unicodedata


def slugify(value: str) -> str:
    """Convert display text into a stable URL-safe slug."""

    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
