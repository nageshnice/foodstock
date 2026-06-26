import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import AppException

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_BYTES = 5 * 1024 * 1024


def _upload_root() -> Path:
    root = Path(__file__).resolve().parent.parent.parent / "uploads" / "products"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _public_url(relative_path: str) -> str:
    settings = get_settings()
    prefix = settings.root_path.rstrip("/")
    return f"{prefix}{relative_path}" if prefix else relative_path


async def save_product_image(file: UploadFile) -> str:
    if not file.filename:
        raise AppException("Image file is required", code="image_required")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AppException(
            "Unsupported image type. Use JPG, PNG, WEBP, or GIF.",
            code="invalid_image_type",
        )

    content = await file.read()
    if not content:
        raise AppException("Image file is empty", code="empty_image")
    if len(content) > MAX_BYTES:
        raise AppException("Image must be 5 MB or smaller", code="image_too_large")

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = _upload_root() / filename
    destination.write_bytes(content)

    return _public_url(f"/uploads/products/{filename}")
