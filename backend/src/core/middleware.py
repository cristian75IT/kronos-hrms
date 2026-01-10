from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from src.core.context import set_request_context

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract relevant info
        context = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "path": request.url.path
        }
        
        # Set context
        set_request_context(context)
        
        # Process request
        print(f"DEBUG_MIDDLEWARE: Incoming request: {request.method} {request.url}", flush=True)
        response = await call_next(request)
        print(f"DEBUG_MIDDLEWARE: Response status: {response.status_code} for {request.url}", flush=True)
        
        return response
