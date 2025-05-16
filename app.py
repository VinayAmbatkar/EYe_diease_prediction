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

# Updated prompt
input_prompt = """
You are an expert in identifying eye diseases. 
First, determine if the input image is a valid eye image. A valid eye image is a close-up photograph of a human eye, with the eye prominently centered and filling the frame. The image should show detailed features such as the iris, pupil, sclera, eyelids, and eyebrows. The iris should display color variations and a reflective highlight near the pupil. The pupil should be clearly visible and moderately dilated. The sclera should be clear with a slight pinkish hue near the edges. The upper eyelid should be partially visible with a smooth skin texture and natural crease, and the lower eyelid should be faintly discernible. Thick, dark eyebrows should be prominent above the eye, with individual hairs visible. The skin around the eye should have a light complexion with a glossy finish, showing fine lines and pores. The image should be well-lit with soft shadows enhancing the depth of the eye and surrounding features. 

If the image is not a valid eye image, respond with "INVALID_IMAGE".

If the image is a valid eye image, check for the following conditions: cross eyes, conjunctivitis, cataract, glaucoma, uveitis, or bulging eyes. For bulging eyes, look for protrusion of one or both eyeballs, potential thyroid-related signs, and surrounding tissue swelling.

If one of these conditions is detected, respond with the name of the condition (e.g., "cataract").

If no condition is detected, respond with "HEALTHY_EYE".
"""

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
        return response.text.strip().lower()
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
st.set_page_config(page_title="Eye Disease Detection", page_icon="🦠")
st.title("🩺 Eye Disease Detection App")

# Sidebar with form for personal and health details
st.sidebar.header("📝 Personal and Health Details")

# Initialize session state
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Personal Details Form
with st.sidebar.form(key="personal_details_form"):
    name = st.text_input("Name:", key="name")
    age = st.number_input("Age:", min_value=0, max_value=90, key="age")
    gender = st.selectbox("Gender:", ["Male", "Female", "Other"], key="gender")
    location = st.text_input("Location:", key="location")
    
    # Symptoms
    st.subheader("Current Eye Symptoms")
    blurry_vision = st.checkbox("Blurry vision", key="blurry_vision")
    redness = st.checkbox("Redness", key="redness")
    double_vision = st.checkbox("Double vision", key="double_vision")
    eye_pain = st.checkbox("Eye pain", key="eye_pain")
    light_sensitivity = st.checkbox("Light sensitivity", key="light_sensitivity")
    other_symptoms = st.text_input("Other (if any):", key="other_symptoms")
    
    # Additional factors
    st.subheader("Additional Factors")
    sugar = st.checkbox("Sugar (Diabetes)", key="sugar")
    none_factor = st.checkbox("None", key="none_factor")
    
    # Submit button for the form
    submit_button = st.form_submit_button(label="Submit")
    
    if submit_button:
        if not name or age == 0 or not gender or not location:
            st.error("All fields are required. Please fill in all the details.")
        else:
            st.session_state.submitted = True
            st.success("Form submitted successfully!")

# File uploader for images
uploaded_file = st.file_uploader("Upload an eye image...", type=["jpg", "jpeg", "png"])

# Display uploaded image
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)

# Submit button for analyzing the image
submit = st.button("Analyze Image")

# Image Analysis and Report Generation
if submit:
    if not st.session_state.submitted:
        st.error("Please fill out the personal details form first.")
    elif uploaded_file:
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
            
            # Generate report
            pdf_filename = generate_pdf_report(user_details, image, model_response)
            
            # Provide download link
            with open(pdf_filename, 'rb') as pdf_file:
                st.download_button(
                    label="Download Report",
                    data=pdf_file,
                    file_name="Eye_Disease_Report.pdf",
                    mime="application/pdf"
                )
            os.remove(pdf_filename)  # Clean up PDF file
            
            # Display message
            if "error" in message.lower() or "unable" in message.lower():
                st.error(message)
            else:
                st.success(message)
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please upload an image to proceed.")
