# 🗃️ Alembic Database Migration Guide

Alembic is a lightweight database migration tool for usage with SQLAlchemy. It provides a way to manage database schema changes over time, allowing you to version control your database structure and safely apply changes across different environments.

## Table of Contents
- [What is Alembic?](#what-is-alembic)
- [Initial Setup](#initial-setup)
- [Creating Migrations](#creating-migrations)
- [Running Migrations](#running-migrations)
- [Migration Management](#migration-management)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## What is Alembic?

Alembic allows you to:
- **Version Control Database Schema**: Track changes to your database structure over time
- **Auto-generate Migrations**: Automatically detect model changes and create migration scripts
- **Safe Schema Updates**: Apply and rollback database changes safely
- **Environment Management**: Handle different database configurations for development, testing, and production
- **Team Collaboration**: Share database changes consistently across your development team

## Initial Setup

### 1. First Time Setup

When starting with a new database:

```bash
# Create initial migration from current models
alembic revision --autogenerate -m "Initial migration"

# Apply the migration to create tables
alembic upgrade head
```

### 2. Existing Database Setup

If you already have tables in your database:

```bash
# Mark current state as baseline (doesn't run migrations)
alembic stamp head
```

### 3. Environment Configuration

Alembic uses the `DATABASE_URL` environment variable. Set it according to your environment:

```bash
# Development
export DATABASE_URL="postgresql://api_user:api_password@localhost:5432/api_db"

# Production
export DATABASE_URL="postgresql://user:password@prod-server:5432/prod_db"

# Testing
export DATABASE_URL="postgresql://user:password@test-server:5432/test_db"
```

## Creating Migrations

### Auto-Generated Migrations

The most common way to create migrations is auto-generation based on model changes:

```bash
# Auto-detect changes and create migration
alembic revision --autogenerate -m "Add user profile fields"
```

**Example workflow:**
1. Modify your SQLAlchemy models (e.g., add a new field to `User` model)
2. Run the auto-generate command above
3. Review the generated migration file
4. Apply the migration with `alembic upgrade head`

### Manual Migrations

For data migrations or complex schema changes:

```bash
# Create empty migration file
alembic revision -m "Populate default user roles"
```

Then edit the generated file to add your custom migration logic:

```python
def upgrade() -> None:
    # Add your custom migration code here
    op.execute("INSERT INTO roles (name) VALUES ('admin'), ('user')")

def downgrade() -> None:
    # Add rollback logic here
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'user')")
```

### Migration File Structure

Generated migration files follow this structure:

```python
"""Add user profile fields

Revision ID: ae1027a6acf
Revises: 1975ea83b712
Create Date: 2024-01-15 10:30:45.123456
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'ae1027a6acf'
down_revision = '1975ea83b712'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Schema changes to apply
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))

def downgrade() -> None:
    # How to rollback these changes
    op.drop_column('users', 'bio')
    op.drop_column('users', 'phone')
```

## Running Migrations

### Basic Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Apply next migration only
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 1975ea83b712

# Rollback all migrations
alembic downgrade base
```

### Migration Status Commands

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic show head

# Display verbose history
alembic history --verbose
```

### Preview Mode

Generate SQL without executing:

```bash
# See what SQL would be executed
alembic upgrade head --sql

# Save SQL to file
alembic upgrade head --sql > migration.sql
```

## Migration Management

### Working with Branches

When working with feature branches, you might encounter migration conflicts:

```bash
# Create branch-specific migration
alembic revision --autogenerate -m "Feature: user notifications" --branch-label notifications

# Merge branches
alembic merge -m "Merge notifications feature" <rev1> <rev2>
```

### Handling Conflicts

If multiple developers create migrations simultaneously:

1. **Identify the conflict**: `alembic current` shows multiple heads
2. **Create merge migration**: `alembic merge -m "Merge migrations" <rev1> <rev2>`
3. **Apply merged migration**: `alembic upgrade head`

### Database Seeding

Create a data migration for initial data:

```bash
alembic revision -m "Seed initial data"
```

```python
def upgrade() -> None:
    # Insert initial admin user
    op.execute("""
        INSERT INTO users (email, username, hashed_password, is_active, is_superuser, created_at, updated_at)
        VALUES ('admin@example.com', 'admin', '$2b$12$...', true, true, now(), now())
    """)

def downgrade() -> None:
    op.execute("DELETE FROM users WHERE username = 'admin'")
```

## Best Practices

### 1. Review Generated Migrations

Always review auto-generated migrations before applying:

```bash
# Generate migration
alembic revision --autogenerate -m "Add user preferences"

# Review the generated file in alembic/versions/
# Edit if necessary before running upgrade
```

### 2. Test Migrations

Test both upgrade and downgrade paths:

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### 3. Backup Before Production Migrations

```bash
# Backup database before major migrations
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migration
alembic upgrade head
```

### 4. Use Descriptive Migration Messages

```bash
# Good
alembic revision --autogenerate -m "Add user email verification fields"

# Bad
alembic revision --autogenerate -m "Update user model"
```

### 5. Handle Data Carefully

For destructive changes, migrate data first:

```python
def upgrade() -> None:
    # 1. Add new column
    op.add_column('users', sa.Column('full_name', sa.String(200)))
    
    # 2. Migrate existing data
    op.execute("UPDATE users SET full_name = first_name || ' ' || last_name")
    
    # 3. Drop old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "No such revision" Error
```bash
# Check current status
alembic current

# View all revisions
alembic history

# Stamp to correct revision if needed
alembic stamp <correct_revision>
```

#### 2. Multiple Heads
```bash
# Identify multiple heads
alembic heads

# Merge them
alembic merge -m "Merge conflicting migrations" <head1> <head2>
```

#### 3. Failed Migration
```bash
# Check what failed
alembic current

# Fix the migration file or database manually
# Then stamp to correct revision
alembic stamp <last_successful_revision>
```

#### 4. Auto-generate Not Detecting Changes
```bash
# Ensure models are imported in env.py
# Check that target_metadata is set correctly
# Verify database connection
```

### Environment-Specific Issues

#### Docker Environment

The project includes a smart migration script that automatically handles different database states:

```bash
# Option 1: Use the migration service (automatic, recommended)
docker-compose --profile migration up --build

# Option 2: Manual migration using smart script
docker-compose exec api python scripts/migrate.py

# Option 3: Traditional Alembic commands
docker-compose exec api alembic upgrade head

# Generate migrations in container
docker-compose exec api alembic revision --autogenerate -m "Description"

# Check status in container
docker-compose exec api alembic current
```

**Smart Migration Logic**: The `scripts/migrate.py` script automatically detects and handles:
- **Fresh Database**: Runs initial migrations normally
- **Existing Tables without Alembic**: Stamps database and runs pending migrations  
- **Alembic-tracked Database**: Runs pending migrations only

This prevents conflicts when tables already exist from other initialization methods.

#### Production Environment
```bash
# Set production database URL
export DATABASE_URL="postgresql://user:pass@prod-db:5432/prod_db"

# Run with confirmation
alembic upgrade head

# Or use SQL mode for manual execution
alembic upgrade head --sql > prod_migration.sql
```

## Advanced Usage

### Custom Migration Operations

Create reusable migration operations:

```python
# In migration file
def upgrade() -> None:
    # Custom operation
    def create_enum_type(name, values):
        op.execute(f"CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in values)})")
    
    create_enum_type('user_status', ['active', 'inactive', 'suspended'])
    op.add_column('users', sa.Column('status', sa.Enum('user_status'), default='active'))
```

### Branch Management

For complex feature development:

```bash
# Create feature branch migration
alembic revision --autogenerate -m "Feature: advanced search" --branch-label search

# Work on main branch
git checkout main
alembic revision --autogenerate -m "Fix: user validation"

# Merge feature branch
git checkout feature/search
git merge main
alembic merge -m "Merge main into search feature"
```

### Performance Considerations

For large tables:

```python
def upgrade() -> None:
    # Use batch operations for large tables
    with op.batch_alter_table('large_table') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(50)))
        batch_op.create_index('ix_large_table_new_field', ['new_field'])
```

### Environment Variables Override

Create environment-specific configs:

```bash
# Development
export ALEMBIC_CONFIG=alembic.dev.ini

# Production  
export ALEMBIC_CONFIG=alembic.prod.ini

# Use custom config
alembic -c $ALEMBIC_CONFIG upgrade head
```

## Integration with CI/CD

### Automated Migration Testing

```bash
#!/bin/bash
# Test script for CI/CD

# Run migrations
alembic upgrade head

# Test rollback
alembic downgrade -1

# Test re-upgrade
alembic upgrade head

echo "Migration tests passed!"
```

### Production Deployment

```bash
#!/bin/bash
# Production deployment script

# Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
alembic upgrade head

# Verify migration success
if [ $? -eq 0 ]; then
    echo "Migration successful"
else
    echo "Migration failed - check logs"
    exit 1
fi
```

---

## Quick Reference

### Essential Commands
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check status
alembic current

# View history
alembic history

# Rollback
alembic downgrade -1

# Preview SQL
alembic upgrade head --sql
```

### File Structure
```
alembic/
├── versions/           # Migration files
├── env.py             # Environment configuration
└── script.py.mako     # Migration template

alembic.ini            # Main configuration file
```

For more detailed information, refer to the [official Alembic documentation](https://alembic.sqlalchemy.org/).