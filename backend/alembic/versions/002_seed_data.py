"""KRONOS Seed Data Migration.

Revision ID: 002_seed_data
Revises: 001_initial
Create Date: 2024-12-30

Inserts initial configuration data:
- Leave types (FER, ROL, PAR, MAL, etc.)
- Italian national holidays
- Default system parameters
- Expense types
- Daily allowance rules
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_seed_data'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # CONTRACT TYPES (CONFIG)
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.contract_types (id, code, name, is_part_time, part_time_percentage, annual_vacation_days, annual_rol_hours, annual_permit_hours)
        VALUES 
            ('00000000-0000-0000-0000-000000000001', 'FULL_TIME', 'Tempo Pieno', false, 100, 26, 72, 32),
            ('00000000-0000-0000-0000-000000000002', 'PART_TIME_75', 'Part-time 75%', true, 75, 20, 54, 24),
            ('00000000-0000-0000-0000-000000000003', 'PART_TIME_50', 'Part-time 50%', true, 50, 13, 36, 16)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # LOCATIONS (AUTH)
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO auth.locations (id, code, name, city, province)
        VALUES 
            ('00000000-0000-0000-0000-000000000011', 'MIL_01', 'Sede Milano', 'Milano', 'MI'),
            ('00000000-0000-0000-0000-000000000012', 'ROM_01', 'Sede Roma', 'Roma', 'RM')
    """)

    # ═══════════════════════════════════════════════════════════════════
    # WORK SCHEDULES (AUTH)
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO auth.work_schedules (id, code, name, monday_hours, tuesday_hours, wednesday_hours, thursday_hours, friday_hours)
        VALUES 
            ('00000000-0000-0000-0000-000000000021', 'STD_40', 'Settimana Standard 40h', 8, 8, 8, 8, 8),
            ('00000000-0000-0000-0000-000000000022', 'PT_30', 'Part-time 30h', 6, 6, 6, 6, 6)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # LEAVE TYPES
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.leave_types (id, code, name, description, scales_balance, balance_type, requires_approval, requires_attachment, requires_protocol, min_notice_days, max_consecutive_days, max_per_month, allow_past_dates, allow_half_day, allow_negative_balance, color, is_active, sort_order)
        VALUES 
            (gen_random_uuid(), 'FER', 'Ferie', 'Ferie annuali retribuite', true, 'vacation', true, false, false, 1, 20, null, false, true, false, '#22C55E', true, 1),
            (gen_random_uuid(), 'ROL', 'Riduzione Orario Lavoro', 'Permessi ROL da contratto', true, 'rol', true, false, false, 0, 3, null, false, true, false, '#3B82F6', true, 2),
            (gen_random_uuid(), 'PAR', 'Permessi Retribuiti', 'Permessi retribuiti vari', true, 'permits', true, false, false, 1, 5, null, false, true, false, '#8B5CF6', true, 3),
            (gen_random_uuid(), 'MAL', 'Malattia', 'Assenza per malattia', false, null, false, true, true, 0, null, null, true, false, false, '#EF4444', true, 4),
            (gen_random_uuid(), 'MAT', 'Maternità/Paternità', 'Congedo parentale', false, null, true, true, false, 30, null, null, false, false, false, '#EC4899', true, 5),
            (gen_random_uuid(), 'LUT', 'Lutto', 'Permesso per lutto familiare', false, null, false, true, false, 0, 3, null, false, false, false, '#6B7280', true, 6),
            (gen_random_uuid(), 'STU', 'Studio', 'Permesso per esami/studio', false, null, true, true, false, 7, 5, null, false, true, false, '#F59E0B', true, 7),
            (gen_random_uuid(), 'DON', 'Donazione Sangue', 'Giornata donazione sangue', false, null, false, true, false, 0, 1, null, false, false, false, '#DC2626', true, 8),
            (gen_random_uuid(), 'L104', 'Legge 104', 'Permessi legge 104/92', false, null, true, false, false, 0, null, 3, false, true, false, '#14B8A6', true, 9),
            (gen_random_uuid(), 'SW', 'Smart Working', 'Lavoro da remoto', false, null, true, false, false, 1, null, null, false, true, false, '#0EA5E9', true, 10),
            (gen_random_uuid(), 'NRT', 'Non Retribuito', 'Permesso non retribuito', false, null, true, false, false, 0, null, null, false, true, false, '#9CA3AF', true, 11)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # ITALIAN HOLIDAYS 2025
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.holidays (id, name, date, year, is_national)
        VALUES 
            (gen_random_uuid(), 'Capodanno', '2025-01-01', 2025, true),
            (gen_random_uuid(), 'Epifania', '2025-01-06', 2025, true),
            (gen_random_uuid(), 'Pasqua', '2025-04-20', 2025, true),
            (gen_random_uuid(), 'Lunedì dell''Angelo', '2025-04-21', 2025, true),
            (gen_random_uuid(), 'Festa della Liberazione', '2025-04-25', 2025, true),
            (gen_random_uuid(), 'Festa del Lavoro', '2025-05-01', 2025, true),
            (gen_random_uuid(), 'Festa della Repubblica', '2025-06-02', 2025, true),
            (gen_random_uuid(), 'Ferragosto', '2025-08-15', 2025, true),
            (gen_random_uuid(), 'Tutti i Santi', '2025-11-01', 2025, true),
            (gen_random_uuid(), 'Immacolata Concezione', '2025-12-08', 2025, true),
            (gen_random_uuid(), 'Natale', '2025-12-25', 2025, true),
            (gen_random_uuid(), 'Santo Stefano', '2025-12-26', 2025, true)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # EXPENSE TYPES
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.expense_types (id, code, name, description, category, requires_receipt, max_amount, km_reimbursement_rate, is_taxable, is_active, sort_order)
        VALUES 
            (gen_random_uuid(), 'VIA', 'Viaggio', 'Treno, aereo, bus', 'transport', true, 500.00, null, false, true, 1),
            (gen_random_uuid(), 'AUT', 'Auto Propria', 'Rimborso chilometrico', 'transport', false, null, 0.30, false, true, 2),
            (gen_random_uuid(), 'TAX', 'Taxi/NCC', 'Taxi e noleggio con conducente', 'transport', true, 100.00, null, false, true, 3),
            (gen_random_uuid(), 'ALB', 'Albergo', 'Pernottamento in hotel', 'accommodation', true, 150.00, null, false, true, 4),
            (gen_random_uuid(), 'PRA', 'Pasto', 'Pranzo o cena di lavoro', 'meals', true, 50.00, null, false, true, 5),
            (gen_random_uuid(), 'PAR', 'Parcheggio', 'Parcheggio auto', 'transport', true, 30.00, null, false, true, 6),
            (gen_random_uuid(), 'PED', 'Pedaggi', 'Pedaggi autostradali', 'transport', true, 50.00, null, false, true, 7),
            (gen_random_uuid(), 'CAR', 'Carburante', 'Rifornimento auto aziendale', 'transport', true, 100.00, null, false, true, 8),
            (gen_random_uuid(), 'TEL', 'Telefono', 'Chiamate di lavoro', 'communication', true, 30.00, null, false, true, 9),
            (gen_random_uuid(), 'MAT', 'Materiale', 'Materiale di consumo', 'supplies', true, 100.00, null, false, true, 10),
            (gen_random_uuid(), 'ALT', 'Altro', 'Altre spese autorizzate', 'other', true, null, null, false, true, 99)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # DAILY ALLOWANCE RULES
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.daily_allowance_rules (id, name, destination_type, full_day_amount, half_day_amount, threshold_hours, meals_deduction, is_active)
        VALUES 
            (gen_random_uuid(), 'Italia Standard', 'national', 46.48, 23.24, 8, 20.00, true),
            (gen_random_uuid(), 'Europa Standard', 'eu', 77.47, 38.74, 8, 35.00, true),
            (gen_random_uuid(), 'Extra UE Standard', 'extra_eu', 92.96, 46.48, 8, 40.00, true)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # SYSTEM CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.system_config (id, category, key, value, value_type, description, is_sensitive)
        VALUES 
            -- Leave settings
            (gen_random_uuid(), 'leaves', 'vacation_days_per_year', '26', 'integer', 'Giorni ferie annuali standard', false),
            (gen_random_uuid(), 'leaves', 'rol_hours_per_year', '72', 'integer', 'Ore ROL annuali standard', false),
            (gen_random_uuid(), 'leaves', 'ap_expiry_months', '18', 'integer', 'Mesi validità ferie anno precedente', false),
            (gen_random_uuid(), 'leaves', 'ap_expiry_date', '"06-30"', 'string', 'Data scadenza ferie AP (MM-DD)', false),
            (gen_random_uuid(), 'leaves', 'min_advance_vacation', '7', 'integer', 'Giorni anticipo minimo richiesta ferie', false),
            (gen_random_uuid(), 'leaves', 'max_consecutive_vacation', '15', 'integer', 'Massimo giorni ferie consecutive', false),
            (gen_random_uuid(), 'leaves', 'auto_approve_threshold', '2', 'integer', 'Soglia giorni per auto-approvazione', false),
            
            -- Expense settings
            (gen_random_uuid(), 'expenses', 'km_reimbursement_rate', '0.30', 'decimal', 'Rimborso Euro/km auto propria', false),
            (gen_random_uuid(), 'expenses', 'daily_meal_limit', '50.00', 'decimal', 'Limite giornaliero pasti', false),
            (gen_random_uuid(), 'expenses', 'hotel_limit_national', '150.00', 'decimal', 'Limite hotel Italia', false),
            (gen_random_uuid(), 'expenses', 'hotel_limit_eu', '200.00', 'decimal', 'Limite hotel Europa', false),
            (gen_random_uuid(), 'expenses', 'require_approval_above', '100.00', 'decimal', 'Richiedi approvazione sopra Euro', false),
            
            -- Notification settings
            (gen_random_uuid(), 'notifications', 'reminder_before_expiry_days', '30', 'integer', 'Giorni anticipo reminder scadenza ferie', false),
            (gen_random_uuid(), 'notifications', 'pending_approval_reminder_hours', '48', 'integer', 'Ore prima del reminder approvazione', false),
            (gen_random_uuid(), 'notifications', 'email_enabled', 'true', 'boolean', 'Abilita notifiche email', false),
            
            -- Company settings
            (gen_random_uuid(), 'company', 'name', '"La Mia Azienda S.r.l."', 'string', 'Nome azienda', false),
            (gen_random_uuid(), 'company', 'fiscal_code', '"00000000000"', 'string', 'Codice fiscale/P.IVA', false),
            (gen_random_uuid(), 'company', 'default_timezone', '"Europe/Rome"', 'string', 'Timezone predefinito', false),
            (gen_random_uuid(), 'company', 'work_week_days', '5', 'integer', 'Giorni lavorativi settimanali', false),
            (gen_random_uuid(), 'company', 'work_hours_per_day', '8', 'integer', 'Ore lavorative giornaliere', false)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # EMAIL TEMPLATES
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO notifications.email_templates (id, code, notification_type, name, subject, html_content, text_content, is_active)
        VALUES 
            (gen_random_uuid(), 'LEAVE_SUBMITTED', 'leave_request_submitted', 'Richiesta Ferie Sottomessa', 
             'Nuova richiesta ferie da {{employee_name}}',
             '<h2>Nuova Richiesta Ferie</h2><p>{{employee_name}} ha richiesto {{days}} giorni di ferie dal {{start_date}} al {{end_date}}.</p><p><a href="{{approval_url}}">Clicca qui per approvare</a></p>',
             '{{employee_name}} ha richiesto {{days}} giorni di ferie dal {{start_date}} al {{end_date}}.',
             true),
            
            (gen_random_uuid(), 'LEAVE_APPROVED', 'leave_request_approved', 'Richiesta Ferie Approvata',
             'La tua richiesta ferie è stata approvata',
             '<h2>Ferie Approvate</h2><p>La tua richiesta di ferie dal {{start_date}} al {{end_date}} è stata approvata{{#if approver_notes}} con la seguente nota: {{approver_notes}}{{/if}}.</p>',
             'La tua richiesta di ferie dal {{start_date}} al {{end_date}} è stata approvata.',
             true),
            
            (gen_random_uuid(), 'LEAVE_REJECTED', 'leave_request_rejected', 'Richiesta Ferie Rifiutata',
             'La tua richiesta ferie è stata rifiutata',
             '<h2>Ferie Non Approvate</h2><p>La tua richiesta di ferie dal {{start_date}} al {{end_date}} non è stata approvata.</p><p>Motivo: {{rejection_reason}}</p>',
             'La tua richiesta di ferie dal {{start_date}} al {{end_date}} non è stata approvata. Motivo: {{rejection_reason}}',
             true),
            
            (gen_random_uuid(), 'EXPENSE_APPROVED', 'expense_approved', 'Nota Spese Approvata',
             'La tua nota spese {{report_number}} è stata approvata',
             '<h2>Nota Spese Approvata</h2><p>La nota spese {{report_number}} per un totale di €{{total_amount}} è stata approvata. Importo rimborsato: €{{approved_amount}}</p>',
             'La nota spese {{report_number}} è stata approvata. Importo rimborsato: €{{approved_amount}}',
             true),
            
            (gen_random_uuid(), 'BALANCE_ALERT', 'leave_balance_low', 'Ferie in Scadenza',
             'Hai ferie in scadenza',
             '<h2>Promemoria Ferie</h2><p>Le tue ferie dell''anno precedente ({{ap_days}} giorni) scadranno il {{expiry_date}}. Ricordati di pianificarle!</p>',
             'Le tue ferie AP ({{ap_days}} giorni) scadranno il {{expiry_date}}.',
             true)
    """)


def downgrade() -> None:
    # Delete seed data in reverse order
    op.execute("DELETE FROM notifications.email_templates")
    op.execute("DELETE FROM config.system_config")
    op.execute("DELETE FROM config.daily_allowance_rules")
    op.execute("DELETE FROM config.expense_types")
    op.execute("DELETE FROM config.holidays")
    op.execute("DELETE FROM config.leave_types")
    op.execute("DELETE FROM auth.work_schedules")
    op.execute("DELETE FROM auth.locations")
    op.execute("DELETE FROM config.contract_types")
