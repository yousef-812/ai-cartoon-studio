import re
import unicodedata


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    slug = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-")
    if not slug:
        raise ValueError("Series name must contain at least one letter or number")
    return slug
