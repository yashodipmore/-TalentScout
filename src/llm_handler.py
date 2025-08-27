"""
LLM Handler for TalentScout Hiring Assistant

This module handles all interactions with the Groq LLM API.
"""

import os
from groq import Groq
from typing import List, Dict, Any, Optional
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMHandler:
    """Handler for Groq LLM interactions"""
    
    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        """
        Initialize the LLM handler
        
        Args:
            api_key: Groq API key
            model: Model to use (default: llama3-8b-8192)
        """
        self.client = Groq(api_key=api_key)
        self.model = model
        self.max_tokens = 1024
        self.temperature = 0.7
    
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from the LLM
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                top_p=kwargs.get('top_p', 1),
                stream=False
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again."
    
    def extract_information(self, user_input: str, prompt_template: str) -> Dict[str, Any]:
        """
        Extract structured information from user input
        
        Args:
            user_input: User's input text
            prompt_template: Template for information extraction
            
        Returns:
            Extracted information as dictionary
        """
        messages = [
            {
                "role": "system",
                "content": prompt_template
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        try:
            response = self.generate_response(messages, temperature=0.3)
            # Try to parse as JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If not JSON, return raw response
                return {"raw_response": response}
                
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return {}
    
    def generate_technical_questions(self, tech_stack: List[str], experience_level: str = "mid") -> List[Dict[str, Any]]:
        """
        Generate technical questions based on tech stack
        
        Args:
            tech_stack: List of technologies
            experience_level: Experience level of candidate
            
        Returns:
            List of technical questions
        """
        prompt = f"""
        Generate 3-5 technical interview questions for a {experience_level}-level candidate with the following tech stack: {', '.join(tech_stack)}.
        
        For each question, provide:
        - The question text
        - Technology it tests
        - Difficulty level (beginner/intermediate/advanced)
        - Key concepts it evaluates
        
        Return the response as a JSON array with this structure:
        [
            {{
                "question": "question text",
                "technology": "specific technology",
                "difficulty": "difficulty level",
                "concepts": ["concept1", "concept2"]
            }}
        ]
        
        Make questions practical and relevant to real-world scenarios.
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert technical interviewer. Generate relevant, practical technical questions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.generate_response(messages, temperature=0.5)
            questions = json.loads(response)
            return questions if isinstance(questions, list) else []
            
        except Exception as e:
            logger.error(f"Error generating technical questions: {str(e)}")
            return self._fallback_questions(tech_stack)
    
    def _fallback_questions(self, tech_stack: List[str]) -> List[Dict[str, Any]]:
        """
        Fallback questions when API fails
        
        Args:
            tech_stack: List of technologies
            
        Returns:
            List of fallback questions
        """
        fallback_questions = []
        
        for tech in tech_stack[:3]:  # Limit to 3 technologies
            fallback_questions.append({
                "question": f"Can you explain your experience with {tech} and describe a project where you used it?",
                "technology": tech,
                "difficulty": "intermediate",
                "concepts": ["experience", "practical application"]
            })
        
        return fallback_questions
    
    def classify_tech_stack(self, tech_input: str) -> List[str]:
        """
        Extract and classify technologies from user input
        
        Args:
            tech_input: User's tech stack description
            
        Returns:
            List of classified technologies
        """
        prompt = f"""
        Extract and standardize the technologies mentioned in this text: "{tech_input}"
        
        Return only a JSON array of technology names, properly formatted and standardized.
        For example: ["Python", "Django", "PostgreSQL", "React", "AWS"]
        
        Focus on:
        - Programming languages
        - Frameworks and libraries  
        - Databases
        - Cloud platforms
        - Development tools
        
        Standardize names (e.g., "js" -> "JavaScript", "postgres" -> "PostgreSQL")
        """
        
        messages = [
            {
                "role": "system", 
                "content": "You are a technical recruiter expert at identifying and standardizing technology names."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.generate_response(messages, temperature=0.3)
            tech_list = json.loads(response)
            return tech_list if isinstance(tech_list, list) else []
            
        except Exception as e:
            logger.error(f"Error classifying tech stack: {str(e)}")
            # Simple fallback: split by common separators
            return [tech.strip() for tech in tech_input.replace(',', ' ').split() if len(tech.strip()) > 1]
