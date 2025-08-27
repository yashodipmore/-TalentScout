import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

# Initialize Groq client
@st.cache_resource
def init_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

client = init_groq_client()

# Page configuration
st.set_page_config(
    page_title="TalentScout - AI Hiring Assistant",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
}
.user-msg {
    background-color: #dcf8c6;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border: 1px solid #4caf50;
    color: #2e7d32 !important;
}
.bot-msg {
    background-color: #f0f0f0;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border: 1px solid #9c27b0;
    color: #333333 !important;
}
.info-box {
    background-color: #e8f5e8;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #4caf50;
    margin: 15px 0;
    color: #2e7d32 !important;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎯 TalentScout</h1>
    <h3>AI-Powered Hiring Assistant</h3>
    <p>Specialized in Technology Talent Recruitment</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.candidate_info = {}
    st.session_state.current_step = 0

def extract_info_smart(user_input):
    """Smart information extraction"""
    user_lower = user_input.lower()
    extracted = {}
    
    # Extract name - improved logic
    if any(phrase in user_lower for phrase in ['my name is', 'i am', 'i\'m', 'call me']):
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ['am', 'is', 'me'] and i + 1 < len(words):
                extracted['name'] = ' '.join(words[i+1:]).strip('.,!"')
                break
    # If it's just a name (2-3 words, starts with capital)
    elif len(user_input.split()) <= 3 and user_input[0].isupper() and not any(char in user_input for char in ['@', '.com', ':', 'year']):
        extracted['name'] = user_input.strip()
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_input)
    if emails:
        extracted['email'] = emails[0]
    
    # Extract phone
    phone_pattern = r'\b\d{10,15}\b'
    phones = re.findall(phone_pattern, user_input)
    if phones:
        extracted['phone'] = phones[0]
    
    # Extract experience
    if 'year' in user_lower or 'month' in user_lower or 'experience' in user_lower:
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            if 'month' in user_lower:
                extracted['experience'] = numbers[0] + ' months'
            else:
                extracted['experience'] = numbers[0] + ' years'
    
    # Extract position
    positions = ['software engineer', 'data scientist', 'frontend developer', 'backend developer', 'full stack developer', 'ai engineer', 'ml engineer', 'web developer', 'mobile developer']
    for pos in positions:
        if pos in user_lower:
            extracted['position'] = pos.title()
            break
    
    # Extract location (improved) - look for city/state names
    location_keywords = ['pune', 'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'shirpur', 'maharashtra', 'india', 'kolkata', 'ahmedabad', 'surat', 'nagpur']
    found_locations = [loc for loc in location_keywords if loc in user_lower]
    if found_locations:
        # Extract the part that contains location
        if 'shirpur' in user_lower and 'maharashtra' in user_lower:
            extracted['location'] = 'Shirpur, Maharashtra'
        elif any(city in user_lower for city in ['pune', 'mumbai', 'delhi', 'bangalore']):
            for city in ['pune', 'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai']:
                if city in user_lower:
                    extracted['location'] = city.title()
                    break
        else:
            extracted['location'] = ', '.join([loc.title() for loc in found_locations])
    
    # Extract tech stack
    if any(indicator in user_lower for indicator in ['languages:', 'frameworks:', 'tools:', 'tech stack', 'technologies', 'python', 'java', 'javascript']):
        # Check if it's a comprehensive list
        if 'languages:' in user_lower or 'frameworks:' in user_lower:
            extracted['tech_stack'] = user_input.strip()
        else:
            # Extract individual technologies
            tech_keywords = ['python', 'java', 'javascript', 'react', 'node', 'django', 'flask', 'sql', 'html', 'css', 'tensorflow', 'pytorch', 'fastapi', 'streamlit', 'pandas', 'numpy', 'mongodb', 'postgresql', 'mysql', 'git', 'docker', 'aws', 'azure', 'gcp']
            found_tech = [tech for tech in tech_keywords if tech in user_lower]
            if found_tech:
                extracted['tech_stack'] = ', '.join(found_tech)
    
    return extracted

def get_next_question(info):
    """Get the next question based on missing info"""
    questions = [
        ("name", "Could you please tell me your **full name**?"),
        ("email", "Great! Now I need your **email address**."),
        ("phone", "Perfect! Could you provide your **phone number**?"),
        ("experience", "Excellent! How much **experience** do you have in technology? (e.g., 2 years, 6 months)"),
        ("position", "What **position** are you looking for? (e.g., Software Engineer, Data Scientist)"),
        ("location", "What's your **location** or preferred work location?"),
        ("tech_stack", "Finally, tell me about your **tech stack** - what programming languages, frameworks, and tools do you know?")
    ]
    
    for field, question in questions:
        if field not in info or not info[field]:
            return question
    
    return None

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Progress")
    required_fields = ['name', 'email', 'phone', 'experience', 'position', 'location', 'tech_stack']
    completed = sum(1 for field in required_fields if field in st.session_state.candidate_info and st.session_state.candidate_info[field])
    
    progress = completed / len(required_fields)
    st.progress(progress)
    st.write(f"Completed: {completed}/{len(required_fields)} fields")
    
    if st.session_state.candidate_info:
        st.markdown("### 👤 Your Information")
        for key, value in st.session_state.candidate_info.items():
            if value:  # Only show non-empty values
                st.write(f"**{key.title()}:** {value}")
    
    if st.button("🔄 Reset Chat"):
        st.session_state.messages = []
        st.session_state.candidate_info = {}
        st.session_state.current_step = 0
        st.rerun()

# Main chat area
st.markdown("### 💬 Conversation")

# Display messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-msg"><strong>👤 You:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg"><strong>🤖 TalentScout AI:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)

# Initial greeting
if not st.session_state.messages:
    greeting = """Hello! Welcome to TalentScout! 👋

I'm your AI hiring assistant for technology positions. I'll collect some basic information about you and then ask a few technical questions.

**Let's start simple - what's your full name?**"""
    
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.markdown(f'<div class="bot-msg"><strong>🤖 TalentScout AI:</strong><br>{greeting}</div>', unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Extract information
    extracted = extract_info_smart(user_input)
    
    # Update candidate info with any extracted information
    for key, value in extracted.items():
        if value and (key not in st.session_state.candidate_info or not st.session_state.candidate_info[key]):
            st.session_state.candidate_info[key] = value
    
    # Check if all info is collected
    required_fields = ['name', 'email', 'phone', 'experience', 'position', 'location', 'tech_stack']
    all_collected = all(
        field in st.session_state.candidate_info and 
        st.session_state.candidate_info[field] 
        for field in required_fields
    )
    
    # Generate response
    if all_collected:
        # All info collected - show technical questions
        tech_stack = st.session_state.candidate_info.get('tech_stack', 'programming')
        response = f"""Perfect! I have all your information. Here's your profile summary:

**📋 Profile Summary:**
• **Name:** {st.session_state.candidate_info.get('name')}
• **Email:** {st.session_state.candidate_info.get('email')}
• **Phone:** {st.session_state.candidate_info.get('phone')}
• **Experience:** {st.session_state.candidate_info.get('experience')}
• **Position:** {st.session_state.candidate_info.get('position')}
• **Location:** {st.session_state.candidate_info.get('location')}
• **Tech Stack:** {tech_stack}

Now, let's proceed with some technical questions based on your background:

**🎯 Technical Assessment Questions:**

1. **Problem Solving:** How would you approach debugging a slow-performing web application?

2. **Code Quality:** What practices do you follow for writing clean, maintainable code?

3. **Technology Specific:** Describe a challenging project you've worked on with your tech stack and how you solved the technical difficulties.

4. **Best Practices:** How do you handle error management and ensure code security in your applications?

Please answer these questions thoughtfully. Type **'done'** when finished or **'bye'** to end the conversation."""

    elif any(word in user_input.lower() for word in ['bye', 'done', 'thank you', 'thanks']):
        # End conversation
        response = f"""Thank you for your time! 

**📋 Summary:**
{chr(10).join([f"• **{k.title()}:** {v}" for k, v in st.session_state.candidate_info.items() if v])}

**🔄 Next Steps:**
• Technical team review: 1-2 business days
• You'll hear back within 2-3 business days  
• If selected, we'll schedule a detailed interview

Thank you for your interest in TalentScout! 🎯"""

    else:
        # Still collecting info
        next_question = get_next_question(st.session_state.candidate_info)
        
        if extracted:
            # Acknowledge what was captured
            acknowledged = []
            for key, value in extracted.items():
                acknowledged.append(f"**{key.title()}:** {value}")
            
            if next_question:
                response = f"Thank you! I've noted:\n" + "\n".join(acknowledged) + f"\n\n{next_question}"
            else:
                response = "Great! I have all the information I need."
        else:
            # Ask the next question
            if next_question:
                response = next_question
            else:
                response = "I need a bit more information. Could you please provide your missing details?"
    
    # Add AI response
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Footer
st.markdown("---")
st.markdown("🎯 **TalentScout** - Connecting top tech talent with amazing opportunities!")
