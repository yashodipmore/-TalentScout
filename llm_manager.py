"""
LLM Integration using Groq API for TalentScout Hiring Assistant
"""
import json
import re
from typing import List, Dict, Any
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

class LLMManager:
    """Manages all LLM interactions for the hiring assistant"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL
        
    def _make_api_call(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """Make API call to Groq"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=1,
                stream=False
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Sorry, I'm experiencing technical difficulties. Please try again. Error: {str(e)}"
    
    def generate_greeting(self) -> str:
        """Generate personalized greeting message"""
        messages = [
            {
                "role": "system", 
                "content": """You are a friendly and professional hiring assistant for TalentScout, a technology recruitment agency. 
                Generate a warm, welcoming greeting that:
                1. Introduces yourself as TalentScout's hiring assistant
                2. Explains your purpose (initial candidate screening)
                3. Mentions you'll gather basic info and ask technical questions
                4. Keeps it concise and professional
                5. Ends by asking for their name to start"""
            },
            {
                "role": "user", 
                "content": "Generate a greeting message for a new candidate."
            }
        ]
        return self._make_api_call(messages, max_tokens=300)
    
    def extract_information(self, user_input: str, missing_fields: List[str]) -> Dict[str, Any]:
        """Extract candidate information from user input"""
        fields_prompt = ", ".join(missing_fields)
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an information extraction assistant. Extract the following information from the user's response:
                Missing fields: {fields_prompt}
                
                Rules:
                1. Extract only the information that's clearly provided
                2. For experience_years, extract only numbers (e.g., "5" from "5 years")
                3. For tech_stack, extract programming languages, frameworks, databases, tools mentioned
                4. Return ONLY a valid JSON object with extracted fields
                5. If information is not provided, don't include that field
                6. Use exact field names: full_name, email, phone, experience_years, desired_position, location, tech_stack
                
                Example output:
                {{"full_name": "John Doe", "experience_years": "3", "tech_stack": ["Python", "Django", "PostgreSQL"]}}"""
            },
            {
                "role": "user",
                "content": f"User input: {user_input}"
            }
        ]
        
        response = self._make_api_call(messages, max_tokens=500)
        
        try:
            # Clean the response to extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
        except json.JSONDecodeError:
            return {}
    
    def generate_info_prompt(self, missing_fields: List[str]) -> str:
        """Generate a prompt to ask for missing information"""
        messages = [
            {
                "role": "system",
                "content": """You are a professional hiring assistant. Generate a friendly prompt asking for missing candidate information.
                
                Rules:
                1. Be conversational and friendly
                2. Ask for multiple fields in a natural way
                3. Provide examples when helpful
                4. Keep it concise
                5. Don't sound robotic or list-like"""
            },
            {
                "role": "user",
                "content": f"I need to collect these missing fields from the candidate: {', '.join(missing_fields)}. Generate a natural prompt asking for this information."
            }
        ]
        return self._make_api_call(messages, max_tokens=300)
    
    def generate_technical_questions(self, tech_stack: List[str], experience_years: str) -> List[str]:
        """Generate technical questions based on tech stack and experience"""
        tech_list = ", ".join(tech_stack)
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a technical interviewer. Generate 3-5 relevant technical questions for a candidate with {experience_years} years of experience in: {tech_list}
                
                Rules:
                1. Questions should match the experience level ({experience_years} years)
                2. Cover different technologies mentioned
                3. Mix of conceptual and practical questions
                4. Appropriate difficulty level
                5. Return as a numbered list
                6. Each question should be clear and specific
                7. Avoid yes/no questions
                
                For junior (1-2 years): Basic concepts, syntax, simple implementations
                For mid-level (3-5 years): Best practices, design patterns, problem-solving
                For senior (6+ years): Architecture, optimization, leadership scenarios"""
            },
            {
                "role": "user",
                "content": f"Generate technical questions for someone with {experience_years} years experience in {tech_list}"
            }
        ]
        
        response = self._make_api_call(messages, max_tokens=800)
        
        # Extract questions from numbered list
        questions = []
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line):
                question = re.sub(r'^\d+\.\s*', '', line)
                questions.append(question)
        
        return questions[:5]  # Limit to 5 questions
    
    def validate_tech_stack(self, tech_input: str) -> List[str]:
        """Validate and clean tech stack input"""
        messages = [
            {
                "role": "system",
                "content": """You are a tech stack validator. Extract valid programming languages, frameworks, databases, and tools from the user's input.
                
                Rules:
                1. Return only legitimate tech stack items
                2. Correct common misspellings (e.g., "reactjs" -> "React")
                3. Use standard naming (e.g., "NodeJS" -> "Node.js")
                4. Return as a JSON array of strings
                5. Remove duplicates and irrelevant items
                
                Common categories:
                - Languages: Python, JavaScript, Java, C++, etc.
                - Frameworks: React, Django, Spring, etc.
                - Databases: MySQL, PostgreSQL, MongoDB, etc.
                - Tools: Git, Docker, AWS, etc."""
            },
            {
                "role": "user",
                "content": f"Clean and validate this tech stack: {tech_input}"
            }
        ]
        
        response = self._make_api_call(messages, max_tokens=300)
        
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: split by common separators
                items = re.split(r'[,;]\s*', tech_input)
                return [item.strip().title() for item in items if item.strip()]
        except json.JSONDecodeError:
            # Fallback parsing
            items = re.split(r'[,;]\s*', tech_input)
            return [item.strip().title() for item in items if item.strip()]
    
    def generate_response(self, user_input: str, context: str = "") -> str:
        """Generate contextual response to user input"""
        messages = [
            {
                "role": "system",
                "content": f"""You are a professional hiring assistant for TalentScout. 
                Context: {context}
                
                Respond professionally and helpfully to the candidate's input. 
                Keep responses concise and relevant to the hiring process."""
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        return self._make_api_call(messages, max_tokens=300)
    
    def generate_ending_message(self, candidate_name: str = "") -> str:
        """Generate a professional ending message"""
        messages = [
            {
                "role": "system",
                "content": """Generate a professional and warm ending message for a hiring interview. 
                Thank the candidate, mention next steps, and provide a positive closing."""
            },
            {
                "role": "user",
                "content": f"Generate an ending message for candidate: {candidate_name}"
            }
        ]
        return self._make_api_call(messages, max_tokens=300)
