"""
KRONOS - Seed Leave Types

Import leave types from JSON configuration file.
Usage: python -m scripts.seed_leave_types
"""
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Use sync driver for scripts
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kronos:kronos@localhost:5432/kronos")
# Convert async URL to sync if needed
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
if "postgresql+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")


def load_leave_types_json() -> list[dict]:
    """Load leave types from JSON file."""
    json_path = Path(__file__).parent.parent / "setup_data" / "leave_types.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_leave_types():
    """Seed or update leave types from JSON."""
    engine = create_engine(DATABASE_URL)
    leave_types = load_leave_types_json()

    with Session(engine) as session:
        for lt in leave_types:
            # Check if exists
            result = session.execute(
                text("SELECT id FROM config.leave_types WHERE code = :code"),
                {"code": lt["code"]}
            ).fetchone()

            if result:
                # Update existing
                session.execute(
                    text("""
                        UPDATE config.leave_types SET
                            name = :name,
                            description = :description,
                            max_single_request_days = :max_single_request_days,
                            max_consecutive_days = :max_consecutive_days,
                            min_notice_days = :min_notice_days,
                            requires_protocol = :requires_protocol,
                            balance_type = :balance_type,
                            is_active = :is_active
                        WHERE code = :code
                    """),
                    {
                        "code": lt["code"],
                        "name": lt["name"],
                        "description": lt.get("description"),
                        "max_single_request_days": lt.get("max_single_request_days"),
                        "max_consecutive_days": lt.get("max_consecutive_days"),
                        "min_notice_days": lt.get("min_notice_days"),
                        "requires_protocol": lt.get("requires_protocol", False),
                        "balance_type": lt.get("balance_type"),
                        "is_active": lt.get("is_active", True),
                    }
                )
                print(f"  ✓ Updated: {lt['code']} - {lt['name']}")
            else:
                # Insert new
                session.execute(
                    text("""
                        INSERT INTO config.leave_types (
                            code, name, description, 
                            max_single_request_days, max_consecutive_days, min_notice_days,
                            requires_protocol, balance_type, is_active
                        ) VALUES (
                            :code, :name, :description,
                            :max_single_request_days, :max_consecutive_days, :min_notice_days,
                            :requires_protocol, :balance_type, :is_active
                        )
                    """),
                    {
                        "code": lt["code"],
                        "name": lt["name"],
                        "description": lt.get("description"),
                        "max_single_request_days": lt.get("max_single_request_days"),
                        "max_consecutive_days": lt.get("max_consecutive_days"),
                        "min_notice_days": lt.get("min_notice_days"),
                        "requires_protocol": lt.get("requires_protocol", False),
                        "balance_type": lt.get("balance_type"),
                        "is_active": lt.get("is_active", True),
                    }
                )
                print(f"  + Created: {lt['code']} - {lt['name']}")

        session.commit()
        print(f"\n✅ Seeded {len(leave_types)} leave types successfully.")


if __name__ == "__main__":
    print("🌱 Seeding Leave Types...")
    seed_leave_types()
