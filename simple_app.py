import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Groq client
@st.cache_resource
def init_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

client = init_groq_client()

def get_ai_response(messages):
    """Get response from Groq API"""
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Page config
st.set_page_config(
    page_title="TalentScout - AI Hiring Assistant",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS for better UI
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
.chat-message {
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
}
.user-message {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
}
.bot-message {
    background-color: #f3e5f5;
    border-left: 4px solid #9c27b0;
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

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Process Steps")
    st.markdown("""
    1. **Basic Information** 👤
    2. **Tech Stack Declaration** 💻
    3. **Technical Questions** 🎯
    4. **Summary & Next Steps** 📋
    """)
    
    if st.session_state.candidate_info:
        st.markdown("### 👤 Your Info")
        for key, value in st.session_state.candidate_info.items():
            st.markdown(f"**{key.title()}:** {value}")
    
    if st.button("🔄 Start Over"):
        st.session_state.messages = []
        st.session_state.candidate_info = {}
        st.session_state.stage = "greeting"
        st.experimental_rerun()

# Main chat area
st.markdown("### 💬 Chat Interface")

# Display messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message bot-message"><strong>TalentScout AI:</strong> {message["content"]}</div>', unsafe_allow_html=True)

# Initial greeting
if not st.session_state.messages:
    greeting = """Hello! Welcome to TalentScout! 👋

I'm your AI hiring assistant, here to help with your initial screening for technology positions.

I'll guide you through a quick process:
1. **Collect your basic information** (name, contact, experience)
2. **Learn about your tech stack** (programming languages, frameworks, tools)
3. **Ask some technical questions** based on your skills
4. **Provide next steps** for your application

Let's get started! Could you please tell me your **full name**?"""
    
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.markdown(f'<div class="chat-message bot-message"><strong>TalentScout AI:</strong> {greeting}</div>', unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process input based on current stage
    if st.session_state.stage == "greeting":
        st.session_state.stage = "collecting_info"
    
    # Create AI prompt based on current context
    context = f"""
    You are a professional hiring assistant for TalentScout, a tech recruitment agency.
    
    Current conversation stage: {st.session_state.stage}
    Candidate information collected so far: {json.dumps(st.session_state.candidate_info)}
    
    User's latest message: "{user_input}"
    
    Your tasks:
    1. Extract any relevant information from the user's message
    2. Ask for missing information naturally and professionally
    3. Once you have all basic info (name, email, phone, experience, desired position, location, tech stack), move to technical questions
    
    Required information to collect:
    - Full Name
    - Email Address
    - Phone Number
    - Years of Experience  
    - Desired Position(s)
    - Current Location
    - Tech Stack (programming languages, frameworks, databases, tools)
    
    Be conversational, professional, and ask for one piece of information at a time unless the user provides multiple items.
    """
    
    # Get AI response
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": user_input}
    ]
    
    ai_response = get_ai_response(messages)
    
    # Simple info extraction (you can make this more sophisticated)
    user_lower = user_input.lower()
    
    # Extract name
    if not st.session_state.candidate_info.get('name') and any(word in user_lower for word in ['name is', 'i am', 'i\'m', 'call me']):
        # Simple name extraction - you can improve this
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ['am', 'is'] and i + 1 < len(words):
                potential_name = ' '.join(words[i+1:i+3])
                st.session_state.candidate_info['name'] = potential_name.strip('.,!')
                break
    
    # Extract email
    if '@' in user_input and '.' in user_input:
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        if emails:
            st.session_state.candidate_info['email'] = emails[0]
    
    # Extract experience
    if 'year' in user_lower:
        import re
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            st.session_state.candidate_info['experience'] = numbers[0] + ' years'
    
    # Add AI response
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Check if conversation should end
    if any(word in user_lower for word in ['bye', 'goodbye', 'thank you', 'thanks', 'done']):
        summary = f"""
        Thank you for your time! Here's a summary of our conversation:
        
        **Your Information:**
        {json.dumps(st.session_state.candidate_info, indent=2)}
        
        **Next Steps:**
        • Our technical team will review your information
        • You'll hear back within 2-3 business days
        • If selected, we'll schedule a technical interview
        
        Thank you for your interest in TalentScout! 🎯
        """
        st.session_state.messages.append({"role": "assistant", "content": summary})
    
    st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("🎯 **TalentScout** - Connecting top tech talent with amazing opportunities!")
