"""
KRONOS Email Template Seeder

Run this script to seed the database with default email templates.
Usage:
    python -m scripts.seed_templates

Templates are synced to Brevo when created if brevo_template_id is not set.
"""
import asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.core.config import settings
from src.services.notifications.models import EmailTemplate, NotificationType


# Default templates with professional HTML content
DEFAULT_TEMPLATES = [
    {
        "code": "generic_notification",
        "name": "Notifica Generica",
        "description": "Template generico per notifiche di sistema",
        "notification_type": NotificationType.INFO.value,
        "subject": "{{title}}",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; }
        .header h1 { color: white; margin: 0; font-size: 24px; }
        .content { background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px; }
        .btn { display: inline-block; background: #4f46e5; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>KRONOS HR</h1>
        </div>
        <div class="content">
            <h2>{{title}}</h2>
            <p>{{message}}</p>
            {{#action_url}}
            <p style="text-align: center; margin-top: 30px;">
                <a href="{{action_url}}" class="btn">Vai all'applicazione</a>
            </p>
            {{/action_url}}
        </div>
        <div class="footer">
            <p>Questa email è stata inviata automaticamente da KRONOS HR.</p>
            <p>© 2024 KRONOS - Sistema di Gestione Presenze</p>
        </div>
    </div>
</body>
</html>
""",
        "text_content": "{{title}}\n\n{{message}}\n\n---\nKRONOS HR - Sistema di Gestione Presenze",
        "available_variables": ["title", "message", "action_url"],
    },
    {
        "code": "leave_request_submitted",
        "name": "Richiesta Ferie Inviata",
        "description": "Conferma invio richiesta ferie",
        "notification_type": NotificationType.LEAVE_REQUEST_SUBMITTED.value,
        "subject": "Richiesta Ferie Inviata - {{leave_type}}",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; }
        .header h1 { color: white; margin: 0; }
        .content { background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }
        .info-box { background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 12px 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ Richiesta Ferie Inviata</h1>
        </div>
        <div class="content">
            <p>La tua richiesta di <strong>{{leave_type}}</strong> è stata inviata con successo.</p>
            <div class="info-box">
                <p><strong>Periodo:</strong> dal {{start_date}} al {{end_date}}</p>
                <p><strong>Giorni richiesti:</strong> {{days_requested}}</p>
            </div>
            <p>Riceverai una notifica quando la richiesta sarà approvata o rifiutata.</p>
        </div>
        <div class="footer">
            <p>KRONOS HR - Sistema di Gestione Presenze</p>
        </div>
    </div>
</body>
</html>
""",
        "text_content": "Richiesta Ferie Inviata\n\nLa tua richiesta di {{leave_type}} è stata inviata.\nPeriodo: {{start_date}} - {{end_date}}\nGiorni: {{days_requested}}\n\nRiceverai notifica sull'esito.",
        "available_variables": ["leave_type", "start_date", "end_date", "days_requested"],
    },
    {
        "code": "leave_request_approved",
        "name": "Ferie Approvate",
        "description": "Notifica approvazione ferie",
        "notification_type": NotificationType.LEAVE_REQUEST_APPROVED.value,
        "subject": "✅ Ferie Approvate - {{leave_type}}",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #059669, #10b981); padding: 30px; border-radius: 12px 12px 0 0; }
        .header h1 { color: white; margin: 0; }
        .content { background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }
        .success-box { background: #ecfdf5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 12px 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Ferie Approvate!</h1>
        </div>
        <div class="content">
            <p>Ottime notizie! La tua richiesta di <strong>{{leave_type}}</strong> è stata approvata.</p>
            <div class="success-box">
                <p><strong>Periodo approvato:</strong> dal {{start_date}} al {{end_date}}</p>
                <p><strong>Giorni:</strong> {{days_requested}}</p>
            </div>
            <p>Buon riposo! 🏖️</p>
        </div>
        <div class="footer">
            <p>KRONOS HR - Sistema di Gestione Presenze</p>
        </div>
    </div>
</body>
</html>
""",
        "text_content": "Ferie Approvate!\n\nLa tua richiesta di {{leave_type}} è stata approvata.\nPeriodo: {{start_date}} - {{end_date}}\n\nBuon riposo!",
        "available_variables": ["leave_type", "start_date", "end_date", "days_requested"],
    },
    {
        "code": "leave_request_rejected",
        "name": "Ferie Rifiutate",
        "description": "Notifica rifiuto ferie con motivazione",
        "notification_type": NotificationType.LEAVE_REQUEST_REJECTED.value,
        "subject": "❌ Richiesta Ferie Rifiutata",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #dc2626, #ef4444); padding: 30px; border-radius: 12px 12px 0 0; }
        .header h1 { color: white; margin: 0; }
        .content { background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }
        .error-box { background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 12px 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Richiesta Rifiutata</h1>
        </div>
        <div class="content">
            <p>Purtroppo la tua richiesta di <strong>{{leave_type}}</strong> è stata rifiutata.</p>
            <div class="error-box">
                <p><strong>Motivo:</strong> {{rejection_reason}}</p>
            </div>
            <p>Puoi contattare il tuo responsabile per maggiori informazioni o inviare una nuova richiesta per date alternative.</p>
        </div>
        <div class="footer">
            <p>KRONOS HR - Sistema di Gestione Presenze</p>
        </div>
    </div>
</body>
</html>
""",
        "text_content": "Richiesta Ferie Rifiutata\n\nLa richiesta di {{leave_type}} è stata rifiutata.\nMotivo: {{rejection_reason}}\n\nContatta il tuo responsabile per maggiori informazioni.",
        "available_variables": ["leave_type", "rejection_reason", "start_date", "end_date"],
    },
    {
        "code": "compliance_alert",
        "name": "Avviso Compliance",
        "description": "Notifica per problemi di conformità",
        "notification_type": NotificationType.COMPLIANCE_ALERT.value,
        "subject": "⚠️ Avviso Compliance: {{alert_title}}",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #d97706, #f59e0b); padding: 30px; border-radius: 12px 12px 0 0; }
        .header h1 { color: white; margin: 0; }
        .content { background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }
        .warning-box { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 12px 12px; }
        .btn { display: inline-block; background: #d97706; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Avviso Compliance</h1>
        </div>
        <div class="content">
            <h2>{{alert_title}}</h2>
            <div class="warning-box">
                <p>{{alert_message}}</p>
            </div>
            <p>Questo avviso richiede la tua attenzione. Accedi a KRONOS per verificare e risolvere la situazione.</p>
            <p style="text-align: center; margin-top: 30px;">
                <a href="{{action_url}}" class="btn">Verifica Ora</a>
            </p>
        </div>
        <div class="footer">
            <p>KRONOS HR - Sistema di Gestione Presenze</p>
        </div>
    </div>
</body>
</html>
""",
        "text_content": "Avviso Compliance: {{alert_title}}\n\n{{alert_message}}\n\nAccedi a KRONOS per verificare.",
        "available_variables": ["alert_title", "alert_message", "action_url"],
    },
    {
        "code": "system_announcement",
        "name": "Annuncio di Sistema",
        "description": "Comunicazioni aziendali e annunci",
        "notification_type": NotificationType.SYSTEM_ANNOUNCEMENT.value,
        "subject": "📢 {{title}}",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; }
        .header h1 { color: white; margin: 0; }
        .content { background: #fff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 12px 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📢 Comunicazione Aziendale</h1>
        </div>
        <div class="content">
            <h2>{{title}}</h2>
            <div style="white-space: pre-wrap;">{{message}}</div>
        </div>
        <div class="footer">
            <p>KRONOS HR - Sistema di Gestione Presenze</p>
        </div>
    </div>
</body>
</html>
""",
        "text_content": "{{title}}\n\n{{message}}\n\n---\nKRONOS HR",
        "available_variables": ["title", "message"],
    },
]


async def seed_templates():
    """Seed default email templates."""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        created = 0
        skipped = 0
        
        for tmpl_data in DEFAULT_TEMPLATES:
            # Check if template exists
            result = await session.execute(
                select(EmailTemplate).where(EmailTemplate.code == tmpl_data["code"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"⏭️  Template '{tmpl_data['code']}' already exists, skipping...")
                skipped += 1
                continue
            
            # Create template
            template = EmailTemplate(
                id=uuid4(),
                code=tmpl_data["code"],
                name=tmpl_data["name"],
                description=tmpl_data["description"],
                notification_type=tmpl_data["notification_type"],
                subject=tmpl_data["subject"],
                html_content=tmpl_data["html_content"],
                text_content=tmpl_data["text_content"],
                available_variables=tmpl_data["available_variables"],
                is_active=True,
            )
            session.add(template)
            created += 1
            print(f"✅ Created template: {tmpl_data['code']}")
        
        await session.commit()
        print(f"\n📧 Template seeding complete: {created} created, {skipped} skipped")


if __name__ == "__main__":
    asyncio.run(seed_templates())
