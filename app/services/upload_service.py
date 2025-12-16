"""
Image upload service for Supabase Storage
"""
import uuid
import re
from typing import List, Dict, Optional
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

DEFAULT_STORAGE_BUCKET = "recipe-images"
ALLOWED_BUCKETS = ["recipe-images", "cooking-events"]
# Private buckets require signed URLs for access
PRIVATE_BUCKETS = ["cooking-events"]
SIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour
MAX_FILE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

# Video upload constants (local filesystem storage)
TEMP_VIDEO_DIR = "temp/videos"
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-m4v"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "m4v"}
MAX_VIDEO_SIZE_MB = 500
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

# Formats that need conversion to JPEG for OpenAI compatibility
FORMATS_TO_CONVERT = {'image/heic', 'image/heif'}


class UploadService:
    """Service for handling image uploads to Supabase Storage"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def upload_image(
        self,
        file: UploadFile,
        user_id: str,
        bucket: str = DEFAULT_STORAGE_BUCKET
    ) -> Dict[str, any]:
        """
        Upload a single image to Supabase Storage
        Automatically converts HEIC/HEIF to JPEG for OpenAI compatibility

        Args:
            file: The uploaded file
            user_id: ID of the user uploading the image
            bucket: Target storage bucket (default: recipe-images)

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
            self.supabase.storage.from_(bucket).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",  # Cache for 1 hour
                }
            )

            # Generate URL based on bucket privacy
            if bucket in PRIVATE_BUCKETS:
                # Generate signed URL for private buckets
                signed_url_response = self.supabase.storage.from_(bucket).create_signed_url(
                    storage_path,
                    SIGNED_URL_EXPIRY_SECONDS
                )
                url = signed_url_response.get("signedURL")
                logger.info(f"Generated signed URL for private bucket: {bucket}")
            else:
                # Use public URL for public buckets
                url = self.supabase.storage.from_(bucket).get_public_url(storage_path)

            if file.content_type in FORMATS_TO_CONVERT:
                logger.info(f"Successfully uploaded converted image: {storage_path} ({original_size} → {final_size} bytes, {int((1 - final_size/original_size) * 100)}% reduction)")
            else:
                logger.info(f"Successfully uploaded image: {storage_path}")

            return {
                "url": url,
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
        user_id: str,
        bucket: str = DEFAULT_STORAGE_BUCKET
    ) -> List[Dict[str, any]]:
        """
        Upload multiple images to Supabase Storage

        Args:
            files: List of uploaded files
            user_id: ID of the user uploading the images
            bucket: Target storage bucket (default: recipe-images)

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
                result = await self.upload_image(file, user_id, bucket)
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

    async def delete_image(
        self,
        storage_path: str,
        bucket: str = DEFAULT_STORAGE_BUCKET
    ) -> bool:
        """
        Delete an image from Supabase Storage

        Args:
            storage_path: The storage path of the image to delete
            bucket: Target storage bucket (default: recipe-images)

        Returns:
            True if deletion was successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            self.supabase.storage.from_(bucket).remove([storage_path])
            logger.info(f"Successfully deleted image: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image {storage_path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {str(e)}"
            )

    async def delete_images(
        self,
        storage_paths: List[str],
        bucket: str = DEFAULT_STORAGE_BUCKET
    ) -> bool:
        """
        Delete multiple images from Supabase Storage

        Args:
            storage_paths: List of storage paths to delete
            bucket: Target storage bucket (default: recipe-images)

        Returns:
            True if all deletions were successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            self.supabase.storage.from_(bucket).remove(storage_paths)
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

    def create_signed_url(
        self,
        bucket: str,
        path: str,
        expires_in: int = SIGNED_URL_EXPIRY_SECONDS
    ) -> Optional[str]:
        """
        Generate a signed URL for a private file.

        Args:
            bucket: Storage bucket name
            path: File path within the bucket
            expires_in: URL expiry time in seconds (default 1 hour)

        Returns:
            Signed URL string, or None if generation fails
        """
        try:
            response = self.supabase.storage.from_(bucket).create_signed_url(
                path,
                expires_in
            )
            return response.get("signedURL")
        except Exception as e:
            logger.error(f"Failed to create signed URL for {bucket}/{path}: {str(e)}")
            return None

    @staticmethod
    def extract_storage_path(url: str, bucket: str) -> Optional[str]:
        """
        Extract storage path from a Supabase storage URL.

        Handles both public URLs and signed URLs.
        Pattern: .../storage/v1/object/public/{bucket}/{path}
        Or: .../storage/v1/object/sign/{bucket}/{path}?token=...

        Args:
            url: The storage URL (public or signed)
            bucket: The bucket name to extract path from

        Returns:
            The storage path, or None if extraction fails
        """
        if not url:
            return None

        # If URL is already just a path (not a full URL), return it
        if not url.startswith("http"):
            return url

        # Try to extract path after bucket name
        # Handles both /public/{bucket}/ and /sign/{bucket}/ patterns
        pattern = rf"/(?:public|sign)/{re.escape(bucket)}/(.+?)(?:\?|$)"
        match = re.search(pattern, url)

        if match:
            return match.group(1)

        return None

    # ========== Video Upload Methods (for Instagram client-side download) ==========
    # Videos are stored on local filesystem instead of Supabase (50MB limit on free tier)

    async def save_video_locally(
        self,
        file: UploadFile,
        job_id: str
    ) -> Dict[str, any]:
        """
        Save a video to local filesystem for extraction processing.

        Used when the mobile client downloads an Instagram video and uploads
        it for server-side processing. Videos are stored locally to avoid
        Supabase storage limits.

        Args:
            file: The uploaded video file
            job_id: Extraction job ID (used in storage path)

        Returns:
            Dict with path, size, and content_type

        Raises:
            HTTPException: If file validation fails or save fails
        """
        import os

        # Validate video file
        self._validate_video_file(file)

        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            # Validate file size
            if file_size > MAX_VIDEO_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Video size exceeds maximum allowed size of {MAX_VIDEO_SIZE_MB}MB"
                )

            # Generate storage path: {job_id}/{uuid}.{ext}
            file_extension = self._get_video_extension(file.filename, file.content_type)
            relative_path = f"{job_id}/{uuid.uuid4()}.{file_extension}"

            # Create job directory if it doesn't exist
            job_dir = os.path.join(TEMP_VIDEO_DIR, job_id)
            os.makedirs(job_dir, exist_ok=True)

            # Write to local file
            full_path = os.path.join(TEMP_VIDEO_DIR, relative_path)
            with open(full_path, "wb") as f:
                f.write(file_content)

            logger.info(f"Successfully saved video for job {job_id}: {relative_path} ({file_size} bytes)")

            return {
                "path": relative_path,
                "size": file_size,
                "content_type": file.content_type,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to save video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save video: {str(e)}"
            )
        finally:
            await file.seek(0)

    def _validate_video_file(self, file: UploadFile) -> None:
        """
        Validate video file type.

        Args:
            file: The file to validate

        Raises:
            HTTPException: If file is invalid
        """
        # Check content type
        if file.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid video type: {file.content_type}. Allowed types: {', '.join(ALLOWED_VIDEO_TYPES)}"
            )

        # Check file extension
        if file.filename:
            extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if extension not in ALLOWED_VIDEO_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid video extension: .{extension}. Allowed extensions: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
                )

    def _get_video_extension(self, filename: str, content_type: str) -> str:
        """
        Get video file extension from filename or content type.

        Args:
            filename: Original filename
            content_type: MIME type

        Returns:
            File extension (lowercase, without dot)
        """
        if filename and "." in filename:
            return filename.rsplit(".", 1)[-1].lower()

        # Fallback based on content type
        type_to_ext = {
            "video/mp4": "mp4",
            "video/quicktime": "mov",
            "video/x-m4v": "m4v",
        }
        return type_to_ext.get(content_type, "mp4")

    def get_video_full_path(self, relative_path: str) -> str:
        """
        Get the full filesystem path for a video.

        Args:
            relative_path: Relative path (e.g., "job-id/uuid.mp4")

        Returns:
            Full path to the video file
        """
        import os
        return os.path.join(TEMP_VIDEO_DIR, relative_path)

    async def delete_local_video(self, relative_path: str) -> bool:
        """
        Delete a video from local filesystem.

        Args:
            relative_path: Relative path in temp/videos directory

        Returns:
            True if deletion was successful
        """
        import os
        import shutil

        try:
            full_path = os.path.join(TEMP_VIDEO_DIR, relative_path)

            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Deleted local video: {relative_path}")

                # Try to remove parent directory if empty
                parent_dir = os.path.dirname(full_path)
                if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                    logger.info(f"Removed empty directory: {parent_dir}")

            return True
        except Exception as e:
            logger.warning(f"Failed to delete local video {relative_path}: {str(e)}")
            return False
