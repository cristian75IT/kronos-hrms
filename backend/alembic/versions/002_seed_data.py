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
    # LEAVE TYPES
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.leave_types (id, code, name, description, color, is_paid, affects_balance, requires_approval, requires_attachment, max_consecutive_days, min_advance_days, carry_over_allowed, is_active, sort_order)
        VALUES 
            (gen_random_uuid(), 'FER', 'Ferie', 'Ferie annuali retribuite', '#22C55E', true, true, true, false, 20, 1, true, true, 1),
            (gen_random_uuid(), 'ROL', 'Riduzione Orario Lavoro', 'Permessi ROL da contratto', '#3B82F6', true, true, true, false, 3, 0, false, true, 2),
            (gen_random_uuid(), 'PAR', 'Permessi Retribuiti', 'Permessi retribuiti vari', '#8B5CF6', true, true, true, false, 5, 1, false, true, 3),
            (gen_random_uuid(), 'MAL', 'Malattia', 'Assenza per malattia', '#EF4444', true, false, false, true, null, 0, false, true, 4),
            (gen_random_uuid(), 'MAT', 'Maternità/Paternità', 'Congedo parentale', '#EC4899', true, false, true, true, null, 30, false, true, 5),
            (gen_random_uuid(), 'LUT', 'Lutto', 'Permesso per lutto familiare', '#6B7280', true, false, false, true, 3, 0, false, true, 6),
            (gen_random_uuid(), 'STU', 'Studio', 'Permesso per esami/studio', '#F59E0B', true, true, true, true, 5, 7, false, true, 7),
            (gen_random_uuid(), 'DON', 'Donazione Sangue', 'Giornata donazione sangue', '#DC2626', true, false, false, true, 1, 0, false, true, 8),
            (gen_random_uuid(), 'L104', 'Legge 104', 'Permessi legge 104/92', '#14B8A6', true, false, true, false, null, 0, false, true, 9),
            (gen_random_uuid(), 'SW', 'Smart Working', 'Lavoro da remoto', '#0EA5E9', true, false, true, false, null, 1, false, true, 10),
            (gen_random_uuid(), 'NRT', 'Non Retribuito', 'Permesso non retribuito', '#9CA3AF', false, true, true, false, null, 0, false, true, 11)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # ITALIAN HOLIDAYS 2025
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.holidays (id, name, date, year, is_national, is_recurring)
        VALUES 
            (gen_random_uuid(), 'Capodanno', '2025-01-01', 2025, true, true),
            (gen_random_uuid(), 'Epifania', '2025-01-06', 2025, true, true),
            (gen_random_uuid(), 'Pasqua', '2025-04-20', 2025, true, false),
            (gen_random_uuid(), 'Lunedì dell''Angelo', '2025-04-21', 2025, true, false),
            (gen_random_uuid(), 'Festa della Liberazione', '2025-04-25', 2025, true, true),
            (gen_random_uuid(), 'Festa del Lavoro', '2025-05-01', 2025, true, true),
            (gen_random_uuid(), 'Festa della Repubblica', '2025-06-02', 2025, true, true),
            (gen_random_uuid(), 'Ferragosto', '2025-08-15', 2025, true, true),
            (gen_random_uuid(), 'Tutti i Santi', '2025-11-01', 2025, true, true),
            (gen_random_uuid(), 'Immacolata Concezione', '2025-12-08', 2025, true, true),
            (gen_random_uuid(), 'Natale', '2025-12-25', 2025, true, true),
            (gen_random_uuid(), 'Santo Stefano', '2025-12-26', 2025, true, true)
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
        INSERT INTO config.daily_allowance_rules (id, destination_type, full_day_amount, half_day_amount, breakfast_deduction, lunch_deduction, dinner_deduction, overnight_bonus, tax_free_limit, valid_from, is_active)
        VALUES 
            (gen_random_uuid(), 'national', 46.48, 23.24, 2.79, 9.29, 9.29, 0.00, 46.48, '2025-01-01', true),
            (gen_random_uuid(), 'eu', 77.47, 38.74, 4.65, 15.49, 15.49, 10.00, 77.47, '2025-01-01', true),
            (gen_random_uuid(), 'extra_eu', 92.96, 46.48, 5.58, 18.59, 18.59, 15.00, 92.96, '2025-01-01', true)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # SYSTEM PARAMETERS
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.system_parameters (id, category, key, value, value_type, description, is_editable)
        VALUES 
            -- Leave settings
            (gen_random_uuid(), 'leaves', 'vacation_days_per_year', '26', 'integer', 'Giorni ferie annuali standard', true),
            (gen_random_uuid(), 'leaves', 'rol_hours_per_year', '72', 'integer', 'Ore ROL annuali standard', true),
            (gen_random_uuid(), 'leaves', 'ap_expiry_months', '18', 'integer', 'Mesi validità ferie anno precedente', true),
            (gen_random_uuid(), 'leaves', 'ap_expiry_date', '06-30', 'string', 'Data scadenza ferie AP (MM-DD)', true),
            (gen_random_uuid(), 'leaves', 'min_advance_vacation', '7', 'integer', 'Giorni anticipo minimo richiesta ferie', true),
            (gen_random_uuid(), 'leaves', 'max_consecutive_vacation', '15', 'integer', 'Massimo giorni ferie consecutive', true),
            (gen_random_uuid(), 'leaves', 'auto_approve_threshold', '2', 'integer', 'Soglia giorni per auto-approvazione', true),
            
            -- Expense settings
            (gen_random_uuid(), 'expenses', 'km_reimbursement_rate', '0.30', 'decimal', 'Rimborso Euro/km auto propria', true),
            (gen_random_uuid(), 'expenses', 'daily_meal_limit', '50.00', 'decimal', 'Limite giornaliero pasti', true),
            (gen_random_uuid(), 'expenses', 'hotel_limit_national', '150.00', 'decimal', 'Limite hotel Italia', true),
            (gen_random_uuid(), 'expenses', 'hotel_limit_eu', '200.00', 'decimal', 'Limite hotel Europa', true),
            (gen_random_uuid(), 'expenses', 'require_approval_above', '100.00', 'decimal', 'Richiedi approvazione sopra Euro', true),
            
            -- Notification settings
            (gen_random_uuid(), 'notifications', 'reminder_before_expiry_days', '30', 'integer', 'Giorni anticipo reminder scadenza ferie', true),
            (gen_random_uuid(), 'notifications', 'pending_approval_reminder_hours', '48', 'integer', 'Ore prima del reminder approvazione', true),
            (gen_random_uuid(), 'notifications', 'email_enabled', 'true', 'boolean', 'Abilita notifiche email', true),
            
            -- Company settings
            (gen_random_uuid(), 'company', 'name', 'La Mia Azienda S.r.l.', 'string', 'Nome azienda', true),
            (gen_random_uuid(), 'company', 'fiscal_code', '00000000000', 'string', 'Codice fiscale/P.IVA', true),
            (gen_random_uuid(), 'company', 'default_timezone', 'Europe/Rome', 'string', 'Timezone predefinito', true),
            (gen_random_uuid(), 'company', 'work_week_days', '5', 'integer', 'Giorni lavorativi settimanali', false),
            (gen_random_uuid(), 'company', 'work_hours_per_day', '8', 'integer', 'Ore lavorative giornaliere', false)
    """)

    # ═══════════════════════════════════════════════════════════════════
    # EMAIL TEMPLATES
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO notifications.email_templates (id, notification_type, name, subject, html_content, text_content, is_active)
        VALUES 
            (gen_random_uuid(), 'leave_request_submitted', 'Richiesta Ferie Sottomessa', 
             'Nuova richiesta ferie da {{employee_name}}',
             '<h2>Nuova Richiesta Ferie</h2><p>{{employee_name}} ha richiesto {{days}} giorni di ferie dal {{start_date}} al {{end_date}}.</p><p><a href="{{approval_url}}">Clicca qui per approvare</a></p>',
             '{{employee_name}} ha richiesto {{days}} giorni di ferie dal {{start_date}} al {{end_date}}.',
             true),
            
            (gen_random_uuid(), 'leave_request_approved', 'Richiesta Ferie Approvata',
             'La tua richiesta ferie è stata approvata',
             '<h2>Ferie Approvate</h2><p>La tua richiesta di ferie dal {{start_date}} al {{end_date}} è stata approvata{{#if approver_notes}} con la seguente nota: {{approver_notes}}{{/if}}.</p>',
             'La tua richiesta di ferie dal {{start_date}} al {{end_date}} è stata approvata.',
             true),
            
            (gen_random_uuid(), 'leave_request_rejected', 'Richiesta Ferie Rifiutata',
             'La tua richiesta ferie è stata rifiutata',
             '<h2>Ferie Non Approvate</h2><p>La tua richiesta di ferie dal {{start_date}} al {{end_date}} non è stata approvata.</p><p>Motivo: {{rejection_reason}}</p>',
             'La tua richiesta di ferie dal {{start_date}} al {{end_date}} non è stata approvata. Motivo: {{rejection_reason}}',
             true),
            
            (gen_random_uuid(), 'expense_report_approved', 'Nota Spese Approvata',
             'La tua nota spese {{report_number}} è stata approvata',
             '<h2>Nota Spese Approvata</h2><p>La nota spese {{report_number}} per un totale di €{{total_amount}} è stata approvata. Importo rimborsato: €{{approved_amount}}</p>',
             'La nota spese {{report_number}} è stata approvata. Importo rimborsato: €{{approved_amount}}',
             true),
            
            (gen_random_uuid(), 'balance_expiring', 'Ferie in Scadenza',
             'Hai ferie in scadenza',
             '<h2>Promemoria Ferie</h2><p>Le tue ferie dell''anno precedente ({{ap_days}} giorni) scadranno il {{expiry_date}}. Ricordati di pianificarle!</p>',
             'Le tue ferie AP ({{ap_days}} giorni) scadranno il {{expiry_date}}.',
             true)
    """)


def downgrade() -> None:
    # Delete seed data in reverse order
    op.execute("DELETE FROM notifications.email_templates")
    op.execute("DELETE FROM config.system_parameters")
    op.execute("DELETE FROM config.daily_allowance_rules")
    op.execute("DELETE FROM config.expense_types")
    op.execute("DELETE FROM config.holidays")
    op.execute("DELETE FROM config.leave_types")
