"""
API routes for Hotel Front Desk conversational AI system.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import json
import logging
import re

from .websocket_manager import WebSocketManager
from .dependencies import (
    get_websocket_manager,
    get_session_manager,
    get_ollama_client,
    get_memory_manager,
    get_prompt_builder
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_greeting_from_response(response: str, has_history: bool) -> str:
    """
    Remove greeting patterns from assistant responses if conversation history exists.
    
    Args:
        response: The assistant's response text
        has_history: Whether conversation history exists
        
    Returns:
        Cleaned response text
    """
    if not has_history or not response:
        return response
    
    # Patterns to remove (case insensitive)
    greeting_patterns = [
        r'^Hello\s+\w+,?\s*',  # "Hello Name," or "Hello Name "
        r'^Hi\s+\w+,?\s*',      # "Hi Name," or "Hi Name "
        r'^Hey\s+\w+,?\s*',     # "Hey Name," or "Hey Name "
        r'^Hello,?\s*',         # "Hello," or "Hello "
        r'^Hi,?\s*',            # "Hi," or "Hi "
        r'^Hey,?\s*',           # "Hey," or "Hey "
    ]
    
    cleaned = response
    for pattern in greeting_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove leading whitespace after cleaning
    cleaned = cleaned.lstrip()
    
    return cleaned


router = APIRouter()


# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, description="User message")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    reply: str = Field(..., description="Assistant's response")


@router.post("/sessions")
async def create_session() -> Dict[str, Any]:
    """
    Create a new conversation session.
    
    Returns:
        Dict containing session_id and metadata
    """
    # TODO: Implement session creation logic
    pass


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """
    Retrieve session information.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict containing session data
    """
    # TODO: Implement session retrieval logic
    pass


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, str]:
    """
    Delete a session and its history.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict with deletion confirmation
    """
    # TODO: Implement session deletion logic
    pass


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str) -> Dict[str, Any]:
    """
    Retrieve conversation history for a session.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict containing conversation history
    """
    # TODO: Implement history retrieval logic
    pass


@router.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    session_manager=Depends(get_session_manager),
    memory_manager=Depends(get_memory_manager),
    prompt_builder=Depends(get_prompt_builder),
    ollama_client=Depends(get_ollama_client)
) -> ChatResponse:
    """
    REST endpoint for synchronous chat interaction.
    
    Accepts POST requests with JSON payload:
    {
        "session_id": "string",
        "message": "string"
    }
    
    Returns JSON response:
    {
        "reply": "string"
    }
    
    Args:
        request: ChatRequest containing session_id and message
        session_manager: Session manager dependency
        memory_manager: Memory manager dependency
        prompt_builder: Prompt builder dependency
        ollama_client: Ollama client dependency
        
    Returns:
        ChatResponse containing the assistant's reply
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for server errors
    """
    try:
        session_id = request.session_id
        user_message = request.message
        
        # Validate inputs
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Invalid session_id: must be a non-empty string"
            )
        
        if not user_message or not user_message.strip():
            raise HTTPException(
                status_code=400,
                detail="Invalid message: must be a non-empty string"
            )
        
        logger.info(f"REST API: Processing message for session {session_id}: {user_message[:50]}...")
        
        # Ensure session exists in session manager
        if not session_manager.get_session(session_id):
            session_manager.create_session()
            from datetime import datetime
            session_manager.sessions[session_id] = {
                'created_at': datetime.now(),
                'last_active': datetime.now()
            }
            logger.info(f"Created new session: {session_id}")
        
        # Ensure memory session exists
        if not memory_manager.session_exists(session_id):
            memory_manager.create_session(session_id)
            logger.info(f"Created new memory session: {session_id}")
        
        # Get conversation history
        history = memory_manager.get_history(session_id)
        active_context = memory_manager.get_active_context(history)
        
        # Build prompt with context
        prompt = prompt_builder.build_prompt(active_context, user_message)
        
        # Generate response from LLM (non-streaming)
        logger.info(f"Generating response for session {session_id}")
        response = ollama_client.generate(prompt)
        
        # Check if response is an error message
        if response.startswith("Error:"):
            logger.error(f"LLM error for session {session_id}: {response}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate response: {response}"
            )
        
        # Clean greeting from response if conversation history exists
        cleaned_response = clean_greeting_from_response(response, len(active_context) > 0)
        
        # Store conversation in memory
        memory_manager.add_message(session_id, "user", user_message)
        memory_manager.add_message(session_id, "assistant", cleaned_response)
        
        logger.info(f"REST API: Response generated for session {session_id}")
        
        return ChatResponse(reply=cleaned_response)
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except ValueError as ve:
        logger.error(f"Validation error in chat endpoint: {ve}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(ve)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    WebSocket endpoint for real-time hotel assistant conversation.
    
    Accepts JSON messages with format:
    {
        "session_id": "string",
        "message": "string"
    }
    
    Args:
        websocket: WebSocket connection
        ws_manager: WebSocket connection manager
    """
    # Import dependencies
    from .dependencies import get_session_manager, get_ollama_client, get_memory_manager, get_prompt_builder
    
    session_manager = get_session_manager()
    ollama_client = get_ollama_client()
    memory_manager = get_memory_manager()
    prompt_builder = get_prompt_builder()
    
    # Initially accept the connection without session_id
    await websocket.accept()
    logger.info("WebSocket connection accepted, awaiting session_id")
    
    current_session_id = None
    
    try:
        while True:
            # Receive message from client
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message format
                if not isinstance(message_data, dict):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid message format. Expected JSON object."
                    })
                    continue
                
                session_id = message_data.get("session_id")
                user_message = message_data.get("message")
                
                # Validate required fields
                if not session_id or not user_message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing required fields: 'session_id' and 'message'"
                    })
                    continue
                
                # Register connection with session_id if first message or session changed
                if current_session_id != session_id:
                    # Update session tracking without closing the WebSocket
                    # (same connection, different session ID)
                    async with ws_manager._lock:
                        # Remove old session ID from tracking (if exists)
                        if current_session_id in ws_manager.active_connections:
                            # Only remove from dict, don't close the connection
                            ws_manager.active_connections.pop(current_session_id)
                            logger.info(f"Removed old session tracking: {current_session_id}")
                        
                        # If new session ID already has a connection, close that old one
                        if session_id in ws_manager.active_connections:
                            old_ws = ws_manager.active_connections[session_id]
                            if old_ws != websocket:  # Only close if it's a different connection
                                try:
                                    await old_ws.close()
                                except:
                                    pass
                        
                        # Register current WebSocket with new session ID
                        ws_manager.active_connections[session_id] = websocket
                    
                    # Update current session ID
                    current_session_id = session_id
                    logger.info(f"WebSocket session updated to: {session_id}")
                
                # Ensure session exists in session manager
                if not session_manager.get_session(session_id):
                    session_manager.create_session()
                    session_manager.sessions[session_id] = {
                        'created_at': session_manager.sessions.get(session_id, {}).get('created_at'),
                        'last_active': session_manager.sessions.get(session_id, {}).get('last_active')
                    }
                
                # Ensure memory session exists
                if not memory_manager.session_exists(session_id):
                    memory_manager.create_session(session_id)
                
                # Handle init/handshake messages - just acknowledge, don't process
                if user_message == "__INIT__" or message_data.get("type") == "init":
                    logger.info(f"Received init handshake for session {session_id}")
                    await websocket.send_json({
                        "type": "status",
                        "message": "Session registered"
                    })
                    continue
                
                logger.info(f"Processing message for session {session_id}: {user_message[:50]}...")
                
                # Send acknowledgment
                await websocket.send_json({
                    "type": "status",
                    "message": "Processing your request..."
                })
                
                # Get conversation history
                history = memory_manager.get_history(session_id)
                active_context = memory_manager.get_active_context(history)
                
                # Build prompt
                prompt = prompt_builder.build_prompt(active_context, user_message)
                
                # Store user message
                memory_manager.add_message(session_id, "user", user_message)
                
                # Stream response from Ollama
                full_response = ""
                
                try:
                    async for token in ollama_client.generate_stream(prompt):
                        if token:
                            full_response += token
                            # Send each token to client
                            await websocket.send_text(token)
                    
                    # Send completion signal
                    await websocket.send_json({
                        "type": "done",
                        "message": "Response complete"
                    })
                    
                    # Clean greeting from response if conversation history exists
                    cleaned_response = clean_greeting_from_response(full_response, len(active_context) > 0)
                    
                    # Store cleaned assistant response
                    memory_manager.add_message(session_id, "assistant", cleaned_response)
                    logger.info(f"Response completed for session {session_id}")
                
                except Exception as stream_error:
                    logger.error(f"Error during streaming: {stream_error}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error generating response: {str(stream_error)}"
                    })
            
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON decode error: {json_error}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue
            
            except Exception as msg_error:
                logger.error(f"Error processing message: {msg_error}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(msg_error)}"
                })
                continue
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {current_session_id}")
        if current_session_id:
            await ws_manager.disconnect(current_session_id)
    
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket endpoint: {e}")
        if current_session_id:
            await ws_manager.disconnect(current_session_id)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Unexpected error: {str(e)}"
            })
        except:
            pass

