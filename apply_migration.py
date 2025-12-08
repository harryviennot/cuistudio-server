#!/usr/bin/env python3
"""
Script to apply database migrations to Supabase

This script helps you apply SQL migrations to your Supabase database.
It can either execute the migration directly (if DATABASE_URL is provided)
or provide instructions for manual execution.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration(migration_file: str):
    """Apply a migration file to Supabase"""

    # Read migration file
    migration_path = Path(__file__).parent / "database" / "migrations" / migration_file

    if not migration_path.exists():
        print(f"❌ Error: Migration file not found: {migration_path}")
        sys.exit(1)

    print(f"📖 Reading migration file: {migration_file}")
    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    print(f"\n{'='*80}")
    print(f"🔄 Migration: {migration_file}")
    print(f"{'='*80}\n")

    # Check if we have a DATABASE_URL for direct execution
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        try:
            import psycopg2
            print("✅ Found DATABASE_URL - attempting direct execution...")

            # Connect to database
            conn = psycopg2.connect(database_url)
            conn.autocommit = False

            try:
                cursor = conn.cursor()

                # Execute migration
                cursor.execute(migration_sql)

                # Commit changes
                conn.commit()
                print("✅ Migration applied successfully!")

                cursor.close()
                conn.close()

                return

            except Exception as e:
                conn.rollback()
                print(f"❌ Error executing migration: {str(e)}")
                print("   Rolling back changes...")
                conn.close()
                sys.exit(1)

        except ImportError:
            print("⚠️  psycopg2 not installed. Install with: pip install psycopg2-binary")
            print("   Falling back to manual instructions...\n")
        except Exception as e:
            print(f"⚠️  Could not connect to database: {str(e)}")
            print("   Falling back to manual instructions...\n")

    # Provide manual instructions
    print("📋 Please apply this migration manually using one of these methods:\n")

    print("1️⃣  Supabase Dashboard SQL Editor:")
    print("   • Go to your Supabase project dashboard")
    print("   • Navigate to SQL Editor")
    print("   • Copy and paste the contents from:")
    print(f"     {migration_path}")
    print("   • Click 'Run'\n")

    print("2️⃣  Using psql (PostgreSQL client):")
    print("   psql 'postgresql://postgres:[PASSWORD]@[HOST]/postgres' \\")
    print(f"        -f {migration_path}\n")

    print("3️⃣  Using Supabase CLI:")
    print("   supabase db push\n")

    print(f"{'='*80}")
    print("📄 Migration file location:")
    print(f"   {migration_path}\n")
    print("📝 What this migration does:")
    print("   • Creates helper functions to migrate instruction format")
    print("   • Updates existing recipes from old format (text field)")
    print("     to new format (title + description fields)")
    print("   • Adds validation functions for future use")
    print("   • Preserves all existing data during migration")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_migration.py <migration_file>")
        print("\nExample:")
        print("  python apply_migration.py 009_update_instruction_model.sql")
        sys.exit(1)

    migration_file = sys.argv[1]
    apply_migration(migration_file)
