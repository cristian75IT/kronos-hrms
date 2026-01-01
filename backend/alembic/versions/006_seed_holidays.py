"""Seed holidays for Italy - National and Local

Revision ID: 006_seed_holidays
Revises: 005_holiday_enhancements
Create Date: 2026-01-01 11:20:00.000000

Seeds holidays data for:
- National holidays (all of Italy)
- Local holidays (Santo Patrono - Cagliari, Milano)
"""
from alembic import op
from datetime import date

# revision identifiers, used by Alembic.
revision = '006_seed_holidays'
down_revision = '005_holiday_enhancements'
branch_labels = None
depends_on = None


# ═══════════════════════════════════════════════════════════════════
# Italian National Holidays (Fixed dates - same every year)
# ═══════════════════════════════════════════════════════════════════
NATIONAL_HOLIDAYS = [
    ('01-01', 'Capodanno'),
    ('01-06', 'Epifania'),
    ('04-25', 'Festa della Liberazione'),
    ('05-01', 'Festa del Lavoro'),
    ('06-02', 'Festa della Repubblica'),
    ('08-15', 'Ferragosto (Assunzione)'),
    ('11-01', 'Tutti i Santi'),
    ('12-08', 'Immacolata Concezione'),
    ('12-25', 'Natale'),
    ('12-26', 'Santo Stefano'),
]

# ═══════════════════════════════════════════════════════════════════
# Local Holidays (Santo Patrono)
# ═══════════════════════════════════════════════════════════════════
LOCAL_HOLIDAYS = {
    'Cagliari': [
        ('10-30', 'San Saturnino'),
    ],
    'Milano': [
        ('12-07', "Sant'Ambrogio"),
    ],
}


def upgrade() -> None:
    """Seed holidays for current and next year."""
    current_year = date.today().year
    
    def escape_sql(s: str) -> str:
        """Escape single quotes for SQL strings."""
        return s.replace("'", "''")
    
    # Seed for current year and next year
    for year in [current_year, current_year + 1]:
        # National holidays
        for month_day, name in NATIONAL_HOLIDAYS:
            full_date = f"{year}-{month_day}"
            name_escaped = escape_sql(name)
            op.execute(f"""
                INSERT INTO config.holidays (id, date, name, is_national, is_regional, is_confirmed, year)
                VALUES (gen_random_uuid(), '{full_date}', '{name_escaped}', true, false, true, {year})
                ON CONFLICT DO NOTHING
            """)
        
        # Local holidays (Santo Patrono)
        for location, holidays in LOCAL_HOLIDAYS.items():
            for holiday_data in holidays:
                month_day = holiday_data[0]
                name = escape_sql(holiday_data[1])
                full_date = f"{year}-{month_day}"
                op.execute(f"""
                    INSERT INTO config.holidays (id, date, name, is_national, is_regional, is_confirmed, year)
                    VALUES (gen_random_uuid(), '{full_date}', '{name} - Patrono di {location}', false, false, true, {year})
                    ON CONFLICT DO NOTHING
                """)


def downgrade() -> None:
    """Remove seeded holidays."""
    current_year = date.today().year
    
    # Remove seeded holidays for current and next year
    for year in [current_year, current_year + 1]:
        op.execute(f"DELETE FROM config.holidays WHERE year = {year}")
