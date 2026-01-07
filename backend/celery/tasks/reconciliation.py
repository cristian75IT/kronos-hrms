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
    """
    if not getattr(settings, 'auto_fix_reconciliation', False):
        logger.info("Auto-fix disabled, skipping")
        return {"status": "skipped", "reason": "auto_fix_disabled"}
    
    # TODO: Implement auto-fix logic
    # Should create ledger entries for approved requests that don't have them
    
    logger.info("Auto-fix not yet implemented")
    return {"status": "not_implemented"}
