from datetime import date
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    GeneratedReport,
    DailySnapshot,
    HRAlert,
    EmployeeMonthlyStats,
    TrainingRecord,
    MedicalRecord,
    SafetyCompliance,
    ReportStatus
)
from sqlalchemy import select, and_, desc, func, or_
from src.core.exceptions import NotFoundError


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class ReportRepository(BaseRepository):
    async def get_cached(
        self,
        report_type: str,
        period_start: date,
        department_id: Optional[UUID] = None
    ) -> Optional[GeneratedReport]:
        conditions = [
            GeneratedReport.report_type == report_type,
            GeneratedReport.period_start == period_start,
            GeneratedReport.status == ReportStatus.COMPLETED.value,
        ]
        
        if department_id:
            conditions.append(GeneratedReport.department_id == department_id)
        else:
            conditions.append(GeneratedReport.department_id.is_(None))
        
        stmt = select(GeneratedReport).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, report: GeneratedReport) -> GeneratedReport:
        self.session.add(report)
        await self.session.flush()
        return report

    async def get(self, id: UUID) -> Optional[GeneratedReport]:
        return await self.session.get(GeneratedReport, id)


class DailySnapshotRepository(BaseRepository):
    async def get_by_date(self, snapshot_date: date) -> Optional[DailySnapshot]:
        stmt = select(DailySnapshot).where(DailySnapshot.snapshot_date == snapshot_date)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, snapshot: DailySnapshot) -> DailySnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def update(self, snapshot: DailySnapshot) -> DailySnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot


class HRAlertRepository(BaseRepository):
    async def get_active(self, limit: int = 50) -> Sequence[HRAlert]:
        stmt = (
            select(HRAlert)
            .where(HRAlert.is_active == True)
            .order_by(
                HRAlert.severity.desc(),
                HRAlert.created_at.desc(),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, id: UUID) -> Optional[HRAlert]:
        return await self.session.get(HRAlert, id)

    async def create(self, alert: HRAlert) -> HRAlert:
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def update(self, alert: HRAlert) -> HRAlert:
        self.session.add(alert)
        await self.session.flush()
        return alert


class EmployeeMonthlyStatsRepository(BaseRepository):
    async def get(self, employee_id: UUID, year: int, month: int) -> Optional[EmployeeMonthlyStats]:
        stmt = select(EmployeeMonthlyStats).where(
            EmployeeMonthlyStats.employee_id == employee_id,
            EmployeeMonthlyStats.year == year,
            EmployeeMonthlyStats.month == month
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, stats: EmployeeMonthlyStats) -> EmployeeMonthlyStats:
        self.session.add(stats)
        await self.session.flush()
        return stats


class TrainingRecordRepository(BaseRepository):
    async def get_by_employee(self, employee_id: UUID) -> Sequence[TrainingRecord]:
        stmt = select(TrainingRecord).where(TrainingRecord.employee_id == employee_id).order_by(desc(TrainingRecord.training_date))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, id: UUID) -> Optional[TrainingRecord]:
        return await self.session.get(TrainingRecord, id)

    async def create(self, record: TrainingRecord) -> TrainingRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def update(self, id: UUID, **kwargs) -> Optional[TrainingRecord]:
        record = await self.get(id)
        if not record:
            return None
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        await self.session.flush()
        return record

    async def delete(self, id: UUID) -> bool:
        record = await self.get(id)
        if not record:
            return False
        await self.session.delete(record)
        await self.session.flush()
        return True

    async def get_expiring_count(self, today: date, threshold: date) -> int:
        stmt = select(func.count()).select_from(TrainingRecord).where(
            and_(
                TrainingRecord.expiry_date <= threshold,
                TrainingRecord.expiry_date >= today,
                TrainingRecord.status != "scaduto"
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_expired_count(self, today: date) -> int:
        stmt = select(func.count()).select_from(TrainingRecord).where(
            and_(
                TrainingRecord.expiry_date < today,
                TrainingRecord.status != "programmato"
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_compliance_by_type(self) -> dict:
        stmt = select(
            TrainingRecord.training_type,
            func.count()
        ).where(
            TrainingRecord.status == "valido"
        ).group_by(TrainingRecord.training_type)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def get_expiring(self, today: date, threshold: date) -> Sequence[TrainingRecord]:
        stmt = select(TrainingRecord).where(
            and_(
                TrainingRecord.expiry_date <= threshold,
                TrainingRecord.expiry_date >= today,
                TrainingRecord.status != "scaduto"
            )
        ).order_by(TrainingRecord.expiry_date)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_datatable(
        self,
        start: int,
        length: int,
        search_value: Optional[str] = None,
        order_column: Optional[str] = None,
        order_dir: str = "asc"
    ) -> Sequence[TrainingRecord]:
        query = select(TrainingRecord)
        if search_value:
            query = query.where(
                or_(
                    TrainingRecord.training_name.ilike(f"%{search_value}%"),
                    TrainingRecord.training_type.ilike(f"%{search_value}%"),
                )
            )
        
        if order_column == "training_date":
            query = query.order_by(desc(TrainingRecord.training_date) if order_dir == "desc" else TrainingRecord.training_date)
        elif order_column == "expiry_date":
            query = query.order_by(desc(TrainingRecord.expiry_date) if order_dir == "desc" else TrainingRecord.expiry_date)
        else:
            query = query.order_by(desc(TrainingRecord.created_at))
            
        query = query.offset(start).limit(length)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_total_count(self) -> int:
        stmt = select(func.count()).select_from(TrainingRecord)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_filtered_count(self, search_value: str) -> int:
        query = select(func.count()).select_from(TrainingRecord)
        if search_value:
            query = query.where(
                or_(
                    TrainingRecord.training_name.ilike(f"%{search_value}%"),
                    TrainingRecord.training_type.ilike(f"%{search_value}%"),
                )
            )
        result = await self.session.execute(query)
        return result.scalar() or 0


class MedicalRecordRepository(BaseRepository):
    async def get_by_employee(self, employee_id: UUID) -> Sequence[MedicalRecord]:
        stmt = select(MedicalRecord).where(MedicalRecord.employee_id == employee_id).order_by(desc(MedicalRecord.visit_date))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, id: UUID) -> Optional[MedicalRecord]:
        return await self.session.get(MedicalRecord, id)

    async def create(self, record: MedicalRecord) -> MedicalRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def update(self, id: UUID, **kwargs) -> Optional[MedicalRecord]:
        record = await self.get(id)
        if not record:
            return None
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        await self.session.flush()
        return record

    async def delete(self, id: UUID) -> bool:
        record = await self.get(id)
        if not record:
            return False
        await self.session.delete(record)
        await self.session.flush()
        return True

    async def get_due_count(self, today: date, threshold: date) -> int:
        stmt = select(func.count()).select_from(MedicalRecord).where(
            and_(
                MedicalRecord.next_visit_date <= threshold,
                MedicalRecord.next_visit_date >= today
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class SafetyComplianceRepository(BaseRepository):
    async def get_by_employee(self, employee_id: UUID) -> Optional[SafetyCompliance]:
        stmt = select(SafetyCompliance).where(SafetyCompliance.employee_id == employee_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[SafetyCompliance]:
        stmt = select(SafetyCompliance)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_or_update(self, compliance: SafetyCompliance) -> SafetyCompliance:
        self.session.add(compliance)
        await self.session.flush()
        return compliance
