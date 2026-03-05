"""
Main entry point for local testing of the conversational AI system.
"""

from conversation.memory_manager import MemoryManager
from conversation.prompt_builder import PromptBuilder
from llm.ollama_client import OllamaClient


def main():
    """Initialize and test the conversational AI system."""
    # Initialize core components
    ollama_client = OllamaClient(model_name="hotel-qwen")
    memory_manager = MemoryManager()
    prompt_builder = PromptBuilder()
    
    print("=== Hotel Front Desk Assistant - CLI Testing ===")
    print("Commands: 'exit' to quit, 'reset' to clear conversation\n")
    
    # Session tracking
    session_id = None
    
    # Interactive conversation loop
    while True:
        # Step 1: Ask user for input
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Handle reset command
        if user_input.lower() == 'reset':
            if session_id:
                memory_manager.reset_session(session_id)
                print("[Conversation history cleared]\n")
            else:
                print("[No active session to reset]\n")
            continue
        
        # Step 2: Create session if not exists
        if session_id is None:
            session_id = "test-session-001"  # Use fixed ID for testing
            memory_manager.create_session(session_id)
            print(f"[Session created: {session_id}]\n")
        
        # Step 3: Add user message to memory
        memory_manager.add_message(session_id, "user", user_input)
        
        # Step 4: Use memory manager to filter history
        full_history = memory_manager.get_history(session_id)
        filtered_history = memory_manager.get_active_context(full_history)
        
        # Step 5: Build structured prompt using prompt builder
        # Exclude current message from history since it's added separately in the prompt
        context_history = filtered_history[:-1] if filtered_history else []
        prompt = prompt_builder.build_prompt(context_history, user_input)
        
        # Step 6: Send prompt to Ollama client
        response = ollama_client.generate(prompt)
        
        # Step 7: Print assistant response
        print(f"Assistant: {response}\n")
        
        # Step 8: Save assistant response in session
        memory_manager.add_message(session_id, "assistant", response)


if __name__ == "__main__":
    main()
