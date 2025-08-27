"""
Conversation Manager for TalentScout Hiring Assistant

This module manages the conversation flow and state transitions.
"""

from typing import List, Dict, Any, Optional
import re
import logging
from src.llm_handler import LLMHandler
from src.data_models import CandidateInfo, ConversationState, TechnicalQuestion
from src.prompts import PromptTemplates
from src.utils import validate_email, validate_phone, extract_experience_years

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation flow and state"""
    
    def __init__(self, llm_handler: LLMHandler):
        """
        Initialize conversation manager
        
        Args:
            llm_handler: LLM handler instance
        """
        self.llm = llm_handler
        self.prompts = PromptTemplates()
        
        # Required information fields
        self.required_fields = [
            "name", "email", "phone", "experience_years", 
            "desired_position", "location", "tech_stack"
        ]
        
    def get_welcome_message(self) -> str:
        """Get welcome message"""
        return self.prompts.get_welcome_prompt()
    
    def get_farewell_message(self, candidate_name: str = None) -> str:
        """Get farewell message"""
        name = candidate_name or "candidate"
        return self.prompts.get_farewell_prompt(name)
    
    def process_user_input(self, user_input: str, conversation_state: ConversationState) -> str:
        """
        Process user input and generate appropriate response
        
        Args:
            user_input: User's input text
            conversation_state: Current conversation state
            
        Returns:
            Assistant's response
        """
        try:
            # Check current step and process accordingly
            if conversation_state.current_step == "greeting":
                return self._handle_greeting(user_input, conversation_state)
            
            elif conversation_state.current_step == "info_gathering":
                return self._handle_info_gathering(user_input, conversation_state)
            
            elif conversation_state.current_step == "tech_questions":
                return self._handle_tech_questions(user_input, conversation_state)
            
            elif conversation_state.current_step == "conclusion":
                return self._handle_conclusion(user_input, conversation_state)
            
            else:
                # Default fallback
                return self._handle_info_gathering(user_input, conversation_state)
                
        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}")
            return self.prompts.get_error_handling_prompt()
    
    def _handle_greeting(self, user_input: str, conversation_state: ConversationState) -> str:
        """Handle greeting phase"""
        # Extract information from the first message
        extracted_info = self._extract_information(user_input)
        self._update_candidate_info(extracted_info, conversation_state)
        
        # Move to information gathering
        conversation_state.current_step = "info_gathering"
        
        return self._continue_info_gathering(conversation_state)
    
    def _handle_info_gathering(self, user_input: str, conversation_state: ConversationState) -> str:
        """Handle information gathering phase"""
        # Extract information from user input
        extracted_info = self._extract_information(user_input)
        self._update_candidate_info(extracted_info, conversation_state)
        
        # Check if we have all required information
        missing_info = self._get_missing_information(conversation_state.candidate_info)
        conversation_state.missing_info = missing_info
        
        if not missing_info:
            # All information collected, move to technical questions
            conversation_state.information_complete = True
            conversation_state.current_step = "tech_questions"
            return self._start_technical_questions(conversation_state)
        
        return self._continue_info_gathering(conversation_state)
    
    def _handle_tech_questions(self, user_input: str, conversation_state: ConversationState) -> str:
        """Handle technical questions phase"""
        
        if not conversation_state.questions_generated:
            # Generate technical questions
            tech_stack = conversation_state.candidate_info.tech_stack
            experience_years = conversation_state.candidate_info.experience_years
            
            if tech_stack:
                questions = self._generate_technical_questions(tech_stack, experience_years)
                conversation_state.technical_questions = questions
                conversation_state.questions_generated = True
                
                if questions:
                    # Ask first question
                    first_question = questions[0]
                    return f"{self.prompts.get_technical_question_prompt(tech_stack, experience_years)}\n\n**Question 1 ({first_question.technology}):**\n{first_question.question}"
                else:
                    return "I'm having trouble generating questions right now. Could you tell me more about a recent project you worked on and the technologies you used?"
            else:
                return "I'd like to ask some technical questions, but I need to know more about your tech stack first. Could you tell me about the technologies you work with?"
        
        else:
            # Handle answer to technical question
            return self._handle_technical_answer(user_input, conversation_state)
    
    def _handle_technical_answer(self, user_input: str, conversation_state: ConversationState) -> str:
        """Handle answers to technical questions"""
        
        questions = conversation_state.technical_questions
        
        if len(questions) > 1:
            # Ask next question
            next_question = questions[1]
            conversation_state.technical_questions = questions[1:]  # Remove asked question
            return f"Thank you for that answer! \n\n**Next Question ({next_question.technology}):**\n{next_question.question}"
        
        else:
            # No more questions, conclude interview
            conversation_state.current_step = "conclusion"
            conversation_state.interview_complete = True
            return self._conclude_interview(conversation_state)
    
    def _handle_conclusion(self, user_input: str, conversation_state: ConversationState) -> str:
        """Handle conclusion phase"""
        return self.get_farewell_message(conversation_state.candidate_info.name)
    
    def _extract_information(self, user_input: str) -> Dict[str, Any]:
        """Extract information from user input"""
        try:
            prompt = self.prompts.get_information_extraction_prompt()
            extracted = self.llm.extract_information(user_input, prompt)
            
            # Validate and clean extracted information
            cleaned_info = {}
            
            if "name" in extracted and extracted["name"]:
                cleaned_info["name"] = str(extracted["name"]).strip()
            
            if "email" in extracted and extracted["email"]:
                email = str(extracted["email"]).strip()
                if validate_email(email):
                    cleaned_info["email"] = email
            
            if "phone" in extracted and extracted["phone"]:
                phone = str(extracted["phone"]).strip()
                if validate_phone(phone):
                    cleaned_info["phone"] = phone
            
            if "experience_years" in extracted:
                exp_years = extract_experience_years(str(extracted["experience_years"]))
                if exp_years is not None:
                    cleaned_info["experience_years"] = exp_years
            
            if "desired_position" in extracted and extracted["desired_position"]:
                cleaned_info["desired_position"] = str(extracted["desired_position"]).strip()
            
            if "location" in extracted and extracted["location"]:
                cleaned_info["location"] = str(extracted["location"]).strip()
            
            if "tech_stack" in extracted and isinstance(extracted["tech_stack"], list):
                tech_stack = [tech.strip() for tech in extracted["tech_stack"] if tech.strip()]
                if tech_stack:
                    cleaned_info["tech_stack"] = tech_stack
            
            return cleaned_info
            
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return {}
    
    def _update_candidate_info(self, extracted_info: Dict[str, Any], conversation_state: ConversationState):
        """Update candidate information with extracted data"""
        
        candidate_info = conversation_state.candidate_info
        
        for field, value in extracted_info.items():
            if field == "tech_stack":
                # Merge tech stack lists
                existing_tech = set(candidate_info.tech_stack)
                new_tech = set(value)
                candidate_info.tech_stack = list(existing_tech.union(new_tech))
            else:
                # Update other fields if not already set or if new value is provided
                current_value = getattr(candidate_info, field, None)
                if not current_value or value:
                    setattr(candidate_info, field, value)
    
    def _get_missing_information(self, candidate_info: CandidateInfo) -> List[str]:
        """Get list of missing required information"""
        
        missing = []
        
        if not candidate_info.name:
            missing.append("name")
        if not candidate_info.email:
            missing.append("email")
        if not candidate_info.phone:
            missing.append("phone")
        if candidate_info.experience_years is None:
            missing.append("experience_years")
        if not candidate_info.desired_position:
            missing.append("desired_position")
        if not candidate_info.location:
            missing.append("location")
        if not candidate_info.tech_stack:
            missing.append("tech_stack")
        
        return missing
    
    def _continue_info_gathering(self, conversation_state: ConversationState) -> str:
        """Continue gathering missing information"""
        
        missing_info = conversation_state.missing_info
        candidate_info = conversation_state.candidate_info
        
        if not missing_info:
            return "Perfect! I have all the information I need."
        
        # Provide specific prompts for missing information
        next_field = missing_info[0]
        
        if next_field == "name":
            return "Great! Could you please tell me your full name?"
        
        elif next_field == "email":
            return "Thank you! What's your email address?"
        
        elif next_field == "phone":
            return "And your phone number?"
        
        elif next_field == "experience_years":
            return "How many years of professional experience do you have?"
        
        elif next_field == "desired_position":
            return "What position or role are you interested in?"
        
        elif next_field == "location":
            return "What's your current location or preferred work location?"
        
        elif next_field == "tech_stack":
            existing_tech = candidate_info.tech_stack
            if existing_tech:
                return self.prompts.get_tech_stack_clarification_prompt(existing_tech)
            else:
                return self.prompts.get_tech_stack_clarification_prompt([])
        
        return self.prompts.get_conversation_prompt(candidate_info.dict(), missing_info)
    
    def _start_technical_questions(self, conversation_state: ConversationState) -> str:
        """Start the technical questions phase"""
        
        tech_stack = conversation_state.candidate_info.tech_stack
        
        if not tech_stack:
            return "I'd like to ask some technical questions, but I need to know more about your technical skills first. Could you tell me about the technologies you work with?"
        
        return f"Excellent! I have all your basic information. Now I'd like to ask you some technical questions based on your expertise in {', '.join(tech_stack[:3])}{'...' if len(tech_stack) > 3 else ''}.\n\nThese questions will help assess your technical knowledge and problem-solving approach. Ready to proceed?"
    
    def _generate_technical_questions(self, tech_stack: List[str], experience_years: Optional[int]) -> List[TechnicalQuestion]:
        """Generate technical questions based on tech stack"""
        
        try:
            # Determine experience level
            experience_level = "mid"
            if experience_years:
                if experience_years < 2:
                    experience_level = "junior"
                elif experience_years >= 5:
                    experience_level = "senior"
            
            # Generate questions using LLM
            questions_data = self.llm.generate_technical_questions(tech_stack, experience_level)
            
            # Convert to TechnicalQuestion objects
            questions = []
            for q_data in questions_data[:3]:  # Limit to 3 questions
                try:
                    question = TechnicalQuestion(
                        technology=q_data.get("technology", tech_stack[0]),
                        question=q_data.get("question", ""),
                        difficulty_level=q_data.get("difficulty", "intermediate"),
                        category="other",  # We'll improve this later
                        expected_concepts=q_data.get("concepts", [])
                    )
                    questions.append(question)
                except Exception as e:
                    logger.error(f"Error creating question object: {str(e)}")
                    continue
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating technical questions: {str(e)}")
            return []
    
    def _conclude_interview(self, conversation_state: ConversationState) -> str:
        """Conclude the interview"""
        
        candidate_name = conversation_state.candidate_info.name or "candidate"
        
        return f"""
        Thank you for answering those technical questions! You've provided great insights into your technical knowledge and problem-solving approach.

        {self.get_farewell_message(candidate_name)}
        
        Your interview is now complete. You can review your information in the sidebar or export the interview data if needed.
        """
