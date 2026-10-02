from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
UPLOAD_ROOT = Path("uploads/properties")


class ImageService:
    @staticmethod
    async def save_property_image(file: UploadFile) -> str:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Only JPEG, PNG and WebP images are allowed")

        content = await file.read()
        if len(content) > MAX_IMAGE_BYTES:
            raise ValueError("Image must be 8 MB or smaller")

        suffix_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        filename = f"{uuid4().hex}{suffix_map[file.content_type]}"
        UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        destination = UPLOAD_ROOT / filename
        destination.write_bytes(content)

        return f"/uploads/properties/{filename}"
