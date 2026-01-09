#!/usr/bin/env python3
"""
Migration script to move recipe images from user-centric to recipe-centric storage.

This script:
1. Finds all recipes with image_url pointing to recipe-images bucket
2. Copies images matching *-generated.jpg or *-thumbnail.jpg to recipe-assets bucket
3. Updates the image_url in the recipes table
4. Optionally deletes the old files

Usage:
    python scripts/migrate_recipe_images_to_assets.py [--dry-run] [--batch-size 50] [--delete-old]

Options:
    --dry-run       Preview changes without applying them
    --batch-size    Number of recipes to process at a time (default: 50)
    --delete-old    Delete old files after migration (default: keep them)
"""
import asyncio
import argparse
import logging
import os
import re
import sys
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Regex to match old storage paths
# Pattern: recipe-images/{user_id}/{recipe_id}-generated.jpg or {recipe_id}-thumbnail.jpg
OLD_PATH_PATTERN = re.compile(
    r'/storage/v1/object/public/recipe-images/([a-f0-9-]+)/([a-f0-9-]+)-(generated|thumbnail)\.jpg'
)

SOURCE_BUCKET = "recipe-images"
TARGET_BUCKET = "recipe-assets"


def get_supabase_client() -> Client:
    """Create Supabase client from environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_KEY")
    )

    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY/SUPABASE_SECRET_KEY environment variables. "
            "Please set them before running this script."
        )

    return create_client(url, key)


def parse_old_image_url(image_url: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse old image URL to extract user_id, recipe_id, and image type.

    Returns:
        Tuple of (user_id, recipe_id, image_type) or None if not matching
    """
    if not image_url:
        return None

    match = OLD_PATH_PATTERN.search(image_url)
    if match:
        user_id = match.group(1)
        recipe_id = match.group(2)
        image_type = match.group(3)  # 'generated' or 'thumbnail'
        return (user_id, recipe_id, image_type)

    return None


def build_new_url(supabase_url: str, recipe_id: str, image_type: str) -> str:
    """Build new public URL for the migrated image."""
    return f"{supabase_url}/storage/v1/object/public/{TARGET_BUCKET}/{recipe_id}/{image_type}.jpg"


async def migrate_image(
    supabase: Client,
    supabase_url: str,
    recipe_id: str,
    old_path: str,
    new_path: str,
    dry_run: bool = False
) -> bool:
    """
    Copy an image from old path to new path.

    Returns:
        True if successful, False otherwise
    """
    try:
        if dry_run:
            logger.info(f"  [DRY-RUN] Would copy: {old_path} -> {new_path}")
            return True

        # Download from old location
        old_url = f"{supabase_url}/storage/v1/object/public/{SOURCE_BUCKET}/{old_path}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(old_url)

            if response.status_code != 200:
                logger.warning(f"  Failed to download {old_url}: {response.status_code}")
                return False

            image_data = response.content

            if len(image_data) < 1000:
                logger.warning(f"  Image too small ({len(image_data)} bytes), skipping")
                return False

        # Upload to new location
        supabase.storage.from_(TARGET_BUCKET).upload(
            path=new_path,
            file=image_data,
            file_options={
                "content-type": "image/jpeg",
                "cache-control": "3600",
                "upsert": "true"
            }
        )

        logger.info(f"  Copied: {old_path} -> {new_path}")
        return True

    except Exception as e:
        logger.error(f"  Error migrating {old_path}: {e}")
        return False


