"""
WebSocket connection manager for handling concurrent client connections.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for multiple concurrent sessions."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection to register
        """
        try:
            await websocket.accept()
            async with self._lock:
                # If session already exists, close the old connection first
                if session_id in self.active_connections:
                    old_websocket = self.active_connections[session_id]
                    try:
                        await old_websocket.close()
                    except Exception as e:
                        logger.warning(f"Error closing old connection for session {session_id}: {e}")
                
                self.active_connections[session_id] = websocket
            
            logger.info(f"WebSocket connected: session_id={session_id}")
            logger.info(f"Active connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error connecting WebSocket for session {session_id}: {e}")
            raise
    
    async def disconnect(self, session_id: str) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            session_id: Session identifier to disconnect
        """
        try:
            async with self._lock:
                if session_id in self.active_connections:
                    websocket = self.active_connections.pop(session_id)
                    try:
                        await websocket.close()
                    except Exception as e:
                        logger.warning(f"Error closing WebSocket for session {session_id}: {e}")
                    
                    logger.info(f"WebSocket disconnected: session_id={session_id}")
                    logger.info(f"Active connections: {len(self.active_connections)}")
                else:
                    logger.warning(f"Attempted to disconnect non-existent session: {session_id}")
        except Exception as e:
            logger.error(f"Error disconnecting session {session_id}: {e}")
    
    async def send_message(self, session_id: str, message: dict) -> None:
        """
        Send a message to a specific session.
        
        Args:
            session_id: Target session identifier
            message: Message dictionary to send
        """
        websocket = None
        async with self._lock:
            websocket = self.active_connections.get(session_id)
        
        if websocket is None:
            logger.warning(f"Cannot send message - session not connected: {session_id}")
            return
        
        try:
            # Send message as JSON
            if isinstance(message, dict):
                await websocket.send_json(message)
            elif isinstance(message, str):
                await websocket.send_text(message)
            else:
                await websocket.send_text(str(message))
            
            logger.debug(f"Message sent to session {session_id}")
        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected while sending to session {session_id}")
            await self.disconnect(session_id)
        except Exception as e:
            logger.error(f"Error sending message to session {session_id}: {e}")
            await self.disconnect(session_id)
    
    async def broadcast(self, message: dict) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message dictionary to broadcast
        """
        # Get a snapshot of active connections
        connections_snapshot = {}
        async with self._lock:
            connections_snapshot = self.active_connections.copy()
        
        if not connections_snapshot:
            logger.info("No active connections to broadcast to")
            return
        
        logger.info(f"Broadcasting message to {len(connections_snapshot)} connections")
        
        # Send to all connections concurrently
        disconnected_sessions = []
        
        async def send_to_client(session_id: str, websocket: WebSocket):
            try:
                if isinstance(message, dict):
                    await websocket.send_json(message)
                elif isinstance(message, str):
                    await websocket.send_text(message)
                else:
                    await websocket.send_text(str(message))
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected during broadcast: {session_id}")
                disconnected_sessions.append(session_id)
            except Exception as e:
                logger.error(f"Error broadcasting to session {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Send all messages concurrently
        await asyncio.gather(
            *[send_to_client(sid, ws) for sid, ws in connections_snapshot.items()],
            return_exceptions=True
        )
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            await self.disconnect(session_id)
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs.
        
        Returns:
            List of active session identifiers
        """
        return list(self.active_connections.keys())
    
    def is_connected(self, session_id: str) -> bool:
        """
        Check if a session is currently connected.
        
        Args:
            session_id: Session identifier to check
            
        Returns:
            True if connected, False otherwise
        """
        return session_id in self.active_connections
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send a message directly to a specific WebSocket connection.
        This is an alias method for compatibility.
        
        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            if isinstance(message, dict):
                await websocket.send_json(message)
            elif isinstance(message, str):
                await websocket.send_text(message)
            else:
                await websocket.send_text(str(message))
            
            logger.debug("Personal message sent")
        except WebSocketDisconnect:
            logger.warning("WebSocket disconnected while sending personal message")
            raise
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            raise
    
    def get_connection_count(self) -> int:
        """
        Get the number of active connections.
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections)
