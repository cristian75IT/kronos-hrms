"""Contract Levels

Revision ID: 007_contract_levels
Revises: 006_seed_holidays
Create Date: 2026-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_contract_levels'
down_revision = '006_seed_holidays'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # National Contract Levels
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        'national_contract_levels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('national_contract_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('config.national_contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level_name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('sort_order', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='config'
    )
    
    op.create_index(
        'ix_ncl_contract_id',
        'national_contract_levels',
        ['national_contract_id'],
        schema='config'
    )

    # ═══════════════════════════════════════════════════════════════════
    # Seed Levels for CCNL CED
    # ═══════════════════════════════════════════════════════════════════
    # Levels: Dirigente (spesso CCNL separato, ma mettiamo Quadro), 1, 2, 3, 4, 5, 6, 7
    # Use subquery to get CCNL_CED id
    
    op.execute("""
        INSERT INTO config.national_contract_levels (national_contract_id, level_name, description, sort_order)
        SELECT 
            id,
            lvl.name,
            lvl.description,
            lvl.sort
        FROM config.national_contracts
        CROSS JOIN (VALUES 
            ('Q', 'Quadro - Funzioni direttive con elevata responsabilità', 10),
            ('1', 'I Livello - Funzioni ad alto contenuto professionale', 20),
            ('2', 'II Livello - Conoscenze specifiche ed autonomia operativa', 30),
            ('3', 'III Livello - Conoscenze tecniche ed esperienza', 40),
            ('4', 'IV Livello - Esecuzione di attività tecnico-pratiche (impiegati ordine)', 50),
            ('5', 'V Livello - Lavoratori qualificati', 60),
            ('6', 'VI Livello - Lavoratori con semplici conoscenze pratiche', 70),
            ('7', 'VII Livello - Addetti pulizie e mansioni semplici', 80)
        ) AS lvl(name, description, sort)
        WHERE code = 'CCNL_CED'
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('national_contract_levels', schema='config')