async def process_batch(
    supabase: Client,
    supabase_url: str,
    recipes: List[Dict[str, Any]],
    dry_run: bool = False,
    delete_old: bool = False
) -> Tuple[int, int]:
    """
    Process a batch of recipes.

    Returns:
        Tuple of (success_count, skip_count)
    """
    success_count = 0
    skip_count = 0

    for recipe in recipes:
        recipe_id = recipe["id"]
        image_url = recipe.get("image_url", "")

        parsed = parse_old_image_url(image_url)

        if not parsed:
            # Not an old-format URL, skip
            skip_count += 1
            continue

        user_id, url_recipe_id, image_type = parsed

        # Verify recipe_id matches
        if url_recipe_id != recipe_id:
            logger.warning(f"Recipe {recipe_id}: URL recipe_id mismatch ({url_recipe_id}), skipping")
            skip_count += 1
            continue

        old_path = f"{user_id}/{recipe_id}-{image_type}.jpg"
        new_path = f"{recipe_id}/{image_type}.jpg"

        logger.info(f"Processing recipe {recipe_id} ({image_type}):")

        # Copy to new location
        success = await migrate_image(
            supabase, supabase_url, recipe_id, old_path, new_path, dry_run
        )

        if success:
            # Update recipe image_url
            new_url = build_new_url(supabase_url, recipe_id, image_type)

            if not dry_run:
                supabase.table("recipes").update({
                    "image_url": new_url
                }).eq("id", recipe_id).execute()
                logger.info(f"  Updated image_url for recipe {recipe_id}")
            else:
                logger.info(f"  [DRY-RUN] Would update image_url to: {new_url}")

            # Optionally delete old file
            if delete_old and not dry_run:
                try:
                    supabase.storage.from_(SOURCE_BUCKET).remove([old_path])
                    logger.info(f"  Deleted old file: {old_path}")
                except Exception as e:
                    logger.warning(f"  Failed to delete old file {old_path}: {e}")

            success_count += 1
        else:
            skip_count += 1

    return success_count, skip_count


async def main(dry_run: bool = False, batch_size: int = 50, delete_old: bool = False):
    """Main migration function."""
    logger.info("=" * 60)
    logger.info("Recipe Images Migration: recipe-images -> recipe-assets")
    logger.info("=" * 60)

    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    if delete_old:
        logger.info("DELETE OLD FILES - Old files will be removed after migration")

    logger.info("")

    supabase = get_supabase_client()
    supabase_url = os.environ.get("SUPABASE_URL")

    # First, ensure target bucket exists
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]

        if TARGET_BUCKET not in bucket_names:
            if dry_run:
                logger.info(f"[DRY-RUN] Would create bucket: {TARGET_BUCKET}")
            else:
                supabase.storage.create_bucket(TARGET_BUCKET, options={"public": True})
                logger.info(f"Created bucket: {TARGET_BUCKET}")
        else:
            logger.info(f"Bucket {TARGET_BUCKET} already exists")
    except Exception as e:
        logger.warning(f"Could not check/create bucket (may already exist): {e}")

    # Find recipes with old-format image URLs
    logger.info("\nFinding recipes with old-format image URLs...")

    total_success = 0
    total_skip = 0
    offset = 0

    while True:
        # Fetch batch of recipes with image_url containing recipe-images bucket
        response = supabase.table("recipes")\
            .select("id, image_url")\
            .like("image_url", f"%{SOURCE_BUCKET}%")\
            .range(offset, offset + batch_size - 1)\
            .execute()

        recipes = response.data

        if not recipes:
            break

        logger.info(f"\nProcessing batch of {len(recipes)} recipes (offset {offset})...")

        success, skip = await process_batch(
            supabase, supabase_url, recipes, dry_run, delete_old
        )

        total_success += success
        total_skip += skip
        offset += batch_size

        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)

    logger.info("\n" + "=" * 60)
    logger.info("Migration Complete!")
    logger.info(f"  Successfully migrated: {total_success}")
    logger.info(f"  Skipped (already migrated or external URL): {total_skip}")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate recipe images from recipe-images to recipe-assets bucket"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of recipes to process at a time (default: 50)"
    )
    parser.add_argument(
        "--delete-old",
        action="store_true",
        help="Delete old files after successful migration"
    )

    args = parser.parse_args()

    asyncio.run(main(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        delete_old=args.delete_old
    ))
