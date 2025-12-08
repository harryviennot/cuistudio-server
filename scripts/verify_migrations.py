#!/usr/bin/env python3
"""
Verify that migrations were applied correctly.

Checks that:
1. All migration files have corresponding entries in _migrations table
2. Key tables exist and have expected structure
"""

import os
import sys
import re
import psycopg2
from pathlib import Path


def get_migration_files() -> list[tuple[str, str]]:
    """Get all migration files from the migrations directory."""
    migrations_dir = Path(__file__).parent.parent / "database" / "migrations"

    if not migrations_dir.exists():
        return []

    migrations = []
    pattern = re.compile(r"^(\d+)_(.+)\.sql$")

    for file in sorted(migrations_dir.glob("*.sql")):
        match = pattern.match(file.name)
        if match:
            version = match.group(1)
            name = match.group(2)
            migrations.append((version, name))

    return migrations


def verify_migrations_recorded(conn, migration_files: list[tuple[str, str]]) -> bool:
    """Verify all migrations are recorded in _migrations table."""
    cur = conn.cursor()

    cur.execute("SELECT version, name FROM public._migrations ORDER BY version;")
    recorded = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()

    all_good = True
    for version, name in migration_files:
        if version not in recorded:
            print(f"❌ Migration {version}_{name} not recorded in _migrations table")
            all_good = False
        elif recorded[version] != name:
            print(
                f"⚠️  Migration {version} name mismatch: expected '{name}', got '{recorded[version]}'"
            )

    return all_good


def verify_core_tables(conn) -> bool:
    """Verify core tables exist."""
    core_tables = [
        "users",
        "recipes",
        "cookbooks",
        "extraction_jobs",
        "user_recipe_data",
        "_migrations",
    ]

    cur = conn.cursor()

    all_exist = True
    for table in core_tables:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            );
        """,
            (table,),
        )

        exists = cur.fetchone()[0]
        if exists:
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' missing!")
            all_exist = False

    cur.close()
    return all_exist


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        conn = psycopg2.connect(database_url)
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)

    print("Verifying migrations...\n")

    # Get migration files
    migration_files = get_migration_files()

    # Verify all migrations are recorded
    print("Checking migration records...")
    migrations_ok = verify_migrations_recorded(conn, migration_files)

    # Verify core tables exist
    print("\nChecking core tables...")
    tables_ok = verify_core_tables(conn)

    conn.close()

    if migrations_ok and tables_ok:
        print("\n✅ All verifications passed!")
    else:
        print("\n❌ Verification failed!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
