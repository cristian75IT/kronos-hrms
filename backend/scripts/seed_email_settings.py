
import asyncio
import logging
from sqlalchemy import select
from src.core.database import get_db_context
from src.services.notifications.models import EmailProviderSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_email_settings():
    async with get_db_context() as session:
        try:
            # Check if brevo settings exist
            result = await session.execute(
                select(EmailProviderSettings).where(EmailProviderSettings.provider == "brevo")
            )
            existing = result.scalars().first()
            
            if existing:
                logger.info(f"Email settings for provider '{existing.provider}' (ID: {existing.id}) already exist. Active: {existing.is_active}. Skipping seed.")
                return

            logger.info("Creating default 'brevo' email provider settings...")
            settings = EmailProviderSettings(
                provider="brevo",
                api_key="xkeysib-placeholder-key", # Placeholder
                sender_email="noreply@kronos-hrms.com",
                sender_name="KRONOS HR",
                is_active=True,
                test_mode=True, # Safety first
                daily_limit=100
            )
            
            session.add(settings)
            await session.commit()
            logger.info("Default Brevo email settings seeded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to seed email settings: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_email_settings())
