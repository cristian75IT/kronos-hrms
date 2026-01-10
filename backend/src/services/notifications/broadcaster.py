
import asyncio
import logging
from uuid import UUID
from typing import Dict, AsyncGenerator

logger = logging.getLogger(__name__)

class NotificationBroadcaster:
    """
    Singleton broadcaster for Server-Sent Events (SSE).
    Manages active connections and broadcasts notifications to connected users.
    """
    _instance = None
    
    def __init__(self):
        # Map: user_id -> set(asyncio.Queue)
        # A user can have multiple open tabs/connections
        self.connections: Dict[UUID, set[asyncio.Queue]] = {}
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self, user_id: UUID) -> AsyncGenerator[str, None]:
        """
        Establish a new SSE connection for a user.
        Returns a generator yielding formatted SSE strings.
        """
        queue = asyncio.Queue()
        
        if user_id not in self.connections:
            self.connections[user_id] = set()
        self.connections[user_id].add(queue)
        
        logger.debug(f"User {user_id} connected to notification stream. Active connections: {len(self.connections.get(user_id, []))}")

        try:
            # Yield initial connection message
            yield "event: connected\ndata: {\"message\": \"Connected to notification stream\"}\n\n"
            
            while True:
                message = await queue.get()
                # Message is expected to be a ready-to-send string or data dict
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            logger.debug(f"User {user_id} disconnected from notification stream.")
        finally:
            self.disconnect(user_id, queue)

    def disconnect(self, user_id: UUID, queue: asyncio.Queue):
        """Remove a connection."""
        if user_id in self.connections:
            self.connections[user_id].discard(queue)
            if not self.connections[user_id]:
                del self.connections[user_id]

    async def broadcast(self, user_id: UUID, message: str):
        """
        Send a message to all active connections of a user.
        message: JSON string payload.
        """
        if user_id in self.connections:
            for queue in self.connections[user_id]:
                await queue.put(message)
            logger.debug(f"Broadcasted to {user_id}: {message}")
