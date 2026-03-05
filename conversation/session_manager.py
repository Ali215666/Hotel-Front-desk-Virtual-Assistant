"""
Session manager for handling multiple conversation sessions.
"""

import uuid
from typing import Dict, Optional
from datetime import datetime


class SessionManager:
    """Manages conversation sessions and coordinates message processing."""
    
    def __init__(self, ollama_client, memory_manager, prompt_builder):
        """
        Initialize the session manager.
        
        Args:
            ollama_client: Client for interacting with Ollama LLM
            memory_manager: Manager for conversation memory
            prompt_builder: Builder for constructing prompts
        """
        self.ollama_client = ollama_client
        self.memory_manager = memory_manager
        self.prompt_builder = prompt_builder
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            str: Unique session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_active': datetime.now()
        }
        return session_id
    
    def process_message(self, session_id: str, user_message: str) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            session_id: Session identifier
            user_message: User's input message
            
        Returns:
            str: AI-generated response
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Update session activity
        self.sessions[session_id]['last_active'] = datetime.now()
        
        # Ensure memory session exists
        if not self.memory_manager.session_exists(session_id):
            self.memory_manager.create_session(session_id)
        
        # Retrieve conversation history
        history = self.memory_manager.get_history(session_id)
        
        # Get active context (filtered to last 6 turns)
        active_context = self.memory_manager.get_active_context(history)
        
        # Build prompt with context
        prompt = self.prompt_builder.build_prompt(user_message, active_context)
        
        # Generate response from LLM
        response = self.ollama_client.generate(prompt)
        
        # Store conversation in memory
        self.memory_manager.add_message(session_id, "user", user_message)
        self.memory_manager.add_message(session_id, "assistant", response)
        
        return response
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[dict]: Session data or None if not found
        """
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its associated memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session was deleted, False otherwise
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.memory_manager.delete_session(session_id)
            return True
        return False
