#!/usr/bin/env python3
"""
Database Migration Script
Handles database migrations for AI Market Terminal
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, capture_output=True):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=capture_output,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_alembic_installed():
    """Check if alembic is installed"""
    success, stdout, stderr = run_command("alembic --version")
    if not success:
        print("❌ Alembic is not installed. Please install it first:")
        print("   pip install alembic")
        return False
    return True

def init_alembic():
    """Initialize alembic if not already initialized"""
    alembic_ini = Path("apps/api/alembic.ini")
    if not alembic_ini.exists():
        print("🔧 Initializing Alembic...")
        success, stdout, stderr = run_command("cd apps/api && alembic init migrations")
        if not success:
            print(f"❌ Failed to initialize Alembic: {stderr}")
            return False
        
        # Update alembic.ini with database URL
        with open(alembic_ini, 'r') as f:
            content = f.read()
        
        content = content.replace(
            'sqlalchemy.url = driver://user:pass@localhost/dbname',
            'sqlalchemy.url = postgresql://ai_market_user:password@localhost:5432/ai_market_terminal'
        )
        
        with open(alembic_ini, 'w') as f:
            f.write(content)
        
        print("✅ Alembic initialized successfully")
    return True

def create_migration(message):
    """Create a new migration"""
    print(f"📝 Creating migration: {message}")
    success, stdout, stderr = run_command(f"cd apps/api && alembic revision --autogenerate -m '{message}'")
    if not success:
        print(f"❌ Failed to create migration: {stderr}")
        return False
    
    print("✅ Migration created successfully")
    return True

def upgrade_database(target="head"):
    """Upgrade database to target revision"""
    print(f"⬆️  Upgrading database to {target}...")
    success, stdout, stderr = run_command(f"cd apps/api && alembic upgrade {target}")
    if not success:
        print(f"❌ Failed to upgrade database: {stderr}")
        return False
    
    print("✅ Database upgraded successfully")
    return True

def downgrade_database(target="-1"):
    """Downgrade database by target revisions"""
    print(f"⬇️  Downgrading database by {target} revisions...")
    success, stdout, stderr = run_command(f"cd apps/api && alembic downgrade {target}")
    if not success:
        print(f"❌ Failed to downgrade database: {stderr}")
        return False
    
    print("✅ Database downgraded successfully")
    return True

def show_migration_history():
    """Show migration history"""
    print("📋 Migration History:")
    success, stdout, stderr = run_command("cd apps/api && alembic history")
    if success:
        print(stdout)
    else:
        print(f"❌ Failed to show history: {stderr}")

def show_current_revision():
    """Show current database revision"""
    print("📍 Current Database Revision:")
    success, stdout, stderr = run_command("cd apps/api && alembic current")
    if success:
        print(stdout)
    else:
        print(f"❌ Failed to show current revision: {stderr}")

def rollback_migration():
    """Rollback the last migration"""
    print("🔄 Rolling back last migration...")
    success, stdout, stderr = run_command("cd apps/api && alembic downgrade -1")
    if not success:
        print(f"❌ Failed to rollback migration: {stderr}")
        return False
    
    print("✅ Migration rolled back successfully")
    return True

def setup_database():
    """Set up the database with initial schema"""
    print("🗄️  Setting up database...")
    
    # Check if alembic is installed
    if not check_alembic_installed():
        return False
    
    # Initialize alembic if needed
    if not init_alembic():
        return False
    
    # Create initial migration if it doesn't exist
    migrations_dir = Path("apps/api/migrations")
    if not migrations_dir.exists() or not list(migrations_dir.glob("*.py")):
        if not create_migration("Initial schema"):
            return False
    
    # Upgrade to latest
    if not upgrade_database():
        return False
    
    print("✅ Database setup completed successfully")
    return True

def main():
    parser = argparse.ArgumentParser(description="Database Migration Script")
    parser.add_argument("action", choices=[
        "setup", "upgrade", "downgrade", "create", "history", 
        "current", "rollback", "init"
    ], help="Migration action to perform")
    parser.add_argument("--message", "-m", help="Migration message (for create action)")
    parser.add_argument("--target", "-t", default="head", help="Target revision (for upgrade/downgrade)")
    
    args = parser.parse_args()
    
    if args.action == "setup":
        success = setup_database()
    elif args.action == "upgrade":
        success = upgrade_database(args.target)
    elif args.action == "downgrade":
        success = downgrade_database(args.target)
    elif args.action == "create":
        if not args.message:
            print("❌ Migration message is required for create action")
            sys.exit(1)
        success = create_migration(args.message)
    elif args.action == "history":
        show_migration_history()
        success = True
    elif args.action == "current":
        show_current_revision()
        success = True
    elif args.action == "rollback":
        success = rollback_migration()
    elif args.action == "init":
        success = init_alembic()
    else:
        print(f"❌ Unknown action: {args.action}")
        success = False
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
