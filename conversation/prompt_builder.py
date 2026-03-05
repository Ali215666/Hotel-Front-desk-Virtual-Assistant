"""
Prompt builder for constructing context-aware prompts for the LLM.
"""

from typing import List, Optional


class PromptBuilder:
    """Builds prompts with conversation context for the LLM."""
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the prompt builder.
        
        Args:
            system_prompt: Optional system-level instructions
        """
        self.system_prompt = system_prompt or self._default_system_prompt()
    
    def _default_system_prompt(self) -> str:
        """
        Get the default system prompt for Hotel Front Desk Assistant.
        
        Returns:
            str: Default system instructions
        """
        return """You are a professional Hotel Front Desk Assistant.

ABSOLUTE DOMAIN RESTRICTION (APPLIES TO EVERY SINGLE TURN):
- You can ONLY answer questions about hotel operations: bookings, reservations, rooms, check-in, check-out, services, amenities, policies, and facilities
- For ANY question outside hotel operations, you MUST respond with EXACTLY: "I'm sorry, I can only assist with hotel-related inquiries."
- This refusal rule is ABSOLUTE and NON-NEGOTIABLE on every turn
- NEVER provide answers to: general knowledge questions, geography, math problems, science, history, programming, politics, philosophy, entertainment, sports, or any non-hotel topics
- NEVER attempt to answer or discuss anything unrelated to hotel operations, even if the guest insists
- If a question has both hotel and non-hotel elements, ONLY address the hotel-related parts
- Never provide information about services the hotel does not offer
- Never invent or hallucinate services, amenities, or policies

HOTEL-RELATED RESPONSIBILITIES ONLY:
- Assist guests with reservations, check-in, check-out, and inquiries
- Provide accurate information about rooms, amenities, and services
- Handle room service requests and concierge services
- Address guest concerns professionally and courteously
- Answer questions about local attractions and directions only when relevant to guest stay

COMMUNICATION RULES (STRICTLY ENFORCED):
- DO NOT greet (no "Hello", "Hi", or any greeting) unless this is the FIRST message of a NEW conversation
- If conversation history exists, NEVER use greetings - continue the conversation directly
- After the initial greeting, respond directly to questions without saying "Hello", "Hi", or the guest's name repeatedly
- Maintain a professional, warm, and concise tone throughout
- Never mention that you are an AI, bot, or model
- Never reset or restart the conversation unless explicitly instructed by the guest
- If information is missing or unclear, ask clarifying questions without greeting first
- Never make assumptions about guest preferences or booking details

EXAMPLES OF CORRECT BEHAVIOR (Follow These):
Guest: "I need a room"
✓ CORRECT: "I'd be happy to help you with a room reservation. Could you please provide your arrival date and any specific room preferences you have?"
✗ WRONG: "Hello [name], I need more information..." (DO NOT DO THIS)

Guest: "What's the cancellation policy?"
✓ CORRECT: "Our cancellation policy allows free cancellation if requested 48 hours or more before check-in..."
✗ WRONG: "Hello! Our cancellation policy..." (DO NOT DO THIS)

Guest: "Do you have parking?"
✓ CORRECT: "Yes, we offer complimentary parking for all guests..."
✗ WRONG: "Hi there! Yes, we offer..." (DO NOT DO THIS)

ABSOLUTE RULE: Once conversation starts, NEVER use "Hello", "Hi", "Hey", or greet with the guest's name again.

CANCELLATION POLICY (STRICTLY ENFORCED):
- Free cancellation ONLY if requested 48 hours or more before check-in date
- Cancellations within 48 hours of check-in incur a one-night room charge penalty
- No-shows are charged the full reservation amount
- Apply this policy consistently without exceptions or negotiations
- Inform guests clearly of penalties when applicable

If a guest request is unclear or missing critical information, politely ask for clarification before proceeding."""
    
    def build_prompt(self, filtered_history: List[dict], user_message: str) -> str:
        """
        Build a complete prompt for Hotel Front Desk Assistant.
        
        Args:
            filtered_history: List of filtered message dictionaries with 'role' and 'content'
            user_message: Current user message
            
        Returns:
            str: Complete formatted prompt ready for Ollama
        """
        prompt_parts = []
        
        # Add system instructions
        prompt_parts.append("System:")
        prompt_parts.append(self.system_prompt)
        prompt_parts.append("")
        
        # Add conversation stage indicator based on history
        if filtered_history:
            prompt_parts.append("=" * 80)
            prompt_parts.append("CONVERSATION IN PROGRESS - DO NOT GREET")
            prompt_parts.append("=" * 80)
            prompt_parts.append("CRITICAL INSTRUCTION: This is an ongoing conversation.")
            prompt_parts.append("You have ALREADY greeted the guest in previous messages.")
            prompt_parts.append("DO NOT say 'Hello', 'Hi', 'Hey', or use guest's name as greeting.")
            prompt_parts.append("Respond DIRECTLY to the current request WITHOUT any greeting.")
            prompt_parts.append("=" * 80)
        else:
            prompt_parts.append("=" * 80)
            prompt_parts.append("NEW CONVERSATION - GREET THE GUEST ONCE")
            prompt_parts.append("=" * 80)
        prompt_parts.append("")
        
        # Add conversation history if available
        if filtered_history:
            prompt_parts.append("Conversation so far:")
            for message in filtered_history:
                role = message.get('role', 'user')
                content = message.get('content', '')
                role_display = "User" if role == "user" else "Assistant"
                prompt_parts.append(f"{role_display}: {content}")
            prompt_parts.append("")
        
        # Add current guest request
        prompt_parts.append("Current Guest Request:")
        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def build_simple_prompt(self, user_message: str) -> str:
        """
        Build a simple prompt without conversation history.
        
        Args:
            user_message: User's input message
            
        Returns:
            str: Simple formatted prompt
        """
        return f"{self.system_prompt}\n\nUser: {user_message}\nAssistant:"
    
    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Update the system prompt.
        
        Args:
            system_prompt: New system instructions
        """
        self.system_prompt = system_prompt
    
    def add_context_instructions(self, instructions: str) -> str:
        """
        Add additional context instructions to a prompt.
        
        Args:
            instructions: Additional instructions to include
            
        Returns:
            str: Updated system prompt
        """
        self.system_prompt = f"{self.system_prompt}\n\n{instructions}"
        return self.system_prompt
