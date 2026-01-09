"""Signature Service Repository.

Enterprise-grade data access layer with:
- Pagination support
- Type-safe queries using SQLAlchemy 2.0 patterns
- Efficient counting for pagination metadata
"""
from uuid import UUID
from typing import Optional, List, TypedDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.signature.models import SignatureTransaction


class PaginatedResult(TypedDict):
    """Type-safe result for paginated queries."""
    items: List[SignatureTransaction]
    total: int


class SignatureRepository:
    """Repository for SignatureTransaction entities."""
    
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, transaction: SignatureTransaction) -> SignatureTransaction:
        """
        Persist a new signature transaction.
        
        The transaction is immutable after creation - no update method is provided.
        """
        self._session.add(transaction)
        await self._session.flush()
        await self._session.refresh(transaction)
        return transaction

    async def get(self, id: UUID) -> Optional[SignatureTransaction]:
        """Get a signature transaction by ID."""
        return await self._session.get(SignatureTransaction, id)

    async def get_by_document(
        self, 
        document_type: str, 
        document_id: str
    ) -> List[SignatureTransaction]:
        """
        Get signature history for a specific document.
        
        Returns all signatures for the given document, ordered by date (newest first).
        """
        stmt = (
            select(SignatureTransaction)
            .where(
                SignatureTransaction.document_type == document_type,
                SignatureTransaction.document_id == document_id
            )
            .order_by(SignatureTransaction.signed_at.desc())
        )
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user(self, user_id: UUID) -> List[SignatureTransaction]:
        """
        Get all signatures performed by a specific user.
        
        Returns all signatures, ordered by date (newest first).
        No pagination - use get_by_user_paginated for large result sets.
        """
        stmt = (
            select(SignatureTransaction)
            .where(SignatureTransaction.user_id == user_id)
            .order_by(SignatureTransaction.signed_at.desc())
        )
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_paginated(
        self, 
        user_id: UUID,
        offset: int = 0,
        limit: int = 25
    ) -> PaginatedResult:
        """
        Get signatures for a user with pagination.
        
        Args:
            user_id: The user's UUID
            offset: Number of records to skip (0-indexed)
            limit: Maximum number of records to return
            
        Returns:
            PaginatedResult with items and total count
        """
        # Count query
        count_stmt = (
            select(func.count())
            .select_from(SignatureTransaction)
            .where(SignatureTransaction.user_id == user_id)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Data query with pagination
        data_stmt = (
            select(SignatureTransaction)
            .where(SignatureTransaction.user_id == user_id)
            .order_by(SignatureTransaction.signed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        data_result = await self._session.execute(data_stmt)
        items = list(data_result.scalars().all())

        return {"items": items, "total": total}

    async def count_by_user(self, user_id: UUID) -> int:
        """Count total signatures for a user."""
        stmt = (
            select(func.count())
            .select_from(SignatureTransaction)
            .where(SignatureTransaction.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: UUID) -> bool:
        """Check if a signature transaction exists."""
        stmt = (
            select(func.count())
            .select_from(SignatureTransaction)
            .where(SignatureTransaction.id == id)
        )
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0
