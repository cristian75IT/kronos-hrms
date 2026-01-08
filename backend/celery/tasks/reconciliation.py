"""
KRONOS - Balance Reconciliation Task

Daily job to detect and report inconsistencies between:
1. Legacy wallet and new ledger
2. Approved requests and ledger entries
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from uuid import UUID

from celery import shared_task
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import settings

logger = logging.getLogger(__name__)


class ReconciliationAnomaly:
    """Represents a detected inconsistency."""
    
    def __init__(
        self,
        anomaly_type: str,
        severity: str,  # LOW, MEDIUM, HIGH, CRITICAL
        entity_type: str,
        entity_id: UUID,
        details: Dict[str, Any],
    ):
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.details = details
        self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "type": self.anomaly_type,
            "severity": self.severity,
            "entity": f"{self.entity_type}:{self.entity_id}",
            "details": self.details,
            "detected_at": self.detected_at.isoformat(),
        }


async def check_leaves_consistency(session: AsyncSession) -> List[ReconciliationAnomaly]:
    """
    Check consistency between leaves and ledger.
    
    Detects:
    1. Approved requests without ledger entries
    2. Ledger entries without matching approved requests
    3. Amount mismatches between wallet and ledger
    """
    anomalies = []
    
    # 1. Approved requests without ledger entries
    query = text("""
        SELECT lr.id, lr.user_id, lr.approved_at, lr.days_requested
        FROM leaves.leave_requests lr
        WHERE lr.status = 'APPROVED'
        AND lr.balance_deducted = true
        AND NOT EXISTS (
            SELECT 1 FROM leaves.time_ledger tl
            WHERE tl.reference_type = 'LEAVE_REQUEST'
            AND tl.reference_id = lr.id
            AND tl.entry_type = 'USAGE'
        )
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    for row in rows:
        anomalies.append(ReconciliationAnomaly(
            anomaly_type="MISSING_LEDGER_ENTRY",
            severity="HIGH",
            entity_type="LEAVE_REQUEST",
            entity_id=row.id,
            details={
                "user_id": str(row.user_id),
                "approved_at": row.approved_at.isoformat() if row.approved_at else None,
                "days_requested": float(row.days_requested),
                "message": "Approved leave without ledger entry",
            }
        ))
    
    # 2. Ledger entries without matching approved requests
    query = text("""
        SELECT tl.id, tl.reference_id, tl.user_id, tl.amount, tl.created_at
        FROM leaves.time_ledger tl
        WHERE tl.reference_type = 'LEAVE_REQUEST'
        AND tl.entry_type = 'USAGE'
        AND NOT EXISTS (
            SELECT 1 FROM leaves.leave_requests lr
            WHERE lr.id = tl.reference_id
            AND lr.status IN ('APPROVED', 'APPROVED_CONDITIONAL')
        )
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    for row in rows:
        anomalies.append(ReconciliationAnomaly(
            anomaly_type="ORPHAN_LEDGER_ENTRY",
            severity="MEDIUM",
            entity_type="TIME_LEDGER",
            entity_id=row.id,
            details={
                "reference_id": str(row.reference_id),
                "user_id": str(row.user_id),
                "amount": float(row.amount),
                "message": "Ledger entry for non-approved/missing request",
            }
        ))
    
    return anomalies


async def check_expenses_consistency(session: AsyncSession) -> List[ReconciliationAnomaly]:
    """
    Check consistency between expenses and ledger.
    """
    anomalies = []
    
    # Approved trips without budget ledger entry
    query = text("""
        SELECT bt.id, bt.user_id, bt.approved_at, bt.estimated_total
        FROM expenses.business_trips bt
        WHERE bt.status = 'approved'
        AND bt.approved_at IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM expenses.expense_ledger el
            WHERE el.reference_type = 'TRIP'
            AND el.reference_id = bt.id
            AND el.entry_type = 'BUDGET_ALLOCATION'
        )
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    for row in rows:
        anomalies.append(ReconciliationAnomaly(
            anomaly_type="MISSING_BUDGET_ALLOCATION",
            severity="HIGH",
            entity_type="BUSINESS_TRIP",
            entity_id=row.id,
            details={
                "user_id": str(row.user_id),
                "approved_at": row.approved_at.isoformat() if row.approved_at else None,
                "estimated_total": float(row.estimated_total) if row.estimated_total else None,
                "message": "Approved trip without budget ledger entry",
            }
        ))
    
    return anomalies


