"""
Data models for the TalentScout Hiring Assistant

This module contains Pydantic models for structured data handling.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from enum import Enum

class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"

class TechCategory(str, Enum):
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    FRONTEND = "frontend"
    BACKEND = "backend"
    MOBILE = "mobile"
    OTHER = "other"

class CandidateInfo(BaseModel):
    """Model for candidate information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    experience_years: Optional[int] = None
    desired_position: Optional[str] = None
    location: Optional[str] = None
    tech_stack: List[str] = []
    
    @validator('experience_years')
    def validate_experience(cls, v):
        if v is not None and (v < 0 or v > 50):
            raise ValueError('Experience years must be between 0 and 50')
        return v
    
    @validator('tech_stack')
    def validate_tech_stack(cls, v):
        if len(v) > 20:
            raise ValueError('Too many technologies listed (max 20)')
        return v

class TechnicalQuestion(BaseModel):
    """Model for technical questions"""
    technology: str
    question: str
    difficulty_level: str
    category: TechCategory
    expected_concepts: List[str] = []

class ConversationState(BaseModel):
    """Model for tracking conversation state"""
    candidate_info: CandidateInfo = CandidateInfo()
    current_step: str = "greeting"  # greeting, info_gathering, tech_questions, conclusion
    information_complete: bool = False
    questions_generated: bool = False
    interview_complete: bool = False
    technical_questions: List[TechnicalQuestion] = []
    missing_info: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True

class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = {}

class InterviewSession(BaseModel):
    """Model for complete interview session"""
    session_id: str
    candidate_info: CandidateInfo
    conversation_history: List[ChatMessage]
    technical_questions: List[TechnicalQuestion]
    status: str
    created_at: str
    completed_at: Optional[str] = None
