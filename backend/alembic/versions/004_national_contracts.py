"""National Contracts (CCNL) with Versioning

Revision ID: 004_national_contracts
Revises: 003_seed_cont_types
Create Date: 2026-01-01 10:44:00.000000

Implements Italian CCNL (Contratti Collettivi Nazionali di Lavoro) management
with historical versioning to ensure past calculations remain accurate.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_national_contracts'
down_revision = '003_seed_cont_types'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # National Contracts (CCNL) - Master Table
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        'national_contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sector', sa.String(100), nullable=True, comment='Settore economico (Commercio, Metalmeccanico, etc.)'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_url', sa.Text, nullable=True, comment='Link al testo ufficiale del CCNL'),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='config'
    )

    # ═══════════════════════════════════════════════════════════════════
    # National Contract Versions - Historical Parameters
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        'national_contract_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('national_contract_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('config.national_contracts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version_name', sa.String(100), nullable=False, comment='Es: "Rinnovo 2024-2027"'),
        sa.Column('valid_from', sa.Date, nullable=False, comment='Data inizio validità parametri'),
        sa.Column('valid_to', sa.Date, nullable=True, comment='Data fine validità (NULL = ancora valido)'),
        
        # ═══════════════════════════════════════════════════════════════
        # Parametri Orario di Lavoro
        # ═══════════════════════════════════════════════════════════════
        sa.Column('weekly_hours_full_time', sa.Numeric(4, 1), default=40.0, nullable=False, 
                  comment='Ore settimanali per full time'),
        sa.Column('working_days_per_week', sa.Integer, default=5, nullable=False, 
                  comment='Giorni lavorativi settimanali (5 o 6)'),
        sa.Column('daily_hours', sa.Numeric(4, 2), default=8.0, nullable=False, 
                  comment='Ore giornaliere standard'),
        
        # ═══════════════════════════════════════════════════════════════
        # Parametri Ferie (in giorni lavorativi per anno)
        # ═══════════════════════════════════════════════════════════════
        sa.Column('annual_vacation_days', sa.Integer, default=26, nullable=False, 
                  comment='Giorni ferie annuali base'),
        sa.Column('vacation_accrual_method', sa.String(20), default='monthly', nullable=False, 
                  comment='Metodo maturazione: monthly, yearly'),
        sa.Column('vacation_carryover_months', sa.Integer, default=18, nullable=False, 
                  comment='Mesi entro cui fruire ferie anno precedente'),
        sa.Column('vacation_carryover_deadline_month', sa.Integer, default=6, nullable=False, 
                  comment='Mese scadenza ferie AP (6 = 30 Giugno)'),
        sa.Column('vacation_carryover_deadline_day', sa.Integer, default=30, nullable=False, 
                  comment='Giorno scadenza ferie AP'),
        
        # ═══════════════════════════════════════════════════════════════
        # Parametri ROL (Riduzione Orario di Lavoro) - in ore per anno
        # ═══════════════════════════════════════════════════════════════
        sa.Column('annual_rol_hours', sa.Integer, default=72, nullable=False, 
                  comment='Ore ROL annuali (varia per dimensione azienda e anzianità)'),
        sa.Column('rol_accrual_method', sa.String(20), default='monthly', nullable=False, 
                  comment='Metodo maturazione ROL'),
        sa.Column('rol_carryover_months', sa.Integer, default=24, nullable=False, 
                  comment='Mesi entro cui fruire ROL anno precedente'),
        
        # ═══════════════════════════════════════════════════════════════
        # Parametri Ex-Festività / Festività Soppresse (in ore per anno)
        # ═══════════════════════════════════════════════════════════════
        sa.Column('annual_ex_festivita_hours', sa.Integer, default=32, nullable=False, 
                  comment='Ore ex-festività annuali (tipicamente 4 giorni x 8h = 32h)'),
        sa.Column('ex_festivita_accrual_method', sa.String(20), default='yearly', nullable=False, 
                  comment='Metodo maturazione ex-festività'),
        
        # ═══════════════════════════════════════════════════════════════
        # Altri Permessi Retribuiti (in ore per anno)
        # ═══════════════════════════════════════════════════════════════
        sa.Column('annual_study_leave_hours', sa.Integer, default=150, nullable=True, 
                  comment='Ore permesso studio annuali'),
        sa.Column('blood_donation_paid_hours', sa.Integer, default=24, nullable=True, 
                  comment='Ore retribuite per donazione sangue (giornata intera)'),
        sa.Column('marriage_leave_days', sa.Integer, default=15, nullable=True, 
                  comment='Giorni permesso matrimonio'),
        sa.Column('bereavement_leave_days', sa.Integer, default=3, nullable=True, 
                  comment='Giorni permesso lutto'),
        sa.Column('l104_monthly_days', sa.Integer, default=3, nullable=True, 
                  comment='Giorni mensili Legge 104'),
        
        # ═══════════════════════════════════════════════════════════════
        # Parametri Malattia
        # ═══════════════════════════════════════════════════════════════
        sa.Column('sick_leave_carenza_days', sa.Integer, default=3, nullable=False, 
                  comment='Giorni carenza malattia (retribuiti da azienda, non INPS)'),
        sa.Column('sick_leave_max_days_year', sa.Integer, default=180, nullable=True, 
                  comment='Giorni massimi malattia in comporto'),
        
        # ═══════════════════════════════════════════════════════════════
        # Progressione per Anzianità
        # ═══════════════════════════════════════════════════════════════
        sa.Column('seniority_vacation_bonus', postgresql.JSONB, nullable=True,
                  comment='Giorni ferie extra per anzianità: [{"years": 10, "extra_days": 1}, ...]'),
        sa.Column('seniority_rol_bonus', postgresql.JSONB, nullable=True,
                  comment='Ore ROL extra per anzianità'),
        
        # ═══════════════════════════════════════════════════════════════
        # Metadati e Audit
        # ═══════════════════════════════════════════════════════════════
        sa.Column('notes', sa.Text, nullable=True, comment='Note e riferimenti normativi'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        schema='config'
    )
    
    # Index for efficient version lookup by date
    op.create_index(
        'ix_ncv_contract_valid_from',
        'national_contract_versions',
        ['national_contract_id', 'valid_from'],
        schema='config'
    )

    # ═══════════════════════════════════════════════════════════════════
    # Link ContractType to National Contract
    # ═══════════════════════════════════════════════════════════════════
    # Add columns if they don't exist (idempotent approach)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'contract_types' AND column_name = 'national_contract_id'
            ) THEN
                ALTER TABLE config.contract_types ADD COLUMN national_contract_id UUID;
            END IF;
        END $$;
    """)
    
    # Create foreign key if not exists
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_contract_types_national_contract' AND table_schema = 'config'
            ) THEN
                ALTER TABLE config.contract_types 
                ADD CONSTRAINT fk_contract_types_national_contract 
                FOREIGN KEY (national_contract_id) REFERENCES config.national_contracts(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """)
    
    # Add description column if not exists
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'contract_types' AND column_name = 'description'
            ) THEN
                ALTER TABLE config.contract_types ADD COLUMN description TEXT;
            END IF;
        END $$;
    """)

    # ═══════════════════════════════════════════════════════════════════
    # Seed Initial CCNL Data (Commercio as default)
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.national_contracts (id, code, name, sector, description, is_active)
        VALUES 
            (gen_random_uuid(), 'CCNL_CED', 'CCNL Aziende CED', 'Servizi Informatici e CED', 
             'Contratto Collettivo Nazionale di Lavoro per i dipendenti delle aziende del settore Terziario, Distribuzione e Servizi - Centri Elaborazione Dati', true)
        ON CONFLICT (code) DO NOTHING
    """)
    
    # (COMM and MET versions removed)
    
    # Create version for CCNL CED (Centri Elaborazione Dati)
    op.execute("""
        INSERT INTO config.national_contract_versions (
            national_contract_id,
            version_name,
            valid_from,
            weekly_hours_full_time,
            working_days_per_week,
            daily_hours,
            annual_vacation_days,
            vacation_accrual_method,
            vacation_carryover_months,
            vacation_carryover_deadline_month,
            vacation_carryover_deadline_day,
            annual_rol_hours,
            rol_accrual_method,
            rol_carryover_months,
            annual_ex_festivita_hours,
            ex_festivita_accrual_method,
            annual_study_leave_hours,
            blood_donation_paid_hours,
            marriage_leave_days,
            bereavement_leave_days,
            l104_monthly_days,
            sick_leave_carenza_days,
            sick_leave_max_days_year,
            seniority_vacation_bonus,
            notes
        )
        SELECT 
            id,
            'Rinnovo 2024-2027',
            '2024-04-01',
            40.0,
            5,
            8.0,
            26,     -- Ferie: 26 giorni lavorativi
            'monthly',
            18,
            6,      -- Scadenza 30 Giugno
            30,
            72,     -- ROL: 72 ore per aziende > 15 dipendenti
            'monthly',
            24,
            32,     -- Ex-festività: 4 giorni = 32 ore
            'yearly',
            150,    -- 150 ore diritto allo studio triennali
            8,      -- Giornata donazione sangue
            15,     -- 15 giorni matrimonio
            3,      -- 3 giorni lutto
            3,      -- 3 giorni/mese L.104
            3,      -- 3 giorni carenza malattia
            180,    -- 180 giorni comporto
            '[{"years_from": 8, "years_to": null, "extra_days": 1}]'::jsonb,
            'CCNL Terziario Distribuzione e Servizi - Aziende CED. Rinnovo 22 marzo 2024. Include le disposizioni specifiche per i lavoratori del settore informatico e centri elaborazione dati. Orario standard 40h settimanali su 5 giorni.'
        FROM config.national_contracts 
        WHERE code = 'CCNL_CED'
    """)


def downgrade() -> None:
    # Drop foreign key and columns safely
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_contract_types_national_contract' AND table_schema = 'config'
            ) THEN
                ALTER TABLE config.contract_types DROP CONSTRAINT fk_contract_types_national_contract;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'contract_types' AND column_name = 'national_contract_id'
            ) THEN
                ALTER TABLE config.contract_types DROP COLUMN national_contract_id;
            END IF;
        END $$;
    """)
    # Don't drop description column - it may have been added by another migration
    op.execute("DROP INDEX IF EXISTS config.ix_ncv_contract_valid_from")
    op.execute("DROP TABLE IF EXISTS config.national_contract_versions CASCADE")
    op.execute("DROP TABLE IF EXISTS config.national_contracts CASCADE")
