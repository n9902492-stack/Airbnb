from fastapi import UploadFile

from src.services.storage_service import StorageService


class ImageService:
    @staticmethod
    async def save_property_image(file: UploadFile) -> str:
        return await StorageService.save_property_image(file)
