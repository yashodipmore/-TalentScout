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
    st.session_state.phase = "collecting_info"  # "collecting_info" or "technical_questions"

def extract_info_from_input(user_input, expected_field=None):
    """Extract specific information based on current step"""
    user_lower = user_input.lower()
    extracted = {}
    
    # If we're expecting a specific field, try to extract that first
    if expected_field == "name":
        # Just treat the input as name if it looks like one
        if len(user_input.split()) <= 4 and not any(char in user_input for char in ['@', '.com', ':', 'http']):
            extracted['name'] = user_input.strip()
    
    elif expected_field == "email":
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        if emails:
            extracted['email'] = emails[0]
    
    elif expected_field == "phone":
        phone_pattern = r'\b\d{10,15}\b'
        phones = re.findall(phone_pattern, user_input)
        if phones:
            extracted['phone'] = phones[0]
    
    elif expected_field == "experience":
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            if 'month' in user_lower:
                extracted['experience'] = numbers[0] + ' months'
            else:
                extracted['experience'] = numbers[0] + ' years'
    
    elif expected_field == "position":
        # Clean up the position
        if 'software engineer' in user_lower:
            extracted['position'] = 'Software Engineer'
        elif 'data scientist' in user_lower:
            extracted['position'] = 'Data Scientist'
        elif 'developer' in user_lower:
            extracted['position'] = user_input.strip().title()
        else:
            extracted['position'] = user_input.strip().title()
    
    elif expected_field == "location":
        # Clean location input
        extracted['location'] = user_input.strip()
    
    elif expected_field == "tech_stack":
        extracted['tech_stack'] = user_input.strip()
    
    # Also try general extraction for any other info mentioned
    # Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_input)
    if emails and 'email' not in extracted:
        extracted['email'] = emails[0]
    
    # Phone
    phone_pattern = r'\b\d{10,15}\b'
    phones = re.findall(phone_pattern, user_input)
    if phones and 'phone' not in extracted:
        extracted['phone'] = phones[0]
    
    return extracted

def get_ai_response_for_questions(user_input, tech_stack):
    """Generate AI response for technical questions"""
    try:
        prompt = f"""You are a technical interviewer for TalentScout. The candidate's tech stack is: {tech_stack}

User asked: "{user_input}"

If they're asking for questions, generate 2-3 relevant technical questions based on their tech stack.
If they're answering technical questions, provide encouraging feedback and ask follow-up questions.
If they're asking in Hindi/other languages, respond in English but acknowledge their question.
If they're greeting or making conversation, respond professionally but guide them back to technical discussion.

Keep responses concise and professional."""

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I understand you'd like to continue our technical discussion. Could you please answer the questions I provided, or let me know if you'd like me to ask specific questions about any technology?"
    """Determine current step based on collected info"""
    steps = [
        ("name", "What's your **full name**?"),
        ("email", "Great! What's your **email address**?"),
        ("phone", "Perfect! Could you provide your **phone number**?"),
        ("experience", "Excellent! How much **work experience** do you have? (e.g., 2 years, 6 months)"),
        ("position", "What **position** are you looking for? (e.g., Software Engineer, Data Scientist)"),
        ("location", "What's your current **location** or preferred work location?"),
        ("tech_stack", "Finally, tell me about your **tech stack** - what programming languages, frameworks, and tools do you know?")
    ]
    
    for field, question in steps:
        if field not in st.session_state.candidate_info or not st.session_state.candidate_info[field]:
            return field, question
    
    return None, None

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
        st.session_state.phase = "collecting_info"
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

I'm your AI hiring assistant for technology positions. I'll collect some basic information about you step by step, then ask a few technical questions.

**Let's start with your full name.**"""
    
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.markdown(f'<div class="bot-msg"><strong>🤖 TalentScout AI:</strong><br>{greeting}</div>', unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Check for conversation end
    if any(word in user_input.lower() for word in ['bye', 'done', 'thank you', 'thanks', 'quit', 'exit']):
        response = f"""Thank you for your time! 

**📋 Your Information Summary:**
{chr(10).join([f"• **{k.title()}:** {v}" for k, v in st.session_state.candidate_info.items() if v])}

**🔄 Next Steps:**
• Technical team review: 1-2 business days
• You'll hear back within 2-3 business days  
• If selected, we'll schedule a detailed interview

Thank you for your interest in TalentScout! 🎯"""
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    # Get current step
    current_field, current_question = get_current_step()
    
    # Extract information based on current step
    if current_field:
        extracted = extract_info_from_input(user_input, current_field)
        
        # Update candidate info
        for key, value in extracted.items():
            if value:
                st.session_state.candidate_info[key] = value
        
        # Get next step
        next_field, next_question = get_current_step()
        
        if next_question:
            # Still collecting info
            if extracted:
                # Acknowledge what was captured
                acknowledged = []
                for key, value in extracted.items():
                    acknowledged.append(f"**{key.title()}:** {value}")
                
                response = f"Thank you! I've noted:\n" + "\n".join(acknowledged) + f"\n\n{next_question}"
            else:
                response = f"I didn't catch that. {current_question}"
        else:
            # All info collected - show technical questions
            response = f"""Perfect! I have all your information. Here's your profile summary:

**📋 Profile Summary:**
• **Name:** {st.session_state.candidate_info.get('name', 'Not provided')}
• **Email:** {st.session_state.candidate_info.get('email', 'Not provided')}
• **Phone:** {st.session_state.candidate_info.get('phone', 'Not provided')}
• **Experience:** {st.session_state.candidate_info.get('experience', 'Not provided')}
• **Position:** {st.session_state.candidate_info.get('position', 'Not provided')}
• **Location:** {st.session_state.candidate_info.get('location', 'Not provided')}
• **Tech Stack:** {st.session_state.candidate_info.get('tech_stack', 'Not provided')}

Now, let's proceed with some technical questions:

**🎯 Technical Assessment Questions:**

1. **Problem Solving:** How would you approach debugging a slow-performing web application?

2. **Code Quality:** What practices do you follow for writing clean, maintainable code?

3. **Technology Specific:** Describe a challenging project you've worked on and how you solved the technical difficulties.

4. **Best Practices:** How do you handle error management and ensure code security in your applications?

Please answer these questions thoughtfully. Type **'done'** when finished or **'bye'** to end the conversation."""
    
    else:
        # Shouldn't reach here, but just in case
        response = "I think we have all the information we need. Thank you!"
    
    # Add AI response
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Footer
st.markdown("---")
st.markdown("🎯 **TalentScout** - Connecting top tech talent with amazing opportunities!")
