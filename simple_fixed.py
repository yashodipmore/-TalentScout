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

# Custom CSS with better contrast
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
    background-color: #fff3cd;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #ffc107;
    margin: 15px 0;
    color: #856404 !important;
}
h1, h2, h3, h4, h5, h6 {
    color: #333333 !important;
}
.stMarkdown {
    color: #333333 !important;
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
    st.session_state.stage = "greeting"

def get_ai_response(prompt):
    """Get response from Groq API"""
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def extract_info(user_input):
    """Extract information from user input"""
    user_lower = user_input.lower()
    
    # Extract name
    if any(phrase in user_lower for phrase in ['my name is', 'i am', 'i\'m', 'call me']):
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ['am', 'is', 'me'] and i + 1 < len(words):
                name = ' '.join(words[i+1:]).strip('.,!')
                st.session_state.candidate_info['name'] = name
                break
    
    # Extract email
    if '@' in user_input:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        if emails:
            st.session_state.candidate_info['email'] = emails[0]
    
    # Extract phone
    phone_pattern = r'\b\d{10,15}\b'
    phones = re.findall(phone_pattern, user_input)
    if phones:
        st.session_state.candidate_info['phone'] = phones[0]
    
    # Extract experience
    if 'year' in user_lower:
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            st.session_state.candidate_info['experience'] = numbers[0] + ' years'
    
    # Extract tech stack
    tech_keywords = ['python', 'java', 'javascript', 'react', 'node', 'django', 'flask', 'sql', 'html', 'css']
    found_tech = [tech for tech in tech_keywords if tech in user_lower]
    if found_tech:
        st.session_state.candidate_info['tech_stack'] = ', '.join(found_tech)

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Progress")
    required_info = ['name', 'email', 'phone', 'experience', 'tech_stack']
    collected_count = sum(1 for key in required_info if key in st.session_state.candidate_info)
    st.progress(collected_count / len(required_info))
    st.write(f"Collected: {collected_count}/{len(required_info)} items")
    
    if st.session_state.candidate_info:
        st.markdown("### 👤 Your Info")
        for key, value in st.session_state.candidate_info.items():
            st.write(f"**{key.title()}:** {value}")
    
    if st.button("🔄 Reset"):
        st.session_state.messages = []
        st.session_state.candidate_info = {}
        st.session_state.stage = "greeting"
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

I'm your AI hiring assistant. I'll help you with initial screening for tech positions.

Let's start by collecting some basic information:

**Could you please tell me your full name?**"""
    
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.markdown(f'<div class="bot-msg"><strong>🤖 TalentScout AI:</strong><br>{greeting}</div>', unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Extract information
    extract_info(user_input)
    
    # Generate response based on what's missing
    missing_info = []
    if 'name' not in st.session_state.candidate_info:
        missing_info.append("name")
    elif 'email' not in st.session_state.candidate_info:
        missing_info.append("email")
    elif 'phone' not in st.session_state.candidate_info:
        missing_info.append("phone number")
    elif 'experience' not in st.session_state.candidate_info:
        missing_info.append("years of experience")
    elif 'tech_stack' not in st.session_state.candidate_info:
        missing_info.append("tech stack")
    
    # Create response
    if missing_info:
        if 'name' in missing_info:
            response = "Nice to meet you! Could you please tell me your **full name**?"
        elif 'email' in missing_info:
            response = f"Thank you, {st.session_state.candidate_info.get('name', '')}! Now I need your **email address**."
        elif 'phone' in missing_info:
            response = "Great! Could you please provide your **phone number**?"
        elif 'experience' in missing_info:
            response = "Perfect! How many **years of experience** do you have in technology?"
        elif 'tech_stack' in missing_info:
            response = "Excellent! Now tell me about your **tech stack** - what programming languages, frameworks, and tools do you work with?"
    else:
        # All info collected, show technical questions
        tech_stack = st.session_state.candidate_info.get('tech_stack', 'general programming')
        response = f"""Perfect! I have all your information. Based on your tech stack ({tech_stack}), here are some technical questions:

**Technical Assessment:**

1. **Problem Solving:** How would you debug a slow-performing web application?

2. **Code Quality:** What practices do you follow for writing clean, maintainable code?

3. **Technology:** Can you describe a challenging project you worked on with {tech_stack}?

4. **Best Practices:** How do you handle error management and security in your applications?

Please answer these questions thoughtfully. Type 'done' when finished or 'bye' to end."""
    
    # Handle conversation end
    if any(word in user_input.lower() for word in ['bye', 'done', 'finished']):
        response = f"""Thank you for your time! 

**📋 Summary:**
{chr(10).join([f"• **{k.title()}:** {v}" for k, v in st.session_state.candidate_info.items()])}

**🔄 Next Steps:**
• Technical team review: 1-2 business days
• You'll hear back within 2-3 business days
• If selected, we'll schedule a detailed interview

Thank you for your interest in TalentScout! 🎯"""
    
    # Add AI response
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Footer
st.markdown("---")
st.markdown("🎯 **TalentScout** - Connecting top tech talent with amazing opportunities!")
