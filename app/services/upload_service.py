"""
Image upload service for Supabase Storage
"""
import uuid
from typing import List, Dict
from fastapi import UploadFile, HTTPException, status
from supabase import Client
import logging
import io
from PIL import Image

from app.api.v1.schemas.upload import (
    ALLOWED_IMAGE_TYPES,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE_MB,
    MAX_IMAGES_PER_EXTRACTION,
)

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "recipe-images"
MAX_FILE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

# Formats that need conversion to JPEG for OpenAI compatibility
FORMATS_TO_CONVERT = {'image/heic', 'image/heif'}


class UploadService:
    """Service for handling image uploads to Supabase Storage"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def upload_image(
        self,
        file: UploadFile,
        user_id: str
    ) -> Dict[str, any]:
        """
        Upload a single image to Supabase Storage
        Automatically converts HEIC/HEIF to JPEG for OpenAI compatibility

        Args:
            file: The uploaded file
            user_id: ID of the user uploading the image

        Returns:
            Dict with url, path, size, and content_type

        Raises:
            HTTPException: If file validation fails or upload fails
        """
        # Validate file
        self._validate_image_file(file)

        try:
            # Read file content
            file_content = await file.read()
            original_size = len(file_content)

            # Validate file size
            if original_size > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size of {MAX_IMAGE_SIZE_MB}MB"
                )

            # Convert HEIC/HEIF to JPEG for OpenAI compatibility
            if file.content_type in FORMATS_TO_CONVERT:
                logger.info(f"Converting {file.content_type} to JPEG during upload")
                file_content, content_type = await self._convert_to_jpeg(file_content, file.content_type)
                file_extension = "jpg"
            else:
                content_type = file.content_type
                file_extension = self._get_file_extension(file.filename)

            # Generate unique storage path
            storage_path = f"{user_id}/{uuid.uuid4()}.{file_extension}"
            final_size = len(file_content)

            # Upload to Supabase Storage
            response = self.supabase.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",  # Cache for 1 hour
                }
            )

            # Get public URL
            public_url = self.supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)

            if file.content_type in FORMATS_TO_CONVERT:
                logger.info(f"Successfully uploaded converted image: {storage_path} ({original_size} → {final_size} bytes, {int((1 - final_size/original_size) * 100)}% reduction)")
            else:
                logger.info(f"Successfully uploaded image: {storage_path}")

            return {
                "url": public_url,
                "path": storage_path,
                "size": final_size,
                "content_type": content_type,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )
        finally:
            # Reset file pointer for potential re-use
            await file.seek(0)

    async def upload_images(
        self,
        files: List[UploadFile],
        user_id: str
    ) -> List[Dict[str, any]]:
        """
        Upload multiple images to Supabase Storage

        Args:
            files: List of uploaded files
            user_id: ID of the user uploading the images

        Returns:
            List of dicts with upload results

        Raises:
            HTTPException: If validation fails or upload fails
        """
        # Validate number of files
        if len(files) > MAX_IMAGES_PER_EXTRACTION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot upload more than {MAX_IMAGES_PER_EXTRACTION} images per extraction"
            )

        if len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one image is required"
            )

        # Validate all files before uploading any
        for file in files:
            self._validate_image_file(file)

        # Upload all files
        uploaded_images = []
        for file in files:
            try:
                result = await self.upload_image(file, user_id)
                uploaded_images.append(result)
            except Exception as e:
                # If any upload fails, log but continue (or implement rollback)
                logger.error(f"Failed to upload {file.filename}: {str(e)}")
                # For now, we'll fail the entire batch if one fails
                # TODO: Implement cleanup of already uploaded files
                raise

        logger.info(f"Successfully uploaded {len(uploaded_images)} images for user {user_id}")
        return uploaded_images

    def _validate_image_file(self, file: UploadFile) -> None:
        """
        Validate image file type and basic properties

        Args:
            file: The file to validate

        Raises:
            HTTPException: If file is invalid
        """
        # Check content type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        # Check file extension
        if file.filename:
            extension = self._get_file_extension(file.filename)
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file extension: .{extension}. Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
                )

    def _get_file_extension(self, filename: str) -> str:
        """
        Extract file extension from filename

        Args:
            filename: The filename

        Returns:
            File extension (lowercase, without dot)

        Raises:
            HTTPException: If filename has no extension
        """
        if not filename or "." not in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename must have an extension"
            )

        extension = filename.rsplit(".", 1)[1].lower()
        return extension

    async def delete_image(self, storage_path: str) -> bool:
        """
        Delete an image from Supabase Storage

        Args:
            storage_path: The storage path of the image to delete

        Returns:
            True if deletion was successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            self.supabase.storage.from_(STORAGE_BUCKET).remove([storage_path])
            logger.info(f"Successfully deleted image: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image {storage_path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {str(e)}"
            )

    async def delete_images(self, storage_paths: List[str]) -> bool:
        """
        Delete multiple images from Supabase Storage

        Args:
            storage_paths: List of storage paths to delete

        Returns:
            True if all deletions were successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            self.supabase.storage.from_(STORAGE_BUCKET).remove(storage_paths)
            logger.info(f"Successfully deleted {len(storage_paths)} images")
            return True
        except Exception as e:
            logger.error(f"Failed to delete images: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete images: {str(e)}"
            )

    async def _convert_to_jpeg(self, image_data: bytes, original_mime: str) -> tuple[bytes, str]:
        """
        Convert image to JPEG format (optimized for speed)

        Args:
            image_data: Raw image bytes
            original_mime: Original MIME type

        Returns:
            Tuple of (converted_image_bytes, new_mime_type)
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))

            # Resize large images for faster processing and smaller files
            # OpenAI recommends max 2048px per dimension
            max_dimension = 2048
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized {original_mime} image: {image.size} → {new_size}")

            # Convert to RGB (JPEG doesn't support transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = rgb_image
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Save to bytes with optimized settings
            output_buffer = io.BytesIO()
            # Quality 85 = great visual quality, 50% smaller than quality 95
            # optimize=True = use optimal Huffman coding
            image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            converted_data = output_buffer.getvalue()

            # Use image/jpg instead of image/jpeg for Supabase compatibility
            # (Supabase bucket currently only accepts image/jpg, not image/jpeg)
            return converted_data, 'image/jpg'

        except Exception as e:
            logger.error(f"Failed to convert image to JPEG: {str(e)}")
            # Return original if conversion fails
            return image_data, original_mime
