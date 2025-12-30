# Coding Standards

## Python Best Practices

### Regole Fondamentali

| Area | Regola | Strumento |
|------|--------|-----------|
| Code Style | PEP 8, max 88 chars | Ruff |
| Type Hints | Obbligatori su metodi pubblici | mypy (strict) |
| Docstrings | Google style | - |
| Naming | snake_case funzioni, PascalCase classi | Ruff |
| Imports | Ordine: stdlib, third-party, local | isort |
| Logging | structlog, no print() | structlog |

---

## Esempio Codice Conforme

```python
"""User service module."""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.repository import UserRepository
from src.modules.users.schemas import UserResponse
from src.core.exceptions import NotFoundError


class UserService:
    """Service layer for user operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._repository = UserRepository(session)

    async def get_by_id(self, user_id: UUID) -> UserResponse:
        """Retrieve user by ID.
        
        Args:
            user_id: User's unique identifier.
            
        Returns:
            UserResponse with user data.
            
        Raises:
            NotFoundError: If user not found.
        """
        user = await self._repository.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return UserResponse.model_validate(user)
```

---

## Pattern Responsabilità

| Layer | File | Responsabilità |
|-------|------|----------------|
| Router | `router.py` | Endpoint, HTTP status |
| Schema | `schemas.py` | Validazione I/O |
| Service | `service.py` | Business logic |
| Repository | `repository.py` | Query database |
| Model | `models.py` | Tabelle SQLAlchemy |

---

## Flusso Request

```
HTTP → Router → Service → Repository → Database
```

---

## Configurazione Ruff

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true
```
