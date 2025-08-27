"""
Utility functions for TalentScout Hiring Assistant

This module contains helper functions for validation, data processing, and other utilities.
"""

import re
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone is valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove common formatting characters
    cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if it contains only digits and is reasonable length
    if not cleaned_phone.isdigit():
        return False
    
    # Phone should be between 7 and 15 digits
    return 7 <= len(cleaned_phone) <= 15

def extract_experience_years(text: str) -> Optional[int]:
    """
    Extract years of experience from text
    
    Args:
        text: Text containing experience information
        
    Returns:
        Number of years as integer, or None if not found
    """
    if not text:
        return None
    
    # Try to convert directly to int first
    try:
        return int(text)
    except ValueError:
        pass
    
    # Look for patterns like "3 years", "5 yrs", "2.5 years"
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
        r'(\d+(?:\.\d+)?)\s*(?:year|yr)',
        r'(\d+)(?:\+|\s*plus)?'
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                years = float(match.group(1))
                return int(years)  # Convert to int, rounding down
            except ValueError:
                continue
    
    return None

def standardize_tech_name(tech: str) -> str:
    """
    Standardize technology names
    
    Args:
        tech: Technology name to standardize
        
    Returns:
        Standardized technology name
    """
    if not tech:
        return tech
    
    # Common standardizations
    standardizations = {
        'js': 'JavaScript',
        'javascript': 'JavaScript',
        'ts': 'TypeScript',
        'typescript': 'TypeScript',
        'py': 'Python',
        'python': 'Python',
        'java': 'Java',
        'c#': 'C#',
        'csharp': 'C#',
        'cpp': 'C++',
        'c++': 'C++',
        'golang': 'Go',
        'go': 'Go',
        'node': 'Node.js',
        'nodejs': 'Node.js',
        'node.js': 'Node.js',
        'react': 'React',
        'reactjs': 'React',
        'vue': 'Vue.js',
        'vuejs': 'Vue.js',
        'vue.js': 'Vue.js',
        'angular': 'Angular',
        'angularjs': 'AngularJS',
        'django': 'Django',
        'flask': 'Flask',
        'express': 'Express.js',
        'expressjs': 'Express.js',
        'express.js': 'Express.js',
        'spring': 'Spring',
        'springboot': 'Spring Boot',
        'spring boot': 'Spring Boot',
        'mysql': 'MySQL',
        'postgresql': 'PostgreSQL',
        'postgres': 'PostgreSQL',
        'mongodb': 'MongoDB',
        'mongo': 'MongoDB',
        'redis': 'Redis',
        'sqlite': 'SQLite',
        'aws': 'AWS',
        'amazon web services': 'AWS',
        'gcp': 'Google Cloud',
        'google cloud platform': 'Google Cloud',
        'azure': 'Microsoft Azure',
        'docker': 'Docker',
        'kubernetes': 'Kubernetes',
        'k8s': 'Kubernetes',
        'git': 'Git',
        'github': 'GitHub',
        'gitlab': 'GitLab',
        'jenkins': 'Jenkins',
        'terraform': 'Terraform',
        'ansible': 'Ansible'
    }
    
    tech_lower = tech.lower().strip()
    return standardizations.get(tech_lower, tech.strip())

def get_tech_stack_categories() -> Dict[str, List[str]]:
    """
    Get categorized technology stacks
    
    Returns:
        Dictionary with technology categories
    """
    return {
        'Programming Languages': [
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C++', 
            'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala'
        ],
        'Frontend Frameworks': [
            'React', 'Vue.js', 'Angular', 'Svelte', 'Next.js', 'Nuxt.js',
            'Gatsby', 'jQuery', 'Bootstrap', 'Tailwind CSS'
        ],
        'Backend Frameworks': [
            'Django', 'Flask', 'FastAPI', 'Express.js', 'Spring Boot',
            'ASP.NET', 'Ruby on Rails', 'Laravel', 'Symfony'
        ],
        'Databases': [
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite',
            'Oracle', 'SQL Server', 'Cassandra', 'DynamoDB'
        ],
        'Cloud Platforms': [
            'AWS', 'Google Cloud', 'Microsoft Azure', 'DigitalOcean',
            'Heroku', 'Vercel', 'Netlify'
        ],
        'DevOps Tools': [
            'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI', 'GitHub Actions',
            'Terraform', 'Ansible', 'Chef', 'Puppet'
        ],
        'Mobile Development': [
            'React Native', 'Flutter', 'Swift', 'Kotlin', 'Xamarin',
            'Ionic', 'Cordova'
        ]
    }

def categorize_technology(tech: str) -> str:
    """
    Categorize a technology
    
    Args:
        tech: Technology name
        
    Returns:
        Category name
    """
    categories = get_tech_stack_categories()
    
    standardized_tech = standardize_tech_name(tech)
    
    for category, techs in categories.items():
        if standardized_tech in techs:
            return category
    
    return 'Other'

def format_tech_stack_display(tech_stack: List[str]) -> str:
    """
    Format tech stack for display
    
    Args:
        tech_stack: List of technologies
        
    Returns:
        Formatted string for display
    """
    if not tech_stack:
        return "No technologies specified"
    
    # Group by categories
    categories = {}
    for tech in tech_stack:
        category = categorize_technology(tech)
        if category not in categories:
            categories[category] = []
        categories[category].append(standardize_tech_name(tech))
    
    # Format for display
    formatted_parts = []
    for category, techs in categories.items():
        if techs:
            formatted_parts.append(f"**{category}:** {', '.join(techs)}")
    
    return '\n'.join(formatted_parts)

def sanitize_input(text: str) -> str:
    """
    Sanitize user input
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>\"\'&]', '', text)
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000] + "..."
    
    return sanitized.strip()

def extract_keywords_from_text(text: str) -> List[str]:
    """
    Extract important keywords from text
    
    Args:
        text: Text to extract keywords from
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction based on common tech terms
    tech_keywords = []
    categories = get_tech_stack_categories()
    
    text_lower = text.lower()
    
    for category, techs in categories.items():
        for tech in techs:
            if tech.lower() in text_lower:
                tech_keywords.append(tech)
    
    return list(set(tech_keywords))

def generate_interview_summary(candidate_info: dict, questions: List[dict]) -> str:
    """
    Generate a summary of the interview
    
    Args:
        candidate_info: Candidate information dictionary
        questions: List of questions asked
        
    Returns:
        Interview summary string
    """
    summary_parts = []
    
    # Candidate details
    summary_parts.append(f"**Candidate:** {candidate_info.get('name', 'Unknown')}")
    summary_parts.append(f"**Experience:** {candidate_info.get('experience_years', 'Unknown')} years")
    summary_parts.append(f"**Position:** {candidate_info.get('desired_position', 'Unknown')}")
    
    # Tech stack
    tech_stack = candidate_info.get('tech_stack', [])
    if tech_stack:
        summary_parts.append(f"**Technologies:** {', '.join(tech_stack[:5])}")
    
    # Questions asked
    if questions:
        summary_parts.append(f"**Questions Asked:** {len(questions)}")
        tech_areas = list(set([q.get('technology', '') for q in questions if q.get('technology')]))
        if tech_areas:
            summary_parts.append(f"**Areas Covered:** {', '.join(tech_areas)}")
    
    return '\n'.join(summary_parts)
