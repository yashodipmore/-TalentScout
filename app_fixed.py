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

class TalentScoutChatbot:
    def __init__(self):
        self.model = "llama3-8b-8192"
        self.conversation_state = "greeting"
        self.candidate_info = {}
        
    def get_ai_response(self, messages, max_tokens=1000):
        """Get response from Groq API"""
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def generate_response(self, user_input, conversation_history):
        """Generate contextual response based on conversation state"""
        
        # Create system prompt based on current state
        if self.conversation_state == "greeting":
            system_prompt = """You are a friendly AI hiring assistant for TalentScout, a tech recruitment company.
            
            Start by greeting the candidate warmly and explaining that you'll help with initial screening.
            Ask for their full name to begin the process.
            
            Keep it professional but friendly."""
            
        elif self.conversation_state == "collecting_info":
            missing_info = self.get_missing_info()
            current_info = json.dumps(self.candidate_info, indent=2)
            
            system_prompt = f"""You are collecting candidate information for TalentScout.
            
            Current information collected: {current_info}
            Still need: {', '.join(missing_info)}
            
            Extract any relevant info from the user's message and ask for the next missing item naturally.
            
            Required info: name, email, phone, experience (years), desired position, location, tech stack.
            
            Be conversational and professional. Ask for one thing at a time unless they provide multiple items."""
            
        elif self.conversation_state == "technical_questions":
            system_prompt = """You are conducting a technical screening. Generate 3-4 relevant technical questions based on the candidate's tech stack.
            
            Make questions practical and assess real knowledge, not just theory.
            
            Present them clearly and ask the candidate to answer them."""
            
        else:
            system_prompt = "You are a professional hiring assistant. Respond helpfully and professionally."
        
        # Create messages for API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return self.get_ai_response(messages)
    
    def get_missing_info(self):
        """Get list of missing information fields"""
        required_fields = ['name', 'email', 'phone', 'experience', 'position', 'location', 'tech_stack']
        missing = []
        
        for field in required_fields:
            if field not in self.candidate_info or not self.candidate_info[field] or self.candidate_info[field].strip() == '':
                missing.append(field)
        
        return missing
    
    def extract_info(self, user_input):
        """Extract candidate information from user input"""
        user_lower = user_input.lower()
        
        # Extract name - improved logic
        if not self.candidate_info.get('name'):
            if any(phrase in user_lower for phrase in ['my name is', 'i am', 'i\'m', 'call me']):
                # Simple name extraction
                words = user_input.split()
                for i, word in enumerate(words):
                    if word.lower() in ['am', 'is'] and i + 1 < len(words):
                        potential_name = ' '.join(words[i+1:]).strip('.,!')
                        self.candidate_info['name'] = potential_name
                        break
            # Also capture if someone just states their name directly
            elif len(user_input.split()) <= 4 and any(char.isupper() for char in user_input):
                # Likely a name if it's short and has capital letters
                if not any(word in user_lower for word in ['email', 'phone', 'experience', 'year', '@']):
                    self.candidate_info['name'] = user_input.strip()
        
        # Extract email
        if '@' in user_input and '.' in user_input:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, user_input)
            if emails:
                self.candidate_info['email'] = emails[0]
        
        # Extract phone
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        phones = re.findall(phone_pattern, user_input)
        if phones and not self.candidate_info.get('phone'):
            # Simple validation - at least 10 digits
            for phone in phones:
                if len(re.sub(r'[^\d]', '', phone)) >= 10:
                    self.candidate_info['phone'] = phone
                    break
        
        # Extract experience
        if 'year' in user_lower and not self.candidate_info.get('experience'):
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                self.candidate_info['experience'] = numbers[0] + ' years'
        
        # Extract position - improved logic  
        position_keywords = ['developer', 'engineer', 'programmer', 'analyst', 'manager', 'architect', 'consultant', 'designer', 'scientist', 'intern']
        if any(word in user_lower for word in position_keywords) and not self.candidate_info.get('position'):
            # Extract the position title
            if 'software engineer' in user_lower:
                self.candidate_info['position'] = 'Software Engineer'
            elif 'data scientist' in user_lower:
                self.candidate_info['position'] = 'Data Scientist' 
            elif 'full stack developer' in user_lower:
                self.candidate_info['position'] = 'Full Stack Developer'
            elif 'frontend developer' in user_lower:
                self.candidate_info['position'] = 'Frontend Developer'
            elif 'backend developer' in user_lower:
                self.candidate_info['position'] = 'Backend Developer'
            else:
                # Find the position keyword and context
                for keyword in position_keywords:
                    if keyword in user_lower:
                        words = user_input.split()
                        for i, word in enumerate(words):
                            if word.lower() == keyword:
                                # Take word before and after if available
                                if i > 0:
                                    self.candidate_info['position'] = f"{words[i-1]} {words[i]}".title()
                                else:
                                    self.candidate_info['position'] = words[i].title()
                                break
                        break
        
        # Extract location - improved logic
        if not self.candidate_info.get('location'):
            # Look for location patterns
            location_indicators = ['from', 'live in', 'located in', 'based in', 'maharashtra', 'mumbai', 'pune', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'kolkata', 'india']
            
            if any(indicator in user_lower for indicator in location_indicators):
                # If user mentions cities/states directly
                if any(place in user_lower for place in ['shirpur', 'pune', 'mumbai', 'delhi', 'bangalore', 'maharashtra']):
                    self.candidate_info['location'] = user_input.strip()
                # Or if they use location keywords
                elif any(phrase in user_lower for phrase in ['from', 'live in', 'located in', 'based in']):
                    location_words = user_input.split()
                    for i, word in enumerate(location_words):
                        if word.lower() in ['from', 'in'] and i + 1 < len(location_words):
                            self.candidate_info['location'] = ' '.join(location_words[i+1:]).strip('.,!')
                            break
        
        # Extract tech stack - improved logic
        tech_keywords = ['python', 'java', 'javascript', 'react', 'node', 'django', 'flask', 'sql', 'mongodb', 'html', 'css', 'angular', 'vue', 'php', 'ruby', 'go', 'rust', 'c++', 'c#', 'swift', 'kotlin', 'tensorflow', 'pytorch', 'fastapi', 'streamlit', 'pandas', 'numpy', 'aws', 'git', 'github', 'linux', 'matlab', 'tailwind', 'scikit-learn', 'nltk', 'opencv', 'bash']
        mentioned_tech = [tech for tech in tech_keywords if tech in user_lower]
        
        # Also check for comprehensive tech stack descriptions
        if ('languages:' in user_lower or 'frameworks:' in user_lower or 'tools:' in user_lower) and not self.candidate_info.get('tech_stack'):
            self.candidate_info['tech_stack'] = user_input.strip()
        elif mentioned_tech and not self.candidate_info.get('tech_stack'):
            self.candidate_info['tech_stack'] = ', '.join(mentioned_tech)
    
    def format_summary(self):
        """Format candidate information summary"""
        if not self.candidate_info:
            return "No information collected yet."
        
        summary = ""
        for key, value in self.candidate_info.items():
            summary += f"**{key.title()}:** {value}\n"
        return summary

