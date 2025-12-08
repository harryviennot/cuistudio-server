#!/usr/bin/env python3
"""
Run pending database migrations.

Applies all migrations from database/migrations/ that haven't been applied yet.
Migrations are applied in version order and recorded in the _migrations table.
"""

import os
import sys
import re
import psycopg2
from pathlib import Path


def get_migration_files() -> list[tuple[str, str, Path]]:
    """Get all migration files from the migrations directory."""
    migrations_dir = Path(__file__).parent.parent / "database" / "migrations"

    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}", file=sys.stderr)
        return []

    migrations = []
    pattern = re.compile(r"^(\d+)_(.+)\.sql$")

    for file in sorted(migrations_dir.glob("*.sql")):
        match = pattern.match(file.name)
        if match:
            version = match.group(1)
            name = match.group(2)
            migrations.append((version, name, file))

    return migrations


def ensure_migrations_table(conn) -> None:
    """Create _migrations table if it doesn't exist."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public._migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()


def get_applied_migrations(conn) -> set[str]:
    """Get versions of migrations that have been applied."""
    cur = conn.cursor()

    # Check if table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = '_migrations'
        );
    """)

    if not cur.fetchone()[0]:
        cur.close()
        return set()

    cur.execute("SELECT version FROM public._migrations;")
    versions = {row[0] for row in cur.fetchall()}
    cur.close()

    return versions


def apply_migration(conn, version: str, name: str, file_path: Path) -> bool:
    """Apply a single migration."""
    print(f"Applying migration {version}_{name}...")

    try:
        sql = file_path.read_text()

        cur = conn.cursor()

        # Execute the migration
        cur.execute(sql)

        # Record the migration
        cur.execute(
            "INSERT INTO public._migrations (version, name) VALUES (%s, %s);",
            (version, name),
        )

        conn.commit()
        cur.close()

        print(f"  ✅ Applied {version}_{name}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Failed {version}_{name}: {e}", file=sys.stderr)
        return False


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

    # Ensure migrations table exists
    ensure_migrations_table(conn)

    # Get all migration files
    migration_files = get_migration_files()
    print(f"Found {len(migration_files)} migration files")

    # Get applied migrations
    applied = get_applied_migrations(conn)
    print(f"Found {len(applied)} already applied migrations")

    # Find and apply pending migrations
    pending = [(v, n, f) for v, n, f in migration_files if v not in applied]

    if not pending:
        print("No pending migrations to apply")
        conn.close()
        return

    print(f"Applying {len(pending)} pending migrations...")

    failed = False
    for version, name, file_path in pending:
        if not apply_migration(conn, version, name, file_path):
            failed = True
            break  # Stop on first failure

    conn.close()

    if failed:
        print("\n❌ Migration failed!", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ Successfully applied {len(pending)} migrations")


if __name__ == "__main__":
    main()
