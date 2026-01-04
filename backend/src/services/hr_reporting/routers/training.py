"""
KRONOS HR Reporting Service - Training Router.

API endpoints for training and safety management (D.Lgs. 81/08).
"""
from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_hr, TokenPayload

from ..models import TrainingRecord, MedicalRecord, SafetyCompliance
from ..schemas import (
    TrainingRecordCreate,
    TrainingRecordUpdate,
    TrainingRecordResponse,
    MedicalRecordCreate,
    MedicalRecordUpdate,
    MedicalRecordResponse,
    SafetyComplianceResponse,
    TrainingOverviewResponse,
    TrainingExpiringItem,
    DataTableRequest,
    DataTableResponse,
)

router = APIRouter(prefix="/training", tags=["Training & Safety"])


# ═══════════════════════════════════════════════════════════
# Training Records CRUD
# ═══════════════════════════════════════════════════════════

@router.get("/overview", response_model=TrainingOverviewResponse)
async def get_training_overview(
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get training overview for all employees."""
    today = date.today()
    threshold_30_days = today + timedelta(days=30)
    
    # Get all compliance records
    result = await session.execute(
        select(SafetyCompliance)
    )
    all_compliance = result.scalars().all()
    
    # Calculate stats
    fully_compliant = sum(1 for c in all_compliance if c.is_compliant and c.compliance_score >= 90)
    partially_compliant = sum(1 for c in all_compliance if c.is_compliant and c.compliance_score < 90)
    non_compliant = sum(1 for c in all_compliance if not c.is_compliant)
    
    # Count expiring trainings
    expiring_result = await session.execute(
        select(func.count()).select_from(TrainingRecord).where(
            and_(
                TrainingRecord.expiry_date <= threshold_30_days,
                TrainingRecord.expiry_date >= today,
                TrainingRecord.status != "scaduto"
            )
        )
    )
    trainings_expiring = expiring_result.scalar() or 0
    
    # Count expired trainings
    expired_result = await session.execute(
        select(func.count()).select_from(TrainingRecord).where(
            and_(
                TrainingRecord.expiry_date < today,
                TrainingRecord.status != "programmato"
            )
        )
    )
    trainings_expired = expired_result.scalar() or 0
    
    # Count medical visits due
    medical_due_result = await session.execute(
        select(func.count()).select_from(MedicalRecord).where(
            and_(
                MedicalRecord.next_visit_date <= threshold_30_days,
                MedicalRecord.next_visit_date >= today
            )
        )
    )
    medical_visits_due = medical_due_result.scalar() or 0
    
    # Compliance by type
    type_result = await session.execute(
        select(
            TrainingRecord.training_type,
            func.count()
        ).where(
            TrainingRecord.status == "valido"
        ).group_by(TrainingRecord.training_type)
    )
    compliance_by_type = {row[0]: row[1] for row in type_result.all()}
    
    # Fetch employee names from auth service
    try:
        from src.shared.clients import AuthClient
        auth_client = AuthClient()
        users = await auth_client.get_users()
        user_map = {u["id"]: f"{u['first_name']} {u['last_name']}" for u in users}
    except Exception as e:
        logger.error(f"Error fetching users for training overview: {e}")
        user_map = {}

    # Format employees list
    employees = []
    for c in all_compliance:
        employee_id_str = str(c.employee_id)
        employees.append(SafetyComplianceResponse(
            id=c.id,
            employee_id=c.employee_id,
            employee_name=user_map.get(employee_id_str, "Dipendente Sconosciuto"),
            is_compliant=c.is_compliant,
            compliance_score=c.compliance_score,
            has_formazione_generale=c.has_formazione_generale,
            has_formazione_specifica=c.has_formazione_specifica,
            trainings_expiring_soon=c.trainings_expiring_soon,
            trainings_expired=c.trainings_expired,
            medical_fitness_valid=c.medical_fitness_valid,
            medical_next_visit=c.medical_next_visit,
            medical_restrictions=c.medical_restrictions,
            last_check_date=c.last_check_date,
            issues=c.issues,
            updated_at=c.updated_at,
        ))
    
    return TrainingOverviewResponse(
        total_employees=len(all_compliance),
        fully_compliant=fully_compliant,
        partially_compliant=partially_compliant,
        non_compliant=non_compliant,
        trainings_expiring_30_days=trainings_expiring,
        trainings_expired=trainings_expired,
        medical_visits_due=medical_visits_due,
        compliance_by_type=compliance_by_type,
        employees=employees,
    )


@router.get("/expiring", response_model=List[TrainingExpiringItem])
async def get_expiring_trainings(
    days: int = Query(default=60, ge=1, le=365),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get trainings expiring within specified days."""
    today = date.today()
    threshold = today + timedelta(days=days)
    
    result = await session.execute(
        select(TrainingRecord).where(
            and_(
                TrainingRecord.expiry_date <= threshold,
                TrainingRecord.expiry_date >= today,
                TrainingRecord.status != "scaduto"
            )
        ).order_by(TrainingRecord.expiry_date)
    )
    # Fetch employee names from auth service
    try:
        from src.shared.clients import AuthClient
        auth_client = AuthClient()
        users = await auth_client.get_users()
        user_map = {u["id"]: f"{u['first_name']} {u['last_name']}" for u in users}
    except Exception as e:
        logger.error(f"Error fetching users for expiring trainings: {e}")
        user_map = {}

    items = []
    for t in trainings:
        items.append(TrainingExpiringItem(
            id=t.id,
            employee_id=t.employee_id,
            employee_name=user_map.get(str(t.employee_id), "Dipendente Sconosciuto"),
            training_type=t.training_type,
            training_name=t.training_name,
            expiry_date=t.expiry_date,
            days_remaining=(t.expiry_date - today).days,
        ))
    
    return items


@router.get("/employee/{employee_id}", response_model=List[TrainingRecordResponse])
async def get_employee_trainings(
    employee_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get all training records for an employee."""
    result = await session.execute(
        select(TrainingRecord)
        .where(TrainingRecord.employee_id == employee_id)
        .order_by(TrainingRecord.training_date.desc())
    )
    trainings = result.scalars().all()
    
    today = date.today()
    response = []
    for t in trainings:
        days_until_expiry = None
        is_expired = False
        is_expiring_soon = False
        
        if t.expiry_date:
            days_until_expiry = (t.expiry_date - today).days
            is_expired = t.expiry_date < today
            is_expiring_soon = 0 <= days_until_expiry <= 60
        
        response.append(TrainingRecordResponse(
            id=t.id,
            employee_id=t.employee_id,
            training_type=t.training_type,
            training_name=t.training_name,
            description=t.description,
            provider_name=t.provider_name,
            provider_code=t.provider_code,
            training_date=t.training_date,
            expiry_date=t.expiry_date,
            hours=t.hours,
            status=t.status,
            certificate_number=t.certificate_number,
            certificate_path=t.certificate_path,
            notes=t.notes,
            recorded_by=t.recorded_by,
            created_at=t.created_at,
            updated_at=t.updated_at,
            days_until_expiry=days_until_expiry,
            is_expired=is_expired,
            is_expiring_soon=is_expiring_soon,
        ))
    
    return response


@router.post("", response_model=TrainingRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_training_record(
    data: TrainingRecordCreate,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Create a new training record."""
    today = date.today()
    
    # Determine initial status
    status_value = "valido"
    if data.expiry_date:
        if data.expiry_date < today:
            status_value = "scaduto"
        elif (data.expiry_date - today).days <= 60:
            status_value = "in_scadenza"
    
    if data.training_date > today:
        status_value = "programmato"
    
    record = TrainingRecord(
        employee_id=data.employee_id,
        training_type=data.training_type,
        training_name=data.training_name,
        description=data.description,
        provider_name=data.provider_name,
        provider_code=data.provider_code,
        training_date=data.training_date,
        expiry_date=data.expiry_date,
        hours=data.hours,
        status=status_value,
        certificate_number=data.certificate_number,
        notes=data.notes,
        recorded_by=current_user.user_id,
    )
    
    session.add(record)
    await session.commit()
    await session.refresh(record)
    
    return TrainingRecordResponse(
        id=record.id,
        employee_id=record.employee_id,
        training_type=record.training_type,
        training_name=record.training_name,
        description=record.description,
        provider_name=record.provider_name,
        provider_code=record.provider_code,
        training_date=record.training_date,
        expiry_date=record.expiry_date,
        hours=record.hours,
        status=record.status,
        certificate_number=record.certificate_number,
        certificate_path=record.certificate_path,
        notes=record.notes,
        recorded_by=record.recorded_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.put("/{training_id}", response_model=TrainingRecordResponse)
async def update_training_record(
    training_id: UUID,
    data: TrainingRecordUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Update a training record."""
    result = await session.execute(
        select(TrainingRecord).where(TrainingRecord.id == training_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    await session.commit()
    await session.refresh(record)
    
    return TrainingRecordResponse(
        id=record.id,
        employee_id=record.employee_id,
        training_type=record.training_type,
        training_name=record.training_name,
        description=record.description,
        provider_name=record.provider_name,
        provider_code=record.provider_code,
        training_date=record.training_date,
        expiry_date=record.expiry_date,
        hours=record.hours,
        status=record.status,
        certificate_number=record.certificate_number,
        certificate_path=record.certificate_path,
        notes=record.notes,
        recorded_by=record.recorded_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.delete("/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_record(
    training_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Delete a training record."""
    result = await session.execute(
        select(TrainingRecord).where(TrainingRecord.id == training_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    
    employee_id = record.employee_id
    
    await session.delete(record)
    await session.commit()


# ═══════════════════════════════════════════════════════════
# Medical Records CRUD
# ═══════════════════════════════════════════════════════════

@router.get("/medical/{employee_id}", response_model=List[MedicalRecordResponse])
async def get_employee_medical_records(
    employee_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get all medical records for an employee."""
    result = await session.execute(
        select(MedicalRecord)
        .where(MedicalRecord.employee_id == employee_id)
        .order_by(MedicalRecord.visit_date.desc())
    )
    records = result.scalars().all()
    
    today = date.today()
    response = []
    for r in records:
        days_until = None
        if r.next_visit_date:
            days_until = (r.next_visit_date - today).days
        
        response.append(MedicalRecordResponse(
            id=r.id,
            employee_id=r.employee_id,
            visit_type=r.visit_type,
            visit_date=r.visit_date,
            next_visit_date=r.next_visit_date,
            fitness_result=r.fitness_result,
            restrictions=r.restrictions,
            doctor_name=r.doctor_name,
            notes=r.notes,
            document_path=r.document_path,
            recorded_by=r.recorded_by,
            created_at=r.created_at,
            updated_at=r.updated_at,
            days_until_next_visit=days_until,
        ))
    
    return response


@router.post("/medical", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    data: MedicalRecordCreate,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Create a new medical record."""
    record = MedicalRecord(
        employee_id=data.employee_id,
        visit_type=data.visit_type,
        visit_date=data.visit_date,
        next_visit_date=data.next_visit_date,
        fitness_result=data.fitness_result,
        restrictions=data.restrictions,
        doctor_name=data.doctor_name,
        notes=data.notes,
        recorded_by=current_user.user_id,
    )
    
    session.add(record)
    await session.commit()
    await session.refresh(record)
    
    return MedicalRecordResponse(
        id=record.id,
        employee_id=record.employee_id,
        visit_type=record.visit_type,
        visit_date=record.visit_date,
        next_visit_date=record.next_visit_date,
        fitness_result=record.fitness_result,
        restrictions=record.restrictions,
        doctor_name=record.doctor_name,
        notes=record.notes,
        document_path=record.document_path,
        recorded_by=record.recorded_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.put("/medical/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: UUID,
    data: MedicalRecordUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Update a medical record."""
    result = await session.execute(
        select(MedicalRecord).where(MedicalRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    await session.commit()
    await session.refresh(record)
    
    return MedicalRecordResponse(
        id=record.id,
        employee_id=record.employee_id,
        visit_type=record.visit_type,
        visit_date=record.visit_date,
        next_visit_date=record.next_visit_date,
        fitness_result=record.fitness_result,
        restrictions=record.restrictions,
        doctor_name=record.doctor_name,
        notes=record.notes,
        document_path=record.document_path,
        recorded_by=record.recorded_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.delete("/medical/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_record(
    record_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Delete a medical record."""
    result = await session.execute(
        select(MedicalRecord).where(MedicalRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    
    employee_id = record.employee_id
    
    await session.delete(record)
    await session.commit()


# ═══════════════════════════════════════════════════════════
# Safety Compliance
# ═══════════════════════════════════════════════════════════

@router.get("/compliance/{employee_id}", response_model=SafetyComplianceResponse)
async def get_employee_compliance(
    employee_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get safety compliance status for an employee."""
    result = await session.execute(
        select(SafetyCompliance).where(SafetyCompliance.employee_id == employee_id)
    )
    compliance = result.scalar_one_or_none()
    
    if not compliance:
        # Return default empty compliance
        return SafetyComplianceResponse(
            id=employee_id,  # Use employee_id as placeholder
            employee_id=employee_id,
            is_compliant=False,
            compliance_score=0,
            has_formazione_generale=False,
            has_formazione_specifica=False,
            trainings_expiring_soon=0,
            trainings_expired=0,
            medical_fitness_valid=False,
            updated_at=date.today(),
        )
    
    return SafetyComplianceResponse(
        id=compliance.id,
        employee_id=compliance.employee_id,
        is_compliant=compliance.is_compliant,
        compliance_score=compliance.compliance_score,
        has_formazione_generale=compliance.has_formazione_generale,
        has_formazione_specifica=compliance.has_formazione_specifica,
        trainings_expiring_soon=compliance.trainings_expiring_soon,
        trainings_expired=compliance.trainings_expired,
        medical_fitness_valid=compliance.medical_fitness_valid,
        medical_next_visit=compliance.medical_next_visit,
        medical_restrictions=compliance.medical_restrictions,
        last_check_date=compliance.last_check_date,
        issues=compliance.issues,
        updated_at=compliance.updated_at,
    )


@router.get("/datatable", response_model=DataTableResponse)
async def get_training_datatable(
    draw: int = Query(default=1),
    start: int = Query(default=0),
    length: int = Query(default=25),
    search_value: Optional[str] = Query(default=None, alias="search[value]"),
    order_column: Optional[str] = Query(default=None),
    order_dir: str = Query(default="asc"),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get training records in DataTable format."""
    # Base query
    query = select(TrainingRecord)
    
    # Search filter
    if search_value:
        query = query.where(
            or_(
                TrainingRecord.training_name.ilike(f"%{search_value}%"),
                TrainingRecord.training_type.ilike(f"%{search_value}%"),
            )
        )
    
    # Get total count
    count_query = select(func.count()).select_from(TrainingRecord)
    total_result = await session.execute(count_query)
    records_total = total_result.scalar() or 0
    
    # Get filtered count
    if search_value:
        filtered_count_query = select(func.count()).select_from(query.subquery())
        filtered_result = await session.execute(filtered_count_query)
        records_filtered = filtered_result.scalar() or 0
    else:
        records_filtered = records_total
    
    # Ordering
    if order_column == "training_date":
        query = query.order_by(
            TrainingRecord.training_date.desc() if order_dir == "desc" 
            else TrainingRecord.training_date
        )
    elif order_column == "expiry_date":
        query = query.order_by(
            TrainingRecord.expiry_date.desc() if order_dir == "desc" 
            else TrainingRecord.expiry_date
        )
    else:
        query = query.order_by(TrainingRecord.created_at.desc())
    
    # Pagination
    query = query.offset(start).limit(length)
    
    result = await session.execute(query)
    records = result.scalars().all()
    
    # Fetch employee names from auth service
    try:
        from src.shared.clients import AuthClient
        auth_client = AuthClient()
        users = await auth_client.get_users()
        user_map = {u["id"]: f"{u['first_name']} {u['last_name']}" for u in users}
    except Exception as e:
        logger.error(f"Error fetching users for training datatable: {e}")
        user_map = {}

    # Format data
    data = []
    today = date.today()
    for r in records:
        days_until = None
        if r.expiry_date:
            days_until = (r.expiry_date - today).days
        
        data.append({
            "id": str(r.id),
            "employee_id": str(r.employee_id),
            "employee_name": user_map.get(str(r.employee_id), "Dipendente Sconosciuto"),
            "training_type": r.training_type,
            "training_name": r.training_name,
            "training_date": r.training_date.isoformat(),
            "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None,
            "status": r.status,
            "days_until_expiry": days_until,
            "hours": r.hours,
        })
    
    return DataTableResponse(
        draw=draw,
        recordsTotal=records_total,
        recordsFiltered=records_filtered,
        data=data,
    )
