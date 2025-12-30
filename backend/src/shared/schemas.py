"""KRONOS Backend - Shared Schemas."""
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


# Generic type for paginated responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = {"from_attributes": True}


class TimestampMixin(BaseModel):
    """Mixin for created_at/updated_at fields."""
    
    created_at: datetime
    updated_at: datetime


class IDMixin(BaseModel):
    """Mixin for UUID id field."""
    
    id: UUID


# ═══════════════════════════════════════════════════════════
# DataTables Server-Side Processing
# ═══════════════════════════════════════════════════════════

class DataTableColumn(BaseModel):
    """DataTables column definition."""
    
    data: str
    name: str = ""
    searchable: bool = True
    orderable: bool = True
    search: dict = Field(default_factory=lambda: {"value": "", "regex": False})


class DataTableOrder(BaseModel):
    """DataTables order definition."""
    
    column: int
    dir: str = "asc"


class DataTableRequest(BaseModel):
    """DataTables server-side request.
    
    This is the standard format sent by DataTables.net
    when serverSide: true is enabled.
    """
    
    draw: int = Field(..., description="Draw counter for async requests")
    start: int = Field(default=0, description="First record offset")
    length: int = Field(default=25, description="Number of records to return")
    search: dict = Field(
        default_factory=lambda: {"value": "", "regex": False},
        description="Global search value",
    )
    order: list[DataTableOrder] = Field(default_factory=list)
    columns: list[DataTableColumn] = Field(default_factory=list)
    
    @property
    def page(self) -> int:
        """Calculate page number (0-indexed)."""
        if self.length <= 0:
            return 0
        return self.start // self.length
    
    @property
    def search_value(self) -> str:
        """Get global search value."""
        return self.search.get("value", "")
    
    def get_order_by(self) -> list[tuple[str, str]]:
        """Get list of (column_name, direction) tuples."""
        result = []
        for order in self.order:
            if 0 <= order.column < len(self.columns):
                col = self.columns[order.column]
                if col.orderable:
                    result.append((col.data, order.dir))
        return result


class DataTableResponse(BaseModel, Generic[T]):
    """DataTables server-side response.
    
    Standard format expected by DataTables.net.
    """
    
    draw: int = Field(..., description="Echo of draw parameter")
    recordsTotal: int = Field(..., description="Total records before filtering")
    recordsFiltered: int = Field(..., description="Total records after filtering")
    data: list[T] = Field(default_factory=list, description="Data array")
    error: str | None = Field(default=None, description="Error message if any")


# ═══════════════════════════════════════════════════════════
# Standard API Responses
# ═══════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    code: str
    details: dict[str, Any] = Field(default_factory=dict)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response (non-DataTables)."""
    
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "ok"
    service: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
