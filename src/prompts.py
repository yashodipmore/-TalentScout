"""
Prompt templates for TalentScout Hiring Assistant

This module contains all the prompt templates used for different conversation stages.
"""

class PromptTemplates:
    """Collection of prompt templates for the hiring assistant"""
    
    @staticmethod
    def get_welcome_prompt() -> str:
        """Welcome message template"""
        return """
        Hello! Welcome to TalentScout, your AI-powered hiring assistant! 🎯
        
        I'm here to help streamline your interview process by gathering some essential information about you and your technical background. This will take just a few minutes and will help us better understand your qualifications.
        
        Here's what we'll cover:
        1. Basic information (name, contact details, experience)
        2. Your technical skills and preferred tech stack
        3. A few technical questions based on your expertise
        
        Let's get started! Could you please tell me your full name?
        """
    
    @staticmethod
    def get_information_extraction_prompt() -> str:
        """Prompt for extracting candidate information"""
        return """
        You are an expert information extractor for a hiring assistant. Extract the following information from the user's message and return it as JSON:

        {
            "name": "full name if mentioned",
            "email": "email address if mentioned", 
            "phone": "phone number if mentioned",
            "experience_years": "number of years experience if mentioned (as integer)",
            "desired_position": "job position/title if mentioned",
            "location": "location/city if mentioned",
            "tech_stack": ["list", "of", "technologies", "mentioned"]
        }
        
        Rules:
        - Only include fields that are explicitly mentioned
        - For tech_stack, extract any programming languages, frameworks, databases, tools mentioned
        - Use null for missing fields
        - Be precise and don't infer information not clearly stated
        - Standardize technology names (e.g., "js" -> "JavaScript")
        """
    
    @staticmethod
    def get_conversation_prompt(candidate_info: dict, missing_info: list) -> str:
        """Generate conversation prompt based on current state"""
        
        if missing_info:
            missing_fields = {
                "name": "your full name",
                "email": "your email address", 
                "phone": "your phone number",
                "experience_years": "your years of experience",
                "desired_position": "the position you're interested in",
                "location": "your current location",
                "tech_stack": "your technical skills and preferred technologies"
            }
            
            next_field = missing_info[0]
            field_prompt = missing_fields.get(next_field, next_field)
            
            return f"""
            Thank you for that information! Could you please provide {field_prompt}?
            
            This helps us better match you with suitable opportunities and tailor our technical questions to your expertise.
            """
        
        return """
        Perfect! I have all the basic information I need. Now I'd like to ask you a few technical questions based on your experience and tech stack. These questions will help us assess your technical proficiency and problem-solving skills.
        
        Are you ready to proceed with the technical questions?
        """
    
    @staticmethod
    def get_technical_question_prompt(tech_stack: list, experience_years: int = None) -> str:
        """Generate prompt for technical questions"""
        
        experience_level = "mid"
        if experience_years:
            if experience_years < 2:
                experience_level = "junior"
            elif experience_years < 5:
                experience_level = "mid"
            else:
                experience_level = "senior"
        
        return f"""
        Based on your tech stack ({', '.join(tech_stack)}) and {experience_level}-level experience, I'll ask you a few technical questions.
        
        Please answer as thoroughly as you can. Feel free to explain your thought process, mention any trade-offs you consider, and provide examples from your experience when relevant.
        
        Let's start with the first question:
        """
    
    @staticmethod
    def get_question_generation_prompt(tech_stack: list, experience_level: str = "mid") -> str:
        """Prompt for generating technical questions"""
        
        return f"""
        Generate 3-5 technical interview questions for a {experience_level}-level software developer with expertise in: {', '.join(tech_stack)}.
        
        Requirements:
        1. Questions should be practical and scenario-based
        2. Cover different aspects: problem-solving, system design, best practices
        3. Appropriate difficulty for {experience_level} level
        4. Focus on real-world applications
        5. Allow for follow-up discussions
        
        For each question, provide:
        - The question text (clear and specific)
        - Primary technology it tests
        - Difficulty level (beginner/intermediate/advanced)  
        - Key concepts being evaluated
        
        Return as JSON array:
        [
            {{
                "question": "question text here",
                "technology": "primary technology",
                "difficulty": "difficulty level", 
                "concepts": ["concept1", "concept2", "concept3"]
            }}
        ]
        
        Make questions engaging and relevant to current industry practices.
        """
    
    @staticmethod
    def get_followup_prompt(previous_answer: str, question_context: str) -> str:
        """Generate follow-up questions based on answers"""
        
        return f"""
        Based on the candidate's answer: "{previous_answer}"
        
        To the question about: {question_context}
        
        Generate a thoughtful follow-up question that:
        1. Digs deeper into their understanding
        2. Explores practical implementation details
        3. Tests problem-solving approach
        4. Assesses best practices knowledge
        
        Keep it conversational and relevant to their response.
        """
    
    @staticmethod
    def get_farewell_prompt(candidate_name: str = "candidate") -> str:
        """Farewell message template"""
        
        return f"""
        Thank you, {candidate_name}, for taking the time to speak with me today! 
        
        I've gathered all the necessary information about your background and technical skills. Your responses have been recorded and will be reviewed by our hiring team.
        
        Here's what happens next:
        1. Our technical team will review your responses
        2. If there's a good fit, we'll reach out within 2-3 business days
        3. The next step would typically be a technical interview with our engineering team
        
        We appreciate your interest in opportunities with TalentScout, and we'll be in touch soon!
        
        Have a great day! 🚀
        """
    
    @staticmethod
    def get_error_handling_prompt() -> str:
        """Error handling message"""
        
        return """
        I apologize, but I didn't quite understand that. Could you please rephrase your response?
        
        If you're having trouble, you can:
        - Provide information step by step
        - Use simple, clear statements
        - Say "skip" if you don't want to provide certain information
        - Type "help" for assistance
        """
    
    @staticmethod
    def get_validation_prompt(field_name: str, invalid_value: str) -> str:
        """Validation error message"""
        
        validation_messages = {
            "email": "Please provide a valid email address (e.g., john@example.com)",
            "phone": "Please provide a valid phone number (e.g., +1-234-567-8900)", 
            "experience_years": "Please provide experience as a number (e.g., 3 years, 5, etc.)",
            "name": "Please provide your full name",
        }
        
        return validation_messages.get(field_name, f"Please provide a valid {field_name}")
    
    @staticmethod
    def get_tech_stack_clarification_prompt(mentioned_techs: list) -> str:
        """Clarify tech stack information"""
        
        if mentioned_techs:
            return f"""
            I noticed you mentioned: {', '.join(mentioned_techs)}
            
            Could you tell me more about your technical skills? Please include:
            - Programming languages you're proficient in
            - Frameworks and libraries you've worked with
            - Databases you have experience with
            - Any cloud platforms or development tools you use
            
            This helps me ask more relevant technical questions!
            """
        else:
            return """
            Could you tell me about your technical skills and experience? Please include:
            - Programming languages you know
            - Frameworks and libraries you've used
            - Databases you've worked with  
            - Any cloud platforms or development tools
            
            For example: "I work with Python, Django, PostgreSQL, and AWS"
            """
