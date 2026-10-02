from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from src.core.config import settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
UPLOAD_ROOT = Path("uploads/properties")


class StorageService:
    @staticmethod
    async def save_property_image(file: UploadFile) -> str:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Only JPEG, PNG and WebP images are allowed")

        content = await file.read()
        if len(content) > MAX_IMAGE_BYTES:
            raise ValueError("Image must be 8 MB or smaller")

        suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }[file.content_type]
        key = f"properties/{uuid4().hex}{suffix}"

        if settings.storage_provider == "s3":
            import boto3

            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url or None,
                region_name=settings.s3_region or None,
                aws_access_key_id=settings.s3_access_key or None,
                aws_secret_access_key=settings.s3_secret_key or None,
            )
            client.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=content,
                ContentType=file.content_type,
                CacheControl="public,max-age=31536000,immutable",
            )
            base = settings.cdn_base_url.rstrip("/") if settings.cdn_base_url else (
                f"{settings.s3_endpoint_url.rstrip('/')}/{settings.s3_bucket}"
                if settings.s3_endpoint_url
                else f"https://{settings.s3_bucket}.s3.amazonaws.com"
            )
            return f"{base}/{key}"

        destination = UPLOAD_ROOT / key.removeprefix("properties/")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return f"/uploads/{key}"
