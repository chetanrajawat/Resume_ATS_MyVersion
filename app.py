from dotenv import load_dotenv
load_dotenv()
import base64
import streamlit as st
import os
import io
from PIL import Image 
import pdf2image
import google.generativeai as genai

# Configure the API key
genai.configure(api_key="AIzaSyBwAmIS9IZzJMTmGb9TnS_XbWrkFssdMyA")

def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts = [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Streamlit App
st.set_page_config(page_title="ATS Tracking System", layout="centered")
st.header("Resume ATS Tracking System")

# Job Description Input
input_text = st.text_area("Paste the complete Job Description:", 
                         key="input", 
                         height=200,
                         placeholder="Include all requirements, skills, qualifications...")

# Multi-file uploader
uploaded_files = st.file_uploader("Upload Resumes (PDF)", 
                                type=["pdf"], 
                                accept_multiple_files=True)

if uploaded_files and input_text:
    # Create tabs for each resume
    tabs = st.tabs([f"Resume {i+1}" for i in range(len(uploaded_files))])
    
    # Precision matching prompt
    match_prompt = """
    Calculate EXACT percentage match between this resume and job description using:

    SCORING METHOD:
    1. Extract ALL requirements from job description (skills, qualifications, experience)
    2. Check resume for each requirement (present/absent)
    3. match technical requirements in projects or in experience.
    4. match the project experience more than 2 years .
    5. Calculate match percentage using:
       - Must-have requirements: 25% weight
       - Technical skills: 50% weight
       - Experience years/roles: 25% weight

    OUTPUT FORMAT:
    **Match Percentage**: XX% (exact number)
    
    **Key Matches**:
    - [✓] Requirement 1 (evidence from resume)
    - [✓] Requirement 2 (evidence from resume)
    
    **Key Misses**:
    - [✗] Missing Requirement 1
    - [✗] Missing Requirement 2
    
    **Suggestions**:
    - Add [specific missing skill]
    - Highlight [specific experience] more clearly
    """

    for i, uploaded_file in enumerate(uploaded_files):
        with tabs[i]:
            try:
                pdf_content = input_pdf_setup(uploaded_file)
                with st.spinner(f"Calculating match for Resume {i+1}..."):
                    response = get_gemini_response(match_prompt, pdf_content, input_text)
                    
                    # Extract and display the percentage prominently
                    if "**Match Percentage**: " in response:
                        percentage = response.split("**Match Percentage**: ")[1].split("%")[0]
                        st.metric(label="Precision Match Score", 
                                 value=f"{percentage}%", 
                                 delta="vs JD Requirements")
                    
                    st.divider()
                    st.subheader("Detailed Breakdown")
                    st.markdown(response)
                    
            except Exception as e:
                st.error(f"Error processing Resume {i+1}: {str(e)}")

elif uploaded_files or input_text:
    st.warning("Please provide both Job Description and Resume(s)")

# Accuracy tips
with st.expander("How to improve your match score"):
    st.write("""
    1. Mirror JD keywords in your resume exactly
    2. Include all must-have requirements prominently
    3. Quantify experience (years, projects, metrics)
    4. Match job title terminology
    5. List Technical skills using same wording as JD
    """)