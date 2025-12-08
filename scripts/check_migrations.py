#!/usr/bin/env python3
"""
Check for new migrations that haven't been applied to the database.

Compares migration files in database/migrations/ against the _migrations table.
Outputs GitHub Actions variables for use in subsequent jobs.
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


def get_applied_migrations(database_url: str) -> set[str]:
    """Get versions of migrations that have been applied."""
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # Check if _migrations table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '_migrations'
            );
        """)

        if not cur.fetchone()[0]:
            print("Warning: _migrations table doesn't exist yet", file=sys.stderr)
            return set()

        cur.execute("SELECT version FROM public._migrations;")
        versions = {row[0] for row in cur.fetchall()}

        cur.close()
        conn.close()

        return versions
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Get all migration files
    migration_files = get_migration_files()
    print(f"Found {len(migration_files)} migration files", file=sys.stderr)

    # Get applied migrations
    applied = get_applied_migrations(database_url)
    print(f"Found {len(applied)} applied migrations", file=sys.stderr)

    # Find pending migrations
    pending = [(v, n) for v, n in migration_files if v not in applied]

    if pending:
        print(f"Pending migrations: {pending}", file=sys.stderr)
        pending_str = ",".join([f"{v}_{n}" for v, n in pending])

        # Output for GitHub Actions
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"has_new=true\n")
                f.write(f"new_migrations={pending_str}\n")
        else:
            print(f"has_new=true")
            print(f"new_migrations={pending_str}")
    else:
        print("No pending migrations", file=sys.stderr)

        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write("has_new=false\n")
        else:
            print("has_new=false")


if __name__ == "__main__":
    main()
