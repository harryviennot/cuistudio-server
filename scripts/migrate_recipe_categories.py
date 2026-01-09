#!/usr/bin/env python3
"""
Migration script to assign categories to existing recipes.

This script:
1. Fetches all recipes that don't have a category_id set
2. Uses AI to determine the best category based on title, description, and existing tags/categories
3. Updates each recipe with the appropriate category_id

Usage:
    python scripts/migrate_recipe_categories.py [--dry-run] [--batch-size 50]

Options:
    --dry-run       Preview changes without applying them
    --batch-size    Number of recipes to process at a time (default: 50)
"""
import asyncio
import argparse
import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Category mapping for common patterns
CATEGORY_KEYWORDS = {
    "main-dishes": ["main", "entree", "dinner", "plat principal", "meal", "chicken", "beef", "pork", "fish", "meat"],
    "soups": ["soup", "soupe", "stew", "broth", "chowder", "bisque", "potage"],
    "salads": ["salad", "salade", "slaw", "coleslaw"],
    "pasta-noodles": ["pasta", "noodle", "spaghetti", "penne", "lasagna", "ramen", "udon", "pâtes"],
    "sandwiches": ["sandwich", "wrap", "burger", "taco", "burrito", "sub", "panini"],
    "appetizers": ["appetizer", "starter", "entrée", "hors d'oeuvre", "finger food", "small plate"],
    "apero": ["apéro", "apero", "charcuterie", "cheese board", "tapas", "mezze"],
    "desserts": ["dessert", "cake", "pie", "ice cream", "pudding", "brownie", "tart", "mousse", "gâteau"],
    "baked-goods": ["bread", "muffin", "cookie", "pastry", "biscuit", "scone", "croissant", "pain", "pâtisserie"],
    "beverages": ["smoothie", "juice", "drink", "beverage", "lemonade", "tea", "coffee", "boisson"],
    "cocktails": ["cocktail", "margarita", "mojito", "martini", "wine", "sangria", "punch", "spritz"],
    "breakfast": ["breakfast", "brunch", "egg", "pancake", "waffle", "omelette", "petit-déjeuner", "cereal", "toast"],
    "sides": ["side dish", "vegetable", "rice", "potato", "fries", "accompaniment", "légume"],
    "sauces-dips": ["sauce", "dressing", "condiment", "dip", "vinaigrette", "marinade", "pesto", "aioli"],
    "snacks": ["snack", "chips", "nuts", "popcorn", "crackers", "trail mix"],
    "grilled": ["grill", "bbq", "barbecue", "kebab", "skewer", "grillades"],
    "bowls-grains": ["bowl", "buddha bowl", "grain", "quinoa", "farro", "couscous", "poke"],
}


def get_supabase_client() -> Client:
    """Create Supabase client from environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

    return create_client(url, key)


def determine_category(recipe: Dict[str, Any], categories: List[Dict[str, Any]]) -> Optional[str]:
    """
    Determine the best category for a recipe based on its content.

    Uses keyword matching on title, description, tags, and existing categories.
    Returns the category slug or None if no match found.
    """
    # Collect all text to search
    title = (recipe.get("title") or "").lower()
    description = (recipe.get("description") or "").lower()
    tags = [t.lower() for t in (recipe.get("tags") or [])]
    old_categories = [c.lower() for c in (recipe.get("categories") or [])]

    all_text = f"{title} {description} {' '.join(tags)} {' '.join(old_categories)}"

    # Score each category based on keyword matches
    scores = {}
    for cat_slug, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in all_text:
                # Weight title matches higher
                if keyword in title:
                    score += 3
                elif keyword in old_categories or keyword in tags:
                    score += 2
                else:
                    score += 1
        if score > 0:
            scores[cat_slug] = score

    # Return the highest scoring category
    if scores:
        best_category = max(scores, key=scores.get)
        return best_category

    # Default to main-dishes if no match
    return "main-dishes"


async def fetch_categories(supabase: Client) -> Dict[str, str]:
    """Fetch all categories and return slug -> id mapping."""
    response = supabase.table("categories").select("id, slug").execute()
    return {cat["slug"]: cat["id"] for cat in response.data or []}


async def fetch_recipes_without_category(
    supabase: Client,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch recipes that don't have a category_id set."""
    response = supabase.table("recipes")\
        .select("id, title, description, tags, categories")\
        .is_("category_id", "null")\
        .eq("is_draft", False)\
        .order("created_at")\
        .range(offset, offset + limit - 1)\
        .execute()

    return response.data or []


async def update_recipe_category(
    supabase: Client,
    recipe_id: str,
    category_id: str,
    dry_run: bool = False
) -> bool:
    """Update a recipe's category_id."""
    if dry_run:
        return True

    try:
        supabase.table("recipes")\
            .update({"category_id": category_id})\
            .eq("id", recipe_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update recipe {recipe_id}: {e}")
        return False


async def migrate_recipes(dry_run: bool = False, batch_size: int = 50):
    """Main migration function."""
    supabase = get_supabase_client()

    # Fetch category mapping
    logger.info("Fetching categories...")
    category_map = await fetch_categories(supabase)

    if not category_map:
        logger.error("No categories found in database. Run migrations first.")
        return

    logger.info(f"Found {len(category_map)} categories")

    # Process recipes in batches
    offset = 0
    total_processed = 0
    total_updated = 0
    category_counts = {slug: 0 for slug in category_map.keys()}

    while True:
        recipes = await fetch_recipes_without_category(supabase, batch_size, offset)

        if not recipes:
            break

        logger.info(f"Processing batch of {len(recipes)} recipes (offset: {offset})")

        for recipe in recipes:
            # Determine category
            category_slug = determine_category(recipe, list(category_map.keys()))
            category_id = category_map.get(category_slug)

            if not category_id:
                logger.warning(f"No category found for recipe '{recipe['title']}' (id: {recipe['id']})")
                continue

            # Update recipe
            if dry_run:
                logger.info(f"[DRY-RUN] Would assign '{category_slug}' to '{recipe['title']}'")
            else:
                success = await update_recipe_category(supabase, recipe["id"], category_id, dry_run)
                if success:
                    total_updated += 1

            category_counts[category_slug] += 1
            total_processed += 1

        offset += batch_size

    # Print summary
    logger.info("=" * 50)
    logger.info("Migration Summary")
    logger.info("=" * 50)
    logger.info(f"Total recipes processed: {total_processed}")
    if not dry_run:
        logger.info(f"Total recipes updated: {total_updated}")
    logger.info("\nCategory distribution:")
    for slug, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            logger.info(f"  {slug}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Migrate existing recipes to use category_id")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")

    args = parser.parse_args()

    if args.dry_run:
        logger.info("Running in DRY-RUN mode - no changes will be made")

    asyncio.run(migrate_recipes(dry_run=args.dry_run, batch_size=args.batch_size))


if __name__ == "__main__":
    main()
