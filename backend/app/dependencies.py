"""
Dependency injection for FastAPI routes.
"""

from functools import lru_cache
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.websocket_manager import WebSocketManager
from llm.ollama_client import OllamaClient
from conversation.memory_manager import MemoryManager
from conversation.prompt_builder import PromptBuilder
from conversation.session_manager import SessionManager


# Singleton instances
_websocket_manager = None
_ollama_client = None
_memory_manager = None
_prompt_builder = None
_session_manager = None


@lru_cache()
def get_websocket_manager() -> WebSocketManager:
    """
    Get or create WebSocket manager singleton.
    
    Returns:
        WebSocketManager instance
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def get_ollama_client():
    """
    Get or create Ollama client instance.
    
    Returns:
        OllamaClient instance
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


def get_memory_manager():
    """
    Get or create memory manager instance.
    
    Returns:
        MemoryManager instance
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def get_prompt_builder():
    """
    Get or create prompt builder instance.
    
    Returns:
        PromptBuilder instance
    """
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


def get_session_manager():
    """
    Get or create session manager instance.
    
    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        ollama_client = get_ollama_client()
        memory_manager = get_memory_manager()
        prompt_builder = get_prompt_builder()
        _session_manager = SessionManager(ollama_client, memory_manager, prompt_builder)
    return _session_manager
