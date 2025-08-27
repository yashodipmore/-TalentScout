"""
Candidate data models and validation for TalentScout Hiring Assistant
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import re
from datetime import datetime

@dataclass
class CandidateInfo:
    """Candidate information data model"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    experience_years: Optional[str] = None
    desired_position: Optional[str] = None
    location: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize tech_stack as empty list if None"""
        if self.tech_stack is None:
            self.tech_stack = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_complete(self) -> bool:
        """Check if all required information is collected"""
        required_fields = [
            self.full_name, self.email, self.phone, 
            self.experience_years, self.desired_position, 
            self.location, self.tech_stack
        ]
        return all(field for field in required_fields) and len(self.tech_stack) > 0
    
    def missing_fields(self) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        
        if not self.full_name:
            missing.append("full_name")
        if not self.email:
            missing.append("email")
        if not self.phone:
            missing.append("phone")
        if not self.experience_years:
            missing.append("experience_years")
        if not self.desired_position:
            missing.append("desired_position")
        if not self.location:
            missing.append("location")
        if not self.tech_stack or len(self.tech_stack) == 0:
            missing.append("tech_stack")
            
        return missing
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update candidate info from dictionary"""
        for key, value in data.items():
            if hasattr(self, key) and value:
                setattr(self, key, value)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Check if it has 10-15 digits
        return 10 <= len(digits_only) <= 15
    
    @staticmethod
    def clean_experience_years(experience: str) -> str:
        """Extract and clean experience years"""
        # Extract first number found
        numbers = re.findall(r'\d+', str(experience))
        if numbers:
            return numbers[0]
        return experience

@dataclass 
class TechnicalQuestion:
    """Technical question data model"""
    question: str
    technology: str
    difficulty: str = "medium"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class ConversationSession:
    """Conversation session data model"""
    session_id: str
    candidate: CandidateInfo
    state: str
    messages: List[Dict[str, str]]
    technical_questions: List[TechnicalQuestion]
    current_question_index: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        """Initialize session with current timestamp"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if not hasattr(self, 'messages') or self.messages is None:
            self.messages = []
        if not hasattr(self, 'technical_questions') or self.technical_questions is None:
            self.technical_questions = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        history = []
        for msg in self.messages:
            role = "Assistant" if msg["role"] == "assistant" else "Candidate"
            history.append(f"{role}: {msg['content']}")
        return "\n".join(history)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "candidate": self.candidate.to_dict(),
            "state": self.state,
            "messages": self.messages,
            "technical_questions": [q.to_dict() for q in self.technical_questions],
            "current_question_index": self.current_question_index,
            "created_at": self.created_at.isoformat()
        }

class SessionManager:
    """Manages conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
    
    def create_session(self, session_id: str) -> ConversationSession:
        """Create new conversation session"""
        session = ConversationSession(
            session_id=session_id,
            candidate=CandidateInfo(),
            state="greeting",
            messages=[],
            technical_questions=[]
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, session: ConversationSession) -> None:
        """Update session data"""
        self.sessions[session_id] = session
    
    def delete_session(self, session_id: str) -> None:
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
