#!/usr/bin/env python3
"""KRONOS - Database Initialization Script.

Creates all schemas and runs migrations.
Usage: python scripts/init_db.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings


SCHEMAS = ["auth", "leaves", "expenses", "config", "notifications", "audit", "calendar", "hr_reporting", "approvals", "time_wallet", "wallet"]



async def create_schemas():
    """Create all required schemas."""
    print("🔧 Creating database schemas...")
    
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        for schema in SCHEMAS:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            print(f"   ✓ Schema '{schema}' created/verified")
    
    await engine.dispose()
    print("✅ All schemas created successfully!\n")


async def run_migrations():
    """Run Alembic migrations."""
    import subprocess
    
    print("🚀 Running database migrations...")
    
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        print(result.stdout)
        print("✅ Migrations completed successfully!\n")
    else:
        print(f"❌ Migration failed:\n{result.stderr}")
        sys.exit(1)


async def verify_tables():
    """Verify that key tables exist."""
    print("🔍 Verifying database tables...")
    
    engine = create_async_engine(settings.database_url, echo=False)
    
    tables_to_check = [
        ("auth", "users"),
        ("leaves", "leave_requests"),
        ("expenses", "business_trips"),
        ("config", "leave_types"),
        ("config", "calculation_modes"),
        ("notifications", "notifications"),
        ("audit", "audit_logs"),
        ("leaves", "employee_wallets"),
        ("expenses", "trip_wallets"),
        ("calendar", "holidays"),
        ("hr_reporting", "daily_snapshots"),
    ]
    
    async with engine.begin() as conn:
        for schema, table in tables_to_check:
            result = await conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{schema}' 
                    AND table_name = '{table}'
                )
            """))
            exists = result.scalar()
            status = "✓" if exists else "✗"
            print(f"   {status} {schema}.{table}")
    
    await engine.dispose()
    print("✅ Table verification complete!\n")


async def show_summary():
    """Show database summary."""
    print("📊 Database Summary")
    print("=" * 50)
    
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        # Count tables per schema
        for schema in SCHEMAS:
            result = await conn.execute(text(f"""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = '{schema}'
            """))
            count = result.scalar()
            print(f"   {schema}: {count} tables")
        
        # Check seed data
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM config.leave_types"
        ))
        leave_types = result.scalar()
        
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM config.holidays"
        ))
        holidays = result.scalar()
        
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM config.national_contracts"
        ))
        national_contracts = result.scalar()
        
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM config.company_closures"
        ))
        closures = result.scalar()

        result = await conn.execute(text(
            "SELECT COUNT(*) FROM config.calculation_modes"
        ))
        calc_modes = result.scalar()
        
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM config.national_contract_versions"
        ))
        contract_versions = result.scalar()
        
        print(f"\n📋 Seed Data:")
        print(f"   Leave Types: {leave_types}")
        print(f"   Holidays: {holidays}")
        print(f"   National Contracts (CCNL): {national_contracts} ({contract_versions} versions)")
        print(f"   Calculation Modes: {calc_modes}")
        print(f"   Company Closures: {closures}")
    
    await engine.dispose()
    print("\n" + "=" * 50)


async def main():
    """Main initialization function."""
    print("\n" + "=" * 50)
    print("🏢 KRONOS Database Initialization")
    print("=" * 50 + "\n")
    
    print(f"📍 Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}\n")
    
    try:
        await create_schemas()
        await run_migrations()
        await verify_tables()
        await show_summary()
        
        print("\n🎉 Database initialization complete!")
        print("   You can now start the KRONOS services.\n")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
