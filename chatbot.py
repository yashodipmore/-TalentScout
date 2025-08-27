"""
Core chatbot logic for TalentScout Hiring Assistant
"""
import uuid
from typing import Dict, Any, List, Tuple
from models import CandidateInfo, ConversationSession, SessionManager, TechnicalQuestion
from llm_manager import LLMManager
from config import ConversationState, ENDING_KEYWORDS, REQUIRED_INFO

class HiringAssistantBot:
    """Main chatbot class handling conversation flow and logic"""
    
    def __init__(self):
        """Initialize the hiring assistant bot"""
        self.llm_manager = LLMManager()
        self.session_manager = SessionManager()
        
    def start_conversation(self, session_id: str = None) -> Tuple[str, str]:
        """Start a new conversation"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create new session
        session = self.session_manager.create_session(session_id)
        session.state = ConversationState.GREETING
        
        # Generate greeting message
        greeting = self.llm_manager.generate_greeting()
        session.add_message("assistant", greeting)
        
        # Update session state to collect info after greeting
        session.state = ConversationState.COLLECTING_INFO
        self.session_manager.update_session(session_id, session)
        
        return greeting, session_id
    
    def process_message(self, session_id: str, user_input: str) -> str:
        """Process user message and return bot response"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return "Sorry, your session has expired. Please start a new conversation."
        
        # Add user message to history
        session.add_message("user", user_input)
        
        # Check for conversation ending keywords
        if any(keyword in user_input.lower() for keyword in ENDING_KEYWORDS):
            response = self._handle_ending(session)
            session.add_message("assistant", response)
            self.session_manager.update_session(session_id, session)
            return response
        
        # Process based on current state
        if session.state == ConversationState.COLLECTING_INFO:
            response = self._handle_info_collection(session, user_input)
        elif session.state == ConversationState.COLLECTING_TECH_STACK:
            response = self._handle_tech_stack_collection(session, user_input)
        elif session.state == ConversationState.GENERATING_QUESTIONS:
            response = self._handle_question_generation(session)
        elif session.state == ConversationState.ASKING_QUESTIONS:
            response = self._handle_question_answering(session, user_input)
        else:
            response = self.llm_manager.generate_response(user_input, "General conversation")
        
        # Add bot response to history
        session.add_message("assistant", response)
        self.session_manager.update_session(session_id, session)
        
        return response
    
    def _handle_info_collection(self, session: ConversationSession, user_input: str) -> str:
        """Handle information collection phase"""
        # Extract information from user input
        missing_fields = session.candidate.missing_fields()
        extracted_info = self.llm_manager.extract_information(user_input, missing_fields)
        
        # Update candidate information
        if extracted_info:
            session.candidate.update_from_dict(extracted_info)
        
        # Check if we have all required info
        missing_fields = session.candidate.missing_fields()
        
        if not missing_fields:
            # All info collected, move to tech stack if not already collected
            if not session.candidate.tech_stack or len(session.candidate.tech_stack) == 0:
                session.state = ConversationState.COLLECTING_TECH_STACK
                return "Great! I have all your basic information. Now, could you please tell me about your technical skills and tech stack? Please mention the programming languages, frameworks, databases, and tools you're proficient in."
            else:
                # All info including tech stack collected
                session.state = ConversationState.GENERATING_QUESTIONS
                return self._handle_question_generation(session)
        else:
            # Still missing some info, ask for it
            return self.llm_manager.generate_info_prompt(missing_fields)
    
    def _handle_tech_stack_collection(self, session: ConversationSession, user_input: str) -> str:
        """Handle tech stack collection"""
        # Validate and clean tech stack
        tech_stack = self.llm_manager.validate_tech_stack(user_input)
        
        if tech_stack:
            session.candidate.tech_stack = tech_stack
            session.state = ConversationState.GENERATING_QUESTIONS
            
            # Show collected tech stack for confirmation
            tech_list = ", ".join(tech_stack)
            return f"Perfect! I've noted your tech stack: {tech_list}. Now I'll generate some technical questions to assess your skills. Please give me a moment..."
        else:
            return "I couldn't identify any specific technologies from your response. Could you please list your technical skills more clearly? For example: Python, React, MySQL, AWS, etc."
    
    def _handle_question_generation(self, session: ConversationSession) -> str:
        """Generate and start asking technical questions"""
        if not session.technical_questions:
            # Generate questions based on tech stack and experience
            questions = self.llm_manager.generate_technical_questions(
                session.candidate.tech_stack, 
                session.candidate.experience_years or "3"
            )
            
            # Convert to TechnicalQuestion objects
            session.technical_questions = [
                TechnicalQuestion(question=q, technology="mixed") 
                for q in questions
            ]
        
        if session.technical_questions:
            session.state = ConversationState.ASKING_QUESTIONS
            session.current_question_index = 0
            
            first_question = session.technical_questions[0].question
            total_questions = len(session.technical_questions)
            
            return f"Great! I've prepared {total_questions} technical questions for you. Let's begin:\n\n**Question 1 of {total_questions}:**\n{first_question}"
        else:
            return "I'm having trouble generating questions right now. Let me know if you'd like to try again or if you have any questions for me."
    
    def _handle_question_answering(self, session: ConversationSession, user_input: str) -> str:
        """Handle technical question answering phase"""
        current_index = session.current_question_index
        total_questions = len(session.technical_questions)
        
        # Store the answer (in a real system, you'd save this)
        # For now, we'll just acknowledge and move to next question
        
        session.current_question_index += 1
        
        if session.current_question_index < total_questions:
            # Ask next question
            next_question = session.technical_questions[session.current_question_index].question
            question_num = session.current_question_index + 1
            
            return f"Thank you for your answer. Here's the next question:\n\n**Question {question_num} of {total_questions}:**\n{next_question}"
        else:
            # All questions completed
            session.state = ConversationState.ENDING
            return self._handle_ending(session)
    
    def _handle_ending(self, session: ConversationSession) -> str:
        """Handle conversation ending"""
        session.state = ConversationState.ENDING
        candidate_name = session.candidate.full_name or "candidate"
        return self.llm_manager.generate_ending_message(candidate_name)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "candidate_info": session.candidate.to_dict(),
            "current_state": session.state,
            "questions_completed": session.current_question_index,
            "total_questions": len(session.technical_questions),
            "conversation_length": len(session.messages),
            "is_complete": session.candidate.is_complete(),
            "missing_fields": session.candidate.missing_fields()
        }
    
    def export_session_data(self, session_id: str) -> Dict[str, Any]:
        """Export complete session data for analysis"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return session.to_dict()
    
    def reset_session(self, session_id: str) -> str:
        """Reset conversation session"""
        self.session_manager.delete_session(session_id)
        greeting, new_session_id = self.start_conversation()
        return greeting
