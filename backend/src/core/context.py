from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variable to hold request information
request_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar("request_context", default=None)

def get_request_context() -> Optional[Dict[str, Any]]:
    return request_context.get()

def set_request_context(context: Dict[str, Any]) -> None:
    request_context.set(context)
