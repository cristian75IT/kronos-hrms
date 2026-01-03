import asyncio
import sys
import os
from uuid import UUID, uuid4
from datetime import date, datetime, timedelta
import random

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.hr_reporting.models import TrainingRecord, MedicalRecord, SafetyCompliance

# Fixed UUIDs matching seed_enterprise_data.py
ADMIN_ID = UUID("3a5b855c-e426-42e0-a51a-210fc1ac3f61")
HR_ID = UUID("4b6c966d-f537-53f1-b62b-321fd2bd4372")
STAFF_ID = UUID("5c7d077e-0648-6402-c73c-432ae3ce5a83")

EMPLOYEES = [ADMIN_ID, HR_ID, STAFF_ID]

TRAINING_TYPES = [
    ("SICUREZZA_GEN", "Formazione Generale Lavoratori", 4, 1825), # 5 years
    ("SICUREZZA_SPEC", "Formazione Specifica", 4, 1825), # 5 years
    ("PRIMO_SOCCORSO", "Addetto Primo Soccorso", 12, 1095), # 3 years
    ("ANTINCENDIO", "Addetto Antincendio Liv. 2", 8, 1095), # 3 years
    ("PREPOSTO", "Formazione Preposto", 8, 730), # 2 years
    ("PRIVACY", "GDPR & Privacy Policy", 2, 365) # 1 year
]

async def seed_hr_training():
    print("🚀 Starting HR Training & Safety Seed...")
    async with get_db_context() as session:
        try:
            today = date.today()

            for user_id in EMPLOYEES:
                print(f"   👤 Processing User: {user_id}")
                
                # 1. Create Training Records
                # Give each user 3-5 random trainings
                num_trainings = 4
                
                has_general = False
                has_specific = False
                trainings_expired_count = 0
                trainings_expiring_soon_count = 0
                
                for _ in range(num_trainings):
                    t_code, t_name, t_hours, t_validity_days = random.choice(TRAINING_TYPES)
                    
                    # Randomize date: some old (expired), some recent (valid), some closing to expiry
                    # 10% chance expired, 20% expiring soon, 70% valid
                    rand_val = random.random()
                    
                    if rand_val < 0.1: # Expired
                        training_date = today - timedelta(days=t_validity_days + random.randint(1, 100))
                        status = "scaduto"
                        trainings_expired_count += 1
                    elif rand_val < 0.3: # Expiring soon (within 60 days)
                        # Passed days = validity - random(1, 60)
                        days_passed = t_validity_days - random.randint(1, 60)
                        training_date = today - timedelta(days=days_passed)
                        status = "in_scadenza"
                        trainings_expiring_soon_count += 1
                    else: # Valid
                        training_date = today - timedelta(days=random.randint(1, 300))
                        status = "valido"

                    expiry_date = training_date + timedelta(days=t_validity_days)
                    
                    # Track specific compliances
                    if t_code == "SICUREZZA_GEN" and status != "scaduto":
                        has_general = True
                    if t_code == "SICUREZZA_SPEC" and status != "scaduto":
                        has_specific = True

                    record = TrainingRecord(
                        id=uuid4(),
                        employee_id=user_id,
                        training_type=t_code,
                        training_name=t_name,
                        description=f"Corso {t_name}",
                        provider_name="Safety First Srl",
                        provider_code=f"PROV-{t_code}",
                        training_date=training_date,
                        expiry_date=expiry_date,
                        hours=t_hours,
                        status=status,
                        certificate_number=f"CERT-{uuid4().hex[:8].upper()}",
                        recorded_by=HR_ID
                    )
                    session.add(record)
                
                # 2. Create Medical Records
                # 1 visit per user
                last_visit = today - timedelta(days=random.randint(1, 300))
                next_visit = last_visit + timedelta(days=365)
                
                fitness_valid = next_visit >= today
                
                medical = MedicalRecord(
                    id=uuid4(),
                    employee_id=user_id,
                    visit_type="PERIODICA",
                    visit_date=last_visit,
                    next_visit_date=next_visit,
                    fitness_result="IDONEO",
                    doctor_name="Dott. Rossig",
                    notes="Nessuna limitazione",
                    recorded_by=HR_ID
                )
                session.add(medical)
                
                # 3. Create/Update Safety Compliance
                # Check if exists first
                from sqlalchemy import select
                stmt = select(SafetyCompliance).where(SafetyCompliance.employee_id == user_id)
                res = await session.execute(stmt)
                compliance = res.scalar()
                
                is_compliant = has_general and has_specific and fitness_valid and trainings_expired_count == 0
                score = 100
                if not has_general: score -= 30
                if not has_specific: score -= 30
                if not fitness_valid: score -= 20
                if trainings_expired_count > 0: score -= 10 * trainings_expired_count
                score = max(0, score)
                
                if not compliance:
                    compliance = SafetyCompliance(
                        id=uuid4(),
                        employee_id=user_id,
                        is_compliant=is_compliant,
                        compliance_score=score,
                        has_formazione_generale=has_general,
                        has_formazione_specifica=has_specific,
                        trainings_expiring_soon=trainings_expiring_soon_count,
                        trainings_expired=trainings_expired_count,
                        medical_fitness_valid=fitness_valid,
                        medical_next_visit=next_visit,
                        last_check_date=today,
                        issues=[{"type": "MISSING_TRAINING", "severity": "warning", "description": "Formazione non completa"}] if not is_compliant else []
                    )
                    session.add(compliance)
                else:
                    # Update existing
                    compliance.is_compliant = is_compliant
                    compliance.compliance_score = score
                    compliance.has_formazione_generale = has_general
                    compliance.has_formazione_specifica = has_specific
                    compliance.trainings_expiring_soon = trainings_expiring_soon_count
                    compliance.trainings_expired = trainings_expired_count
                    compliance.medical_fitness_valid = fitness_valid
                    compliance.medical_next_visit = next_visit
                    compliance.last_check_date = today

            await session.commit()
            print("\n✨ HR Training Seed Completed Successfully!")

        except Exception as e:
            print(f"\n❌ Error seeding HR Training: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_hr_training())