def main():
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
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: #000000 !important;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #1565c0 !important;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        color: #7b1fa2 !important;
    }
    .info-summary {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ff9800;
        margin: 1rem 0;
        color: #e65100 !important;
    }
    /* Fix chat input styling */
    .stChatInput > div > div > div > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    /* Fix main container text color */
    .stMarkdown {
        color: #000000 !important;
    }
    /* Ensure strong tags are visible */
    strong {
        color: inherit !important;
        font-weight: bold !important;
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
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = TalentScoutChatbot()
        st.session_state.messages = []
        st.session_state.conversation_ended = False
    
    chatbot = st.session_state.chatbot
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📋 Process Overview")
        st.markdown("""
        **Step 1:** Basic Information
        - Name, Contact Details
        - Experience & Position
        
        **Step 2:** Tech Stack Declaration  
        - Programming Languages
        - Frameworks & Tools
        
        **Step 3:** Technical Questions
        - Customized based on your skills
        - 3-4 relevant questions
        
        **Step 4:** Summary & Next Steps
        """)
        
        if chatbot.candidate_info:
            st.markdown("### 👤 Your Information")
            st.markdown(chatbot.format_summary())
        
        # Reset button
        if st.button("🔄 Start New Session"):
            st.session_state.chatbot = TalentScoutChatbot()
            st.session_state.messages = []
            st.session_state.conversation_ended = False
            st.rerun()
    
    # Main chat interface
    st.markdown("### 💬 Chat with AI Assistant")
    
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message bot-message"><strong>TalentScout AI:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    
    # Initial greeting
    if not st.session_state.messages and not st.session_state.conversation_ended:
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
    if not st.session_state.conversation_ended:
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Check for conversation end
            if any(word in user_input.lower() for word in ['bye', 'goodbye', 'exit', 'quit', 'thank you', 'thanks']):
                end_response = f"""Thank you for your time! Here's what happens next:

**📋 Your Information Summary:**
{chatbot.format_summary()}

**🔄 Next Steps:**
• Our technical team will review your responses
• You'll hear back from us within 2-3 business days  
• If selected, we'll schedule a detailed technical interview

**💼 TalentScout Team**
We appreciate your interest in joining our talent network!

*This conversation has ended. Feel free to start a new session anytime.*"""
                
                st.session_state.messages.append({"role": "assistant", "content": end_response})
                st.session_state.conversation_ended = True
                st.rerun()
            
            # Extract information from user input
            chatbot.extract_info(user_input)
            
            # Update conversation state based on collected info
            missing_info = chatbot.get_missing_info()
            if not missing_info and chatbot.conversation_state == "collecting_info":
                chatbot.conversation_state = "technical_questions"
            elif chatbot.conversation_state == "greeting":
                chatbot.conversation_state = "collecting_info"
            
            # Generate AI response
            response = chatbot.generate_response(user_input, st.session_state.messages)
            
            # Special handling for technical questions
            if chatbot.conversation_state == "technical_questions" and not missing_info:
                tech_stack = chatbot.candidate_info.get('tech_stack', 'general programming')
                tech_response = f"""Perfect! I have all your information. Now let's proceed with some technical questions based on your tech stack: **{tech_stack}**

**Technical Assessment Questions:**

1. **Problem Solving:** Describe how you would approach debugging a performance issue in a web application.

2. **Code Quality:** What are the key principles you follow when writing clean, maintainable code?

3. **Technology Specific:** Based on your experience with {tech_stack}, can you explain a challenging project you worked on and how you solved the technical difficulties?

4. **Best Practices:** How do you ensure code security and handle error management in your applications?

Please answer these questions thoughtfully. Take your time and provide detailed responses where possible.

Type 'done' when you've finished answering, or 'bye' to end the conversation."""
                
                response = tech_response
                chatbot.conversation_state = "technical_assessment"
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    else:
        st.markdown('<div class="info-summary">💼 <strong>Conversation Ended</strong><br>Thank you for using TalentScout! Click "Start New Session" to begin again.</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("🎯 **TalentScout** - Connecting top tech talent with amazing opportunities!")

if __name__ == "__main__":
    main()
