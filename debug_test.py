#!/usr/bin/env python3
"""
Debug script to test individual components
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        from app.database import get_supabase_client
        supabase = get_supabase_client()
        print("✅ Database client created successfully")
        
        # Test a simple query
        response = supabase.table("recipes").select("count").limit(1).execute()
        print("✅ Database query successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_recipe_service():
    """Test recipe service"""
    print("\n🔍 Testing recipe service...")
    try:
        from app.database import get_supabase_client
        from app.services.recipe_service import RecipeService
        from app.models import RecipeCreate, SourceType
        
        supabase = get_supabase_client()
        recipe_service = RecipeService(supabase)
        
        # Test creating a recipe
        recipe_data = RecipeCreate(
            user_id="00000000-0000-0000-0000-000000000000",
            title="Test Recipe",
            source_type=SourceType.text,
            ingredients=[],
            instructions=[]
        )
        
        recipe = await recipe_service.create_recipe(recipe_data)
        print(f"✅ Recipe service test successful: {recipe['id']}")
        return True
    except Exception as e:
        print(f"❌ Recipe service test failed: {e}")
        return False

async def test_parsing_service():
    """Test parsing service"""
    print("\n🔍 Testing parsing service...")
    try:
        from app.database import get_supabase_client
        from app.services.parsing_service_clean import ParsingServiceClean as ParsingService
        
        supabase = get_supabase_client()
        parsing_service = ParsingService(supabase)
        print("✅ Parsing service created successfully")
        return True
    except Exception as e:
        print(f"❌ Parsing service test failed: {e}")
        return False

async def main():
    """Run all debug tests"""
    print("🚀 Debug Tests")
    print("=" * 30)
    
    # Test database connection
    db_ok = await test_database_connection()
    
    # Test recipe service
    recipe_ok = await test_recipe_service()
    
    # Test parsing service
    parsing_ok = await test_parsing_service()
    
    print("\n" + "=" * 30)
    print("📊 Test Results:")
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"Recipe Service: {'✅' if recipe_ok else '❌'}")
    print(f"Parsing Service: {'✅' if parsing_ok else '❌'}")

if __name__ == "__main__":
    asyncio.run(main()) 