#!/usr/bin/env python3
"""
Smart migration script that handles both fresh databases and existing ones.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return e

def check_alembic_table_exists():
    """Check if alembic_version table exists."""
    cmd = """python -c "
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text('SELECT version_num FROM alembic_version LIMIT 1'))
            return result.fetchone() is not None
        except Exception:
            return False

print(asyncio.run(check()))
"
"""
    result = run_command(cmd, check=False)
    return result.returncode == 0 and "True" in result.stdout

def check_tables_exist():
    """Check if our application tables exist."""
    cmd = """python -c "
import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text(\\\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')\\\"))
            return result.scalar()
        except Exception:
            return False

print(asyncio.run(check()))
"
"""
    result = run_command(cmd, check=False)
    return result.returncode == 0 and "True" in result.stdout

def main():
    """Main migration logic."""
    print("🔍 Checking database state...")
    
    # Check if Alembic is tracking the database
    alembic_tracking = check_alembic_table_exists()
    tables_exist = check_tables_exist()
    
    print(f"📊 Alembic tracking: {alembic_tracking}")
    print(f"📊 Tables exist: {tables_exist}")
    
    if not alembic_tracking and not tables_exist:
        # Fresh database - run migrations normally
        print("🆕 Fresh database detected. Running initial migrations...")
        result = run_command("alembic upgrade head")
        if result.returncode == 0:
            print("✅ Initial migrations completed successfully!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)
            
    elif not alembic_tracking and tables_exist:
        # Tables exist but Alembic isn't tracking - stamp as current
        print("🏷️  Existing tables detected without Alembic tracking.")
        print("🏷️  Stamping database with current migration state...")
        result = run_command("alembic stamp head")
        if result.returncode == 0:
            print("✅ Database stamped successfully!")
            print("🔄 Running any pending migrations...")
            result = run_command("alembic upgrade head")
            if result.returncode == 0:
                print("✅ All migrations up to date!")
            else:
                print("❌ Migration failed!")
                sys.exit(1)
        else:
            print("❌ Stamping failed!")
            sys.exit(1)
            
    else:
        # Alembic is already tracking - just run pending migrations
        print("🔄 Alembic tracking detected. Running pending migrations...")
        result = run_command("alembic upgrade head")
        if result.returncode == 0:
            print("✅ All migrations up to date!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()