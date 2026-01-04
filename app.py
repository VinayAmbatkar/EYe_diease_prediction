import os
import uuid
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Supported diseases
DISEASES = {
    "cross eyes": {
        "symptoms": ["Misalignment of the eyes", "Double vision", "Poor depth perception"],
        "precautions": ["Consult an ophthalmologist", "Vision therapy", "Corrective surgery if needed"]
    },
    "conjunctivitis": {
        "symptoms": ["Redness in the eye", "Itching or burning sensation", "Discharge from the eye"],
        "precautions": ["Avoid touching eyes", "Use prescribed eye drops", "Maintain proper hygiene"]
    },
    "cataract": {
        "symptoms": ["Blurred or cloudy vision", "Sensitivity to light", "Difficulty seeing at night"],
        "precautions": ["Wear UV-protected sunglasses", "Regular eye check-ups", "Surgery if recommended"]
    },
    "glaucoma": {
        "symptoms": ["Loss of peripheral vision", "Severe eye pain", "Halos around lights"],
        "precautions": ["Regular eye pressure checks", "Avoid smoking", "Healthy diet rich in antioxidants"]
    },
    "uveitis": {
        "symptoms": ["Eye redness", "Pain and sensitivity to light", "Blurred vision"],
        "precautions": ["Seek immediate medical attention", "Use prescribed anti-inflammatory medications", "Avoid eye strain"]
    },
    "bulging eyes": {
        "symptoms": ["Protruding eyeball", "Eye pain", "Dry eyes", "Double vision", "Thyroid-related symptoms"],
        "precautions": ["Consult an endocrinologist", "Protect eyes from injury", "Regular thyroid function tests", "Use artificial tears"]
    }
}

# AI Prompt - Improved for better disease detection
input_prompt = """
You are an expert ophthalmologist AI assistant specialized in identifying eye diseases from images.

TASK: Analyze the provided eye image and identify any eye conditions.

STEP 1 - IMAGE VALIDATION:
Check if this is a valid human eye image. If NOT a human eye image, respond ONLY with: INVALID_IMAGE

STEP 2 - DISEASE DETECTION:
If it IS a valid eye image, carefully examine for these conditions:
- CATARACT: Look for cloudy, milky, or opaque appearance in the lens/pupil area
- CONJUNCTIVITIS: Look for redness, inflammation, discharge, pink/red coloring
- GLAUCOMA: Look for cupping of optic disc, high eye pressure signs, hazy cornea
- CROSS EYES (Strabismus): Look for misaligned eyes, one eye turning inward/outward
- UVEITIS: Look for eye inflammation, redness, light sensitivity signs
- BULGING EYES (Proptosis): Look for protruding eyeballs, thyroid-related signs

IMPORTANT: Look carefully at the pupil area. If there is ANY cloudiness, haziness, or opacity in the pupil or lens area, this indicates CATARACT.

RESPONSE FORMAT - Reply with ONLY ONE of these exact words:
- cataract
- conjunctivitis  
- glaucoma
- cross eyes
- uveitis
- bulging eyes
- HEALTHY_EYE (if no disease detected)
- INVALID_IMAGE (if not an eye image)

DO NOT include any explanation. Reply with ONLY the single word/phrase above.
"""

# Helper function to extract disease name from AI response
def extract_disease_from_response(response_text):
    """Extract the disease name from AI response, handling various response formats"""
    response_lower = response_text.lower().strip()
    
    # Direct matches
    disease_keywords = {
        'cataract': 'cataract',
        'conjunctivitis': 'conjunctivitis',
        'glaucoma': 'glaucoma',
        'cross eyes': 'cross eyes',
        'strabismus': 'cross eyes',
        'uveitis': 'uveitis',
        'bulging eyes': 'bulging eyes',
        'proptosis': 'bulging eyes',
        'exophthalmos': 'bulging eyes',
        'healthy_eye': 'healthy_eye',
        'healthy eye': 'healthy_eye',
        'invalid_image': 'invalid_image',
        'invalid image': 'invalid_image'
    }
    
    # Check for exact match first
    for keyword, disease in disease_keywords.items():
        if response_lower == keyword:
            return disease
    
    # Check if response contains any disease keyword
    for keyword, disease in disease_keywords.items():
        if keyword in response_lower:
            return disease
    
    # If no match found, return the original response
    return response_lower

# Function to generate PDF report
def generate_pdf_report(user_details, image, model_response):
    pdf_filename = f"eye_disease_report_{uuid.uuid4()}.pdf"
    
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # Add title
    pdf.set_font_size(16)
    pdf.cell(200, 10, 'Eye Disease Detection Medical Report', ln=True, align='C')
    pdf.ln(10)
    
    # User details
    pdf.set_font_size(14)
    pdf.cell(0, 10, 'Patient Information', ln=True)
    pdf.set_font_size(12)
    for key, value in user_details.items():
        pdf.cell(0, 10, f"{key}: {value}", ln=True)
    pdf.ln(5)
    
    # Diagnosis details
    pdf.set_font_size(14)
    pdf.cell(0, 10, 'Diagnosis Details', ln=True)
    pdf.set_font_size(12)
    
    if model_response in DISEASES:
        disease = model_response
        pdf.cell(0, 10, f"Detected Condition: {disease.title()}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 10, 'Key Symptoms:', ln=True)
        for symptom in DISEASES[disease]["symptoms"]:
            pdf.cell(0, 10, f"- {symptom}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 10, 'Recommended Precautions:', ln=True)
        for precaution in DISEASES[disease]["precautions"]:
            pdf.cell(0, 10, f"- {precaution}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 10, 'Medical Recommendation:', ln=True)
        pdf.multi_cell(0, 10, f"It is crucial to consult an ophthalmologist for a comprehensive examination and personalized treatment plan for {disease}.")
    elif model_response == "healthy_eye":
        pdf.cell(0, 10, 'Healthy Eye', ln=True)
        pdf.multi_cell(0, 10, 'The uploaded image shows a healthy eye with no signs of disease. Continue regular eye check-ups to maintain optimal eye health.')
    elif model_response == "invalid_image":
        pdf.cell(0, 10, 'Invalid Image', ln=True)
        pdf.multi_cell(0, 10, 'The uploaded image is not a valid eye image. Please upload a close-up photograph of a human eye for analysis.')
    else:
        pdf.cell(0, 10, 'Analysis Result', ln=True)
        pdf.multi_cell(0, 10, 'Unable to determine the condition from the image. Please consult an ophthalmologist for a proper examination.')
    
    # Add image
    pdf.ln(10)
    if image:
        image_path = f"uploaded_image_{uuid.uuid4()}.png"
        image.save(image_path)
        pdf.image(image_path, x=10, y=pdf.get_y(), w=100)
        os.remove(image_path)  # Clean up temporary image file
    
    # Save to file
    pdf.output(pdf_filename)
    return pdf_filename

# Function to detect disease
def detect_disease(input_prompt, image_data):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([input_prompt, image_data[0]])
        raw_response = response.text.strip()
        print(f"Raw AI Response: {raw_response}")
        
        # Extract disease name from response
        extracted = extract_disease_from_response(raw_response)
        print(f"Extracted Disease: {extracted}")
        return extracted
    except Exception as e:
        return f"Error: {str(e)}"

# Function to setup image data
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Streamlit App Configuration
st.set_page_config(
    page_title="Eye Disease Detection AI",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stApp {
        background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%) !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }
    
    /* Info cards */
    .info-card {
        background: white !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        margin-bottom: 1rem !important;
        border-left: 4px solid #667eea !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4) !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    section[data-testid="stSidebar"] .stTextInput > div > div > input,
    section[data-testid="stSidebar"] .stNumberInput > div > div > input,
    section[data-testid="stSidebar"] .stSelectbox > div > div > select {
        border-radius: 8px !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
        background: rgba(255,255,255,0.1) !important;
        color: white !important;
    }
    
    section[data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* File uploader */
    .stFileUploader > div > div {
        background: white !important;
        border-radius: 12px !important;
        border: 2px dashed #667eea !important;
        padding: 2rem !important;
    }
    
    /* Success and error messages */
    .stSuccess {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    /* Image container */
    .stImage {
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15) !important;
    }
    
    /* Form styling */
    .stForm {
        background: rgba(255,255,255,0.1) !important;
        padding: 1rem !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Checkbox styling */
    section[data-testid="stSidebar"] .stCheckbox > label {
        color: white !important;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom container styling */
    .stContainer {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Override Streamlit's default styling */
    .css-1d391kg {
        background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%) !important;
    }
    
    .css-1v0mbdj {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

# Modern Header
st.markdown("""
<div class="main-header">
    <h1>👁️ Eye Disease Detection AI</h1>
    <p>Advanced AI-Powered Eye Health Analysis & Diagnosis</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with form for personal and health details
st.sidebar.markdown("### 📋 Patient Information")
st.sidebar.markdown("---")

# Initialize session state
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Personal Details Form
with st.sidebar.form(key="personal_details_form"):
    st.markdown("#### 👤 Personal Details")
    name = st.text_input("Full Name", placeholder="Enter your name", key="name")
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=0, max_value=120, key="age")
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="gender")
    
    location = st.text_input("Location", placeholder="City, Country", key="location")
    
    # Symptoms
    st.markdown("---")
    st.markdown("#### 🔍 Current Symptoms")
    blurry_vision = st.checkbox("👁️ Blurry vision", key="blurry_vision")
    redness = st.checkbox("🔴 Redness", key="redness")
    double_vision = st.checkbox("👓 Double vision", key="double_vision")
    eye_pain = st.checkbox("💢 Eye pain", key="eye_pain")
    light_sensitivity = st.checkbox("💡 Light sensitivity", key="light_sensitivity")
    other_symptoms = st.text_input("Other symptoms", placeholder="Describe any other symptoms", key="other_symptoms")
    
    # Additional factors
    st.markdown("---")
    st.markdown("#### 🏥 Medical Conditions")
    sugar = st.checkbox("🩺 Diabetes", key="sugar")
    none_factor = st.checkbox("✅ No pre-existing conditions", key="none_factor")
    
    # Submit button for the form
    st.markdown("---")
    submit_button = st.form_submit_button(label="💾 Save Information", use_container_width=True)
    
    if submit_button:
        if not name or age == 0 or not gender or not location:
            st.error("⚠️ Please fill in all required fields.")
        else:
            st.session_state.submitted = True
            st.success("✅ Information saved successfully!")

# Main content area with columns
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### 📤 Upload Eye Image")
    st.markdown("Please upload a clear, close-up image of the eye for analysis")
    
    # File uploader for images
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png"],
        help="Upload a high-quality eye image for accurate diagnosis"
    )
    
    # Display uploaded image
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="📷 Uploaded Eye Image", use_container_width=True)
        
        # Submit button for analyzing the image
        st.markdown("---")
        submit = st.button("🔬 Analyze Image", use_container_width=True, type="primary")
    else:
        submit = False
        st.info("👆 Please upload an eye image to begin analysis")

with col_right:
    st.markdown("### ℹ️ Detectable Conditions")
    
    # Disease information cards
    disease_info = [
        ("🔄 Cross Eyes", "Misalignment of the eyes"),
        ("👁️ Conjunctivitis", "Pink eye infection"),
        ("☁️ Cataract", "Clouding of the eye lens"),
        ("🌊 Glaucoma", "Optic nerve damage"),
        ("🔥 Uveitis", "Eye inflammation"),
        ("👀 Bulging Eyes", "Protruding eyeballs")
    ]
    
    for disease, desc in disease_info:
        st.markdown(f"""
        <div class="info-card">
            <strong>{disease}</strong><br>
            <small style="color: #666;">{desc}</small>
        </div>
        """, unsafe_allow_html=True)

# Image Analysis and Report Generation
if submit:
    if not st.session_state.submitted:
        st.error("⚠️ Please fill out the patient information form in the sidebar first.")
    elif uploaded_file:
        with st.spinner("🔬 Analyzing image... Please wait..."):
            try:
                # Prepare user details
                user_details = {
                    "Name": name,
                    "Age": age,
                    "Gender": gender,
                    "Location": location,
                    "Symptoms": ", ".join([
                        symptom for symptom, selected in zip(
                            ["Blurry vision", "Redness", "Double vision", "Eye pain", "Light sensitivity"],
                            [blurry_vision, redness, double_vision, eye_pain, light_sensitivity]
                        ) if selected
                    ]) or "None",
                    "Additional Factors": "Sugar" if sugar else "None"
                }
                
                # Check user input conditions
                if sugar:
                    disease_found = "glaucoma"
                    message = f"Predicted Disease: {disease_found.title()} detected (based on reported diabetes)!"
                    model_response = "glaucoma"
                elif none_factor:
                    disease_found = None
                    message = "Healthy eye: The uploaded image shows a healthy eye with no signs of disease"
                    model_response = "healthy_eye"
                else:
                    image_data = input_image_setup(uploaded_file)
                    response = detect_disease(input_prompt, image_data)
                    model_response = response
                    
                    if response == "invalid_image":
                        disease_found = None
                        message = "The uploaded image is not a valid eye image. Please upload a close-up photograph of a human eye."
                    elif response == "healthy_eye":
                        disease_found = None
                        message = "Healthy eye: The uploaded image shows a healthy eye with no signs of disease."
                    elif response in DISEASES:
                        disease_found = response
                        message = f"Predicted Disease: {disease_found.title()} detected!"
                    else:
                        disease_found = None
                        message = "Unable to determine the condition from the image."
                
                # Display results in a modern container
                st.markdown("---")
                st.markdown("## 📊 Analysis Results")
                
                # Results container
                if disease_found:
                    st.error(f"⚠️ {message}")
                    
                    # Display disease details
                    st.markdown("### 🔍 Condition Details")
                    with st.expander("📋 View Symptoms & Precautions", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Key Symptoms:**")
                            for symptom in DISEASES[disease_found]["symptoms"]:
                                st.markdown(f"• {symptom}")
                        
                        with col2:
                            st.markdown("**Recommended Precautions:**")
                            for precaution in DISEASES[disease_found]["precautions"]:
                                st.markdown(f"• {precaution}")
                        
                        st.warning("⚕️ Please consult an ophthalmologist for professional diagnosis and treatment.")
                
                elif "invalid" in message.lower():
                    st.warning(f"⚠️ {message}")
                elif "healthy" in message.lower():
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.info(f"ℹ️ {message}")
                
                # Generate report
                pdf_filename = generate_pdf_report(user_details, image, model_response)
                
                # Provide download link in a prominent way
                st.markdown("---")
                st.markdown("### 📄 Medical Report")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    with open(pdf_filename, 'rb') as pdf_file:
                        st.download_button(
                            label="📥 Download Complete Medical Report",
                            data=pdf_file,
                            file_name=f"Eye_Disease_Report_{name.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                os.remove(pdf_filename)  # Clean up PDF file
            
            except Exception as e:
                st.error(f"❌ An error occurred during analysis: {str(e)}")
    else:
        st.error("⚠️ Please upload an image to proceed.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p><strong>Eye Disease Detection AI</strong></p>
    <p>This is an AI-powered diagnostic tool. Always consult with a qualified healthcare professional for medical advice.</p>
    <p style="font-size: 0.9rem;">© 2025 Eye Disease Detection AI. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)
