import re

from app.utils.text import slugify

_SKU_SUFFIX = re.compile(r"-(\d+)$", re.IGNORECASE)


def sku_segment(name: str, *, length: int = 3) -> str:
    """Short lowercase code from a display name (e.g. Exotics → exo)."""
    compact = slugify(name).replace("-", "")
    if not compact:
        return "x" * length
    return compact[:length].lower()


def build_sku_prefix(*names: str) -> str:
    """Build SKU prefix from catalog labels, e.g. Exotics + Curry → exo-cur."""
    return "-".join(sku_segment(name) for name in names if name.strip())


def next_sku_from_existing(prefix: str, existing_skus: list[str]) -> str:
    """Return the next sequential SKU for a prefix, e.g. exo-cur-003."""
    normalized_prefix = prefix.lower()
    max_seq = 0
    for sku in existing_skus:
        sku_lower = sku.strip().lower()
        if not sku_lower.startswith(f"{normalized_prefix}-"):
            continue
        match = _SKU_SUFFIX.search(sku_lower)
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return f"{normalized_prefix}-{max_seq + 1:03d}"