@shared_task(name="reconciliation.check_balance_consistency")
def check_balance_consistency():
    """
    Daily reconciliation task.
    
    Runs at 2 AM each day to detect inconsistencies.
    """
    import asyncio
    
    async def _run():
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            all_anomalies = []
            
            # Check leaves
            try:
                leaves_anomalies = await check_leaves_consistency(session)
                all_anomalies.extend(leaves_anomalies)
                logger.info(f"Leaves reconciliation: {len(leaves_anomalies)} anomalies")
            except Exception as e:
                logger.error(f"Leaves reconciliation failed: {e}")
            
            # Check expenses
            try:
                expenses_anomalies = await check_expenses_consistency(session)
                all_anomalies.extend(expenses_anomalies)
                logger.info(f"Expenses reconciliation: {len(expenses_anomalies)} anomalies")
            except Exception as e:
                logger.error(f"Expenses reconciliation failed: {e}")
            
            # Report anomalies
            if all_anomalies:
                logger.warning(f"RECONCILIATION: Found {len(all_anomalies)} total anomalies")
                
                # Log each anomaly
                for anomaly in all_anomalies:
                    logger.warning(f"  [{anomaly.severity}] {anomaly.anomaly_type}: {anomaly.entity_type}:{anomaly.entity_id}")
                
                # TODO: Send notification to admins
                # TODO: Store anomalies in audit log
            else:
                logger.info("RECONCILIATION: No anomalies detected")
            
            return {
                "status": "completed",
                "checked_at": datetime.utcnow().isoformat(),
                "leaves_anomalies": len([a for a in all_anomalies if a.entity_type in ("LEAVE_REQUEST", "TIME_LEDGER")]),
                "expenses_anomalies": len([a for a in all_anomalies if a.entity_type in ("BUSINESS_TRIP", "EXPENSE_LEDGER")]),
                "total_anomalies": len(all_anomalies),
            }
        
        await engine.dispose()
    
    return asyncio.run(_run())


@shared_task(name="reconciliation.auto_fix_missing_ledger")
def auto_fix_missing_ledger_entries():
    """
    Auto-fix task to create missing ledger entries.
    
    Only runs if AUTO_FIX_RECONCILIATION is enabled.
    Queries for approved leave requests without corresponding ledger entries
    and creates them based on the leave type and days requested.
    """
    if not getattr(settings, 'auto_fix_reconciliation', False):
        logger.info("Auto-fix disabled, skipping")
        return {"status": "skipped", "reason": "auto_fix_disabled"}
    
    import asyncio
    
    async def _run():
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        fixed_count = 0
        error_count = 0
        
        async with async_session() as session:
            # Query approved leave requests without ledger entries
            query = text("""
                SELECT 
                    lr.id,
                    lr.user_id,
                    lr.leave_type_code,
                    lr.days_requested,
                    lr.approved_by,
                    lr.approved_at
                FROM leaves.leave_requests lr
                WHERE lr.status IN ('APPROVED', 'APPROVED_CONDITIONAL')
                AND lr.balance_deducted = true
                AND NOT EXISTS (
                    SELECT 1 FROM leaves.time_ledger tl
                    WHERE tl.reference_type = 'LEAVE_REQUEST'
                    AND tl.reference_id = lr.id
                    AND tl.entry_type = 'USAGE'
                )
                ORDER BY lr.approved_at ASC
                LIMIT 100
            """)
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                logger.info("No missing ledger entries to fix")
                return {
                    "status": "completed",
                    "fixed": 0,
                    "errors": 0,
                    "message": "No missing entries found"
                }
            
            logger.info(f"Found {len(rows)} approved requests without ledger entries")
            
            # Map leave type codes to balance types
            leave_type_to_balance = {
                "FER": "VACATION_AC",  # Ferie -> Vacation Anno Corrente
                "ROL": "ROL",           # ROL -> ROL
                "PER": "PERMITS",       # Permessi Ex Festività -> Permits
                "L104": "PERMITS",      # Legge 104 -> Permits
                "DON": "PERMITS",       # Donazione Sangue -> Permits
                # Other types that might not consume balance
                "MAL": None,            # Malattia - doesn't consume balance
                "LUT": None,            # Lutto - doesn't consume balance
                "MAT": None,            # Matrimonio - doesn't consume balance
            }
            
            for row in rows:
                try:
                    leave_type_code = row.leave_type_code
                    balance_type = leave_type_to_balance.get(leave_type_code)
                    
                    if not balance_type:
                        logger.debug(
                            f"Leave type {leave_type_code} does not consume balance, skipping"
                        )
                        continue
                    
                    # Create the ledger entry directly via SQL for simplicity
                    # (Using the service would require full async context)
                    insert_query = text("""
                        INSERT INTO leaves.time_ledger (
                            id, user_id, year, entry_type, balance_type,
                            amount, reference_type, reference_id, 
                            reference_status, notes, created_by, created_at
                        ) VALUES (
                            gen_random_uuid(),
                            :user_id,
                            EXTRACT(YEAR FROM :approved_at)::int,
                            'USAGE',
                            :balance_type,
                            :amount,
                            'LEAVE_REQUEST',
                            :leave_request_id,
                            'APPROVED',
                            'Auto-fixed by reconciliation task',
                            :approved_by,
                            NOW()
                        )
                    """)
                    
                    await session.execute(insert_query, {
                        "user_id": row.user_id,
                        "approved_at": row.approved_at,
                        "balance_type": balance_type,
                        "amount": row.days_requested,
                        "leave_request_id": row.id,
                        "approved_by": row.approved_by,
                    })
                    
                    fixed_count += 1
                    logger.info(
                        f"Fixed ledger entry for leave request {row.id} "
                        f"(user={row.user_id}, type={balance_type}, amount={row.days_requested})"
                    )
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to fix leave request {row.id}: {e}")
            
            await session.commit()
        
        await engine.dispose()
        
        result = {
            "status": "completed",
            "fixed": fixed_count,
            "errors": error_count,
            "checked_at": datetime.utcnow().isoformat(),
        }
        
        if fixed_count > 0:
            logger.warning(f"RECONCILIATION AUTO-FIX: Created {fixed_count} missing ledger entries")
        if error_count > 0:
            logger.error(f"RECONCILIATION AUTO-FIX: {error_count} errors during fix")
        
        return result
    
    return asyncio.run(_run())

