#!/usr/bin/env python3
"""
Direct migration execution script for Supabase
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

async def run_migration():
    """Execute the migration using Supabase RPC"""

    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SECRET_KEY must be set in .env")
        return

    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)

    # Read migration file
    migration_path = Path(__file__).parent / "database" / "migrations" / "009_update_instruction_model.sql"

    print(f"📖 Reading migration file...")
    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    print(f"\n{'='*80}")
    print(f"🔄 Executing Migration: 009_update_instruction_model.sql")
    print(f"{'='*80}\n")

    try:
        # Execute the SQL via RPC
        # Split the migration into individual statements
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"Executing statement {i}/{len(statements)}...")
                try:
                    # Use Supabase's RPC to execute raw SQL
                    result = supabase.rpc('exec_sql', {'query': statement}).execute()
                    print(f"  ✅ Statement {i} executed")
                except Exception as e:
                    # If RPC doesn't exist, we need to use PostgREST directly
                    print(f"  ⚠️  RPC method not available")
                    print("\n" + "="*80)
                    print("📋 Please run the migration manually:")
                    print("   1. Go to Supabase Dashboard → SQL Editor")
                    print(f"   2. Copy contents from: {migration_path}")
                    print("   3. Paste and click 'Run'")
                    print("="*80)
                    return

        print("\n✅ Migration completed successfully!")
        print("\n📊 Verifying migration...")

        # Verify the migration by checking a recipe
        recipes = supabase.table("recipes").select("id, title, instructions").limit(1).execute()
        if recipes.data:
            recipe = recipes.data[0]
            instructions = recipe.get('instructions', [])
            if instructions and len(instructions) > 0:
                first_instruction = instructions[0]
                if 'title' in first_instruction and 'description' in first_instruction:
                    print("✅ Verification passed: Instructions have new format")
                    print(f"   Sample: {first_instruction}")
                else:
                    print("⚠️  Warning: Instructions may not have migrated correctly")
                    print(f"   Sample: {first_instruction}")

    except Exception as e:
        print(f"❌ Error executing migration: {str(e)}")
        print("\n" + "="*80)
        print("📋 Please run the migration manually:")
        print("   1. Go to Supabase Dashboard → SQL Editor")
        print(f"   2. Copy contents from: {migration_path}")
        print("   3. Paste and click 'Run'")
        print("="*80)

if __name__ == "__main__":
    # Note: Supabase Python client doesn't support direct SQL execution
    # We'll provide a workaround using PostgREST API
    print("\n⚠️  The Supabase Python client doesn't support direct SQL execution.")
    print("Please use one of these methods:\n")
    print("1️⃣  Supabase Dashboard (RECOMMENDED):")
    print("   • Open your Supabase project")
    print("   • Go to SQL Editor")
    print("   • Copy the migration from:")
    print(f"     {Path(__file__).parent / 'database' / 'migrations' / '009_update_instruction_model.sql'}")
    print("   • Paste and click 'Run'\n")

    print("2️⃣  Or copy the migration SQL below and paste it in Supabase SQL Editor:\n")
    print("="*80)

    migration_path = Path(__file__).parent / "database" / "migrations" / "009_update_instruction_model.sql"
    with open(migration_path, 'r') as f:
        print(f.read())

    print("="*80)
