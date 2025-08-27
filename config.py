"""
Configuration settings for TalentScout Hiring Assistant
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-8b-8192"  # Fast and reliable model

# App Configuration
APP_TITLE = os.getenv("APP_TITLE", "TalentScout Hiring Assistant")
COMPANY_NAME = os.getenv("COMPANY_NAME", "TalentScout")
MAX_QUESTIONS_PER_TECH = int(os.getenv("MAX_QUESTIONS_PER_TECH", "3"))

# Conversation States
class ConversationState:
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    COLLECTING_TECH_STACK = "collecting_tech_stack"
    GENERATING_QUESTIONS = "generating_questions"
    ASKING_QUESTIONS = "asking_questions"
    ENDING = "ending"

# Required Information Fields
REQUIRED_INFO = [
    "full_name",
    "email",
    "phone",
    "experience_years",
    "desired_position",
    "location",
    "tech_stack"
]

# Common Tech Stacks for validation
COMMON_TECH_STACKS = {
    "programming_languages": [
        "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "PHP", 
        "Ruby", "Swift", "Kotlin", "TypeScript", "Scala", "R"
    ],
    "frameworks": [
        "React", "Angular", "Vue.js", "Django", "Flask", "FastAPI", "Spring Boot",
        "Express.js", "Next.js", "Laravel", "Ruby on Rails", ".NET"
    ],
    "databases": [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite", "Oracle",
        "SQL Server", "Cassandra", "DynamoDB", "Neo4j"
    ],
    "cloud_platforms": [
        "AWS", "Google Cloud", "Azure", "Docker", "Kubernetes", "Heroku"
    ],
    "tools": [
        "Git", "Jenkins", "Docker", "Kubernetes", "Terraform", "Ansible"
    ]
}

# Conversation ending keywords
ENDING_KEYWORDS = [
    "bye", "goodbye", "exit", "quit", "end", "stop", "thanks", "thank you",
    "that's all", "no more questions", "done", "finish"
]
