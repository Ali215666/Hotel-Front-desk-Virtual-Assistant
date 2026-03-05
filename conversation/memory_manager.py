"""
Thread-safe in-memory session manager for storing conversation history.
"""

import threading
from typing import Dict, List, Literal


class MemoryManager:
    """Thread-safe in-memory session manager for conversation history."""
    
    def __init__(self):
        """Initialize the memory manager with thread-safe storage."""
        self._sessions: Dict[str, List[dict]] = {}
        self._lock = threading.Lock()
    
    def create_session(self, session_id: str) -> None:
        """
        Create a new session with empty history.
        
        Args:
            session_id: Unique session identifier
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = []
    
    def add_message(self, session_id: str, role: Literal["user", "assistant"], content: str) -> None:
        """
        Add a message to the session history.
        
        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = []
            
            message = {
                "role": role,
                "content": content
            }
            self._sessions[session_id].append(message)
    
    def get_history(self, session_id: str) -> List[dict]:
        """
        Retrieve full conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List[dict]: List of message dictionaries with 'role' and 'content'
        """
        with self._lock:
            # Return a copy to prevent external modification
            return list(self._sessions.get(session_id, []))
    
    def get_active_context(self, history: List[dict]) -> List[dict]:
        """
        Filter conversation history to keep only last 6 dialogue turns.
        
        Args:
            history: Full conversation history
            
        Returns:
            List[dict]: Filtered history with last 6 turns (12 messages max)
        """
        if not history:
            return []
        
        # Keep last 6 turns = 12 messages
        max_messages = 12
        
        # If history shorter than 6 turns, return full history
        if len(history) <= max_messages:
            return history
        
        # Return last 12 messages
        return history[-max_messages:]
    
    def reset_session(self, session_id: str) -> None:
        """
        Clear all messages from a session.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id] = []
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session exists
        """
        with self._lock:
            return session_id in self._sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session entirely.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def get_message_count(self, session_id: str) -> int:
        """
        Get the number of messages in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            int: Number of messages in the session
        """
        with self._lock:
            return len(self._sessions.get(session_id, []))
    
    # Legacy compatibility methods
    def add_interaction(self, session_id: str, user_message: str, ai_response: str) -> None:
        """
        Legacy method: Add a user-assistant interaction pair.
        
        Args:
            session_id: Session identifier
            user_message: User's input message
            ai_response: AI's generated response
        """
        self.add_message(session_id, "user", user_message)
        self.add_message(session_id, "assistant", ai_response)
    
    def clear_history(self, session_id: str) -> None:
        """
        Legacy method: Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        self.reset_session(session_id)
