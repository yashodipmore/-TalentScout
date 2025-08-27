import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.title("🎯 TalentScout Test")
st.write("Testing basic Streamlit functionality...")

# Test API key
api_key = os.getenv("GROQ_API_KEY")
if api_key:
    st.success("✅ API Key loaded successfully!")
    st.write(f"API Key starts with: {api_key[:10]}...")
else:
    st.error("❌ API Key not found!")

# Test basic functionality
st.write("### Basic Test")
if st.button("Test Button"):
    st.balloons()
    st.success("Button works!")

# Test input
name = st.text_input("Enter your name:")
if name:
    st.write(f"Hello, {name}!")

st.write("### Environment Info")
st.write(f"Python version: {st.__version__}")
st.write("If you see this, Streamlit is working!")
