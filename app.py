import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
import io
from doctor_dashboard  import doctor_dashboard
# Load Firebase credentials
load_dotenv()
firebase_credentials_path = os.getenv('VARIABLE')

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Import criteria and explanations from original script
inclusion_criteria = [
    "Is the subject aged between 18 and 75 years at Screening?",
    "Has informed consent been obtained?",
    "Is the infection (HABP/VABP ± ccBSI) caused by a suspected or documented carbapenem-resistant Gram-negative pathogen?",
    "Does the subject have CrCL (>30 mL/min)?",

    # HABP/VABP Specific Inclusion Criteria
    "Does the subject have hospital-acquired or ventilator-associated bacterial pneumonia with or without concurrent bloodstream infection?",
    "Does the subject have a new onset or worsening of pulmonary symptoms, such as cough, dyspnea, tachypnea (e.g., respiratory rate > 25 breaths per minute), or expectorated sputum production?",
    "Is there a need for mechanical ventilation or an increase in ventilator support to enhance oxygenation?",
    "Has the subject's partial pressure of oxygen dropped below 60 mmHg while breathing room air, or has the PaO2/FiO2 ratio worsened?",
    "Is there a new onset or increase in suctioned respiratory secretions?",
    "Does the subject have documented fever (e.g., core body temperature ≥ 38°C) or hypothermia (e.g., core body temperature ≤ 35°C)?",
    "Does the subject have leukocytosis with a WBC count ≥ 10,000 cells/mm³, leukopenia with a WBC count ≤ 4,500 cells/mm³, or more than 15% immature neutrophils (bands) on a peripheral blood smear?",

    # cIAI Specific Inclusion Criteria
    "Does the subject meet specific criteria for cIAI inclusion?",
    "Does the subject have cholecystitis with gangrenous rupture or infection progression beyond the gallbladder wall?",
    "Does the subject have diverticular disease with perforation or abscess?",
    "Does the subject have appendiceal perforation or a peri-appendiceal abscess?",
    "Does the subject have acute gastric or duodenal perforation (if operated on more than 24 hours after perforation)?",
    "Does the subject have traumatic perforation of the intestines (if operated on more than 12 hours after perforation)?",
    "Does the subject have secondary peritonitis (excluding spontaneous peritonitis associated with cirrhosis and chronic ascites)?",
    "Does the subject have an intra-abdominal abscess with evidence of intraperitoneal involvement?",

    # ccBSI Specific Inclusion Criteria
    "Does the subject have one or more positive blood cultures identifying a carbapenem-resistant Gram-negative pathogen that is consistent with the subject's clinical condition?",
    "Does the subject have signs or symptoms associated with bacteremia?",

    # cUTI or AP Specific Inclusion Criteria
    "Is there a confirmed cUTI or AP with or without concurrent bloodstream infection?",
    "Has the subject had an indwelling urinary catheter or recent instrumentation of the urinary tract (within 14 days prior to Screening)?",
    "Does the subject have urinary retention with 100 mL or more of residual urine after voiding (neurogenic bladder)?",
    "Does the subject have obstructive uropathy (e.g., nephrolithiasis or fibrosis)?",
    "Does the subject have azotemia caused by intrinsic renal disease (BUN and creatinine values greater than normal clinical laboratory values)?",
    "Does the subject present with at least two signs or symptoms: chills, rigors, or warmth associated with fever (temperature ≥ 38°C); flank pain or suprapubic/pelvic pain; nausea or vomiting; dysuria, urinary frequency, or urgency; or costovertebral angle tenderness on physical examination?",
    "Does the subject's urinalysis show evidence of pyuria, demonstrated by either a positive dipstick analysis for leukocyte esterase or ≥ 10 WBCs/µL in unspun urine, or ≥ 10 WBCs/high-power field in spun urine?",
    "Did the subject have a positive urine culture within 48 hours before WCK 5222 treatment initiation, showing ≥ 10⁵ CFU/mL of a carbapenem-resistant Gram-negative uropathogen?",
    "Is the subject receiving antibiotic prophylaxis for cUTI but presenting with signs and symptoms consistent with an active new cUTI?"
]

exclusion_criteria = [
    "Does the subject have any hypersensitivity or allergic reactions to B-lactam antibiotics?",
    "Does the subject have any pre-existing neurological disorders?",
    "Has the subject received any prior treatment with antibiotics effective against carbapenem-resistant Gram-negative bacteria?",
    "Does the subject have severe sepsis or septic shock requiring high-level vasopressors?",
    "Does the subject have a Cr <30 mL/min at screening?",
    "Is there a history of chronic kidney disease?",
    "Are there any co-infections with specific pathogens (e.g., Gram-positive bacteria, Aspergillosis)?",
    "Is there a central nervous system infection present?",
    "Does the subject have infections requiring extended antibiotic treatment (e.g., bone infections)?",
    "Does the subject have cystic fibrosis or severe bronchiectasis?",
    "Does the subject have severe neutropenia?",
    "Has the subject tested positive for pregnancy or is lactating?",
    "Does the subject have a Sequential Organ Failure Assessment (SOFA) score greater than 6?",
    "Is there any condition that might compromise safety or data quality according to the investigator?",
    "Has the subject received any investigational drug or device within 30 days prior to entry?",
    "Has the subject been previously enrolled in this study or received WCK 5222?",
    "Is the subject receiving dialysis, continuous renal replacement therapy, or ECMO?",
    "Does the subject have myasthenia gravis or any other neuromuscular disorder?",
    "Does the subject have severe liver disease?"
]


def handle_response(question, nurse_id):
    response = st.radio(f"{question}", ["Yes", "No", "Not Sure"], key=f"response_{question}")
    return "Response recorded.", response.lower()

def display_chat():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm here to help you with the eligibility criteria assessment. Feel free to ask any questions."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = "This is a placeholder response. The actual question-answering logic will be implemented later."
        st.session_state.messages.append({"role": "assistant", "content": response})
def run_clinical_test():
    # Create two columns for split layout
    col1, col2 = st.columns([0.6, 0.4])
    
    with col1:
        st.title("Eligibility Criteria Assessment")
        
        nurse_id = st.session_state.nurse_id
        subject_name = st.text_input("Enter the name of the subject:")
        patient_id = st.text_input("Enter the ID of the patient:")

        patient_data = {
            'nurse_id': nurse_id,
            'patient_id': patient_id,
            'subject_name': subject_name,
            'responses': {},
            'conclusion': '',
        }

        # Initialize flags
        unconcluded_flag = False
        exclusion_flag = False

        st.subheader("Inclusion Criteria")
        for idx, question in enumerate(inclusion_criteria, start=1):
            print("\n" + question)
            result, response = handle_response(question, nurse_id)
            print(result,response)
            patient_data['responses'][f'inclusion_{idx}'] = response  # Save response in the dictionary
            if response == "not sure":
                unconcluded_flag = True
        
        st.subheader("Exclusion Criteria")
        for idx, question in enumerate(exclusion_criteria, start=len(inclusion_criteria) + 1):
            print("\n" + question)
            result, response = handle_response(question, nurse_id)
            print(result,response)
            patient_data['responses'][f'exclusion_{idx}'] = response  # Save response in the dictionary
            if response == "not sure":
                unconcluded_flag = True
            if response == "yes":
                exclusion_flag = True
                #exclusion_reasons.append(question)

        if st.button("Submit Patient Data"):
            if unconcluded_flag:
                patient_data['conclusion'] = "Unconcluded"
            elif exclusion_flag:
                patient_data['conclusion'] = "Excluded"
            else:
                patient_data['conclusion'] = "Eligible"

            # Store in Firestore
            patients_ref = db.collection('PATIENTS')
            patients_ref.document(patient_id).set(patient_data)
            
            st.success("Patient data has been stored successfully!")
            st.write(f"Conclusion: {patient_data['conclusion']}")

    with col2:
        st.title("Criteria Assistant")
        display_chat()


def download_report(patient_id, nurse_id):
    try:
        # Query patient data based on patient_id and nurse_id
        patient_ref = db.collection('PATIENTS').where('patient_id', '==', patient_id).where('nurse_id', '==', nurse_id)
        patient_data = patient_ref.stream()  # This returns a generator

        # If the query returns results
        found_patient = False
        for doc in patient_data:
            found_patient = True
            patient_info = doc.to_dict()
            conclusion = patient_info.get('conclusion', '')

            # Check if the patient's conclusion is 'Unconcluded'
            if conclusion == "Unconcluded":
                st.warning("Cannot generate report for unconcluded patient.")
                break  # Exit the loop once warning is shown

            # Otherwise, generate the report PDF
            pdf_bytes = generate_pdf(patient_info, nurse_id, patient_id)

            # Provide the download button for the generated PDF
            st.download_button(
                label=f"Download Report for Patient {patient_id}",
                data=pdf_bytes,
                file_name=f"patient_{patient_id}_report.pdf",
                mime="application/pdf"
            )
        
        #if not found_patient: -->this will give other nurse_id records as not found!! so 
            #st.error(f"Patient with ID {patient_id} not found.") removed it!!!
    
    except Exception as e:
        st.error(f"Error generating PDF: {e}")

def generate_pdf(patient_data, nurse_id, patient_id):
    # Create PDF in memory
    pdf_buffer = io.BytesIO()

    try:
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 14)

        # Creating styles for alignment
        styles = getSampleStyleSheet()
        style_normal = styles["Normal"]
        style_normal.fontName = "Helvetica"
        style_normal.fontSize = 14

        # Adding content to the PDF using Paragraph for better alignment
        c.drawString(100, height - 50, f"Patient Report for ID: {patient_id}")
        c.drawString(100, height - 70, f"Nurse ID: {nurse_id}")
        c.drawString(100, height - 90, f"Name: {patient_data.get('subject_name', 'N/A')}")
        c.drawString(100, height - 110, f"Patient ID: {patient_id}")

        conclusion = patient_data.get('conclusion', '')
        
        # List of exclusion questions mapped to their IDs in Firestore
        exclusion_questions = {
            "exclusion_31": "Does the subject have any hypersensitivity or allergic reactions to B-lactam antibiotics?",
            "exclusion_32": "Does the subject have any pre-existing neurological disorders?",
            "exclusion_33": "Has the subject received any prior treatment with antibiotics effective against carbapenem-resistant Gram-negative bacteria?",
            "exclusion_34": "Does the subject have severe sepsis or septic shock requiring high-level vasopressors?",
            "exclusion_35": "Does the subject have a Cr <30 mL/min at screening?",
            "exclusion_36": "Is there a history of chronic kidney disease?",
            "exclusion_37": "Are there any co-infections with specific pathogens (e.g., Gram-positive bacteria, Aspergillosis)?",
            "exclusion_38": "Is there a central nervous system infection present?",
            "exclusion_39": "Does the subject have infections requiring extended antibiotic treatment (e.g., bone infections)?",
            "exclusion_40": "Does the subject have cystic fibrosis or severe bronchiectasis?",
            "exclusion_41": "Does the subject have severe neutropenia?",
            "exclusion_42": "Has the subject tested positive for pregnancy or is lactating?",
            "exclusion_43": "Does the subject have a Sequential Organ Failure Assessment (SOFA) score greater than 6?",
            "exclusion_44": "Is there any condition that might compromise safety or data quality according to the investigator?",
            "exclusion_45": "Has the subject received any investigational drug or device within 30 days prior to entry?",
            "exclusion_46": "Has the subject been previously enrolled in this study or received WCK 5222?",
            "exclusion_47": "Is the subject receiving dialysis, continuous renal replacement therapy, or ECMO?",
            "exclusion_48": "Does the subject have myasthenia gravis or any other neuromuscular disorder?",
            "exclusion_49": "Does the subject have severe liver disease?"
        }

        # Check if the patient is excluded
        if conclusion == "Excluded":
            exclusion_criteria_violations = []
            
            # Get the responses from the 'responses' field
            responses = patient_data.get('responses', {})

            # Check the responses for each exclusion question and add to the list if 'yes'
            for exclusion_key, exclusion_question in exclusion_questions.items():
                response = responses.get(exclusion_key, "").lower()
                if response == "yes":
                    exclusion_criteria_violations.append(f"Question: {exclusion_question}")

            # If there are any violations, add them to the PDF
            if exclusion_criteria_violations:
                c.drawString(100, height - 140, "Exclusion Criteria Violations:")
                y_position = height - 160

                # Using Paragraph for better text wrapping
                for violation in exclusion_criteria_violations:
                    para = Paragraph(violation, style_normal)
                    para_width = width - 200  # Set max width to fit the page
                    para_height = para.wrap(para_width, 100)[1]  # Wrap the text
                    para.drawOn(c, 100, y_position - para_height)
                    y_position -= (para_height + 10)  # Adjust y-position after each paragraph

        elif conclusion == "Eligible":
            para = Paragraph("Patient is eligible.", style_normal)
            para_width = width - 200
            para_height = para.wrap(para_width, 100)[1]
            para.drawOn(c, 100, height - 140 - para_height)

        # Save the PDF to buffer
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        raise

def download_reports():
    st.title("Patient Reports")
    
    # Retrieve patient data
    patients_ref = db.collection('PATIENTS')
    patients = patients_ref.stream()

    patient_data = []
    for patient in patients:
        data = patient.to_dict()
        patient_data.append({
            'Patient ID': data.get('patient_id', 'N/A'),
            'Subject Name': data.get('subject_name', 'N/A'),
            'Conclusion': data.get('conclusion', 'N/A'),
            'Download': data.get('patient_id', 'N/A')
        })

    df = pd.DataFrame(patient_data)
    st.dataframe(df)

    # Add download buttons for each patient
    for patient_id in df['Patient ID']:
        nurse_id = st.session_state.nurse_id
        download_report(patient_id, nurse_id)
def display_faq_and_queries():
    st.title("📚 FAQ and Raised Queries")

    # Fetch FAQs from the DOCTOR collection
    doctor_doc_ref = db.collection("DOCTOR").document("1")  # Adjust the document path as needed
    doctor_data = doctor_doc_ref.get()  # Use get() to retrieve the document

    answered_qs = []
    raised_qs = []

    # Create a map to store answers for easy lookup
    answers_map = {}

    if doctor_data.exists:
        data = doctor_data.to_dict()
        questions = data.get("qn", [])  # Assuming 'qn' is a list of questions
        answers = data.get("ans", {})  # Assuming 'ans' is a map of question-answer pairs

        # Populate the answers map
        for question in questions:
            if question in answers:  # Check if the question has an answer
                answered_qs.append((question, answers[question]))  # Append as a tuple

        # Identify raised questions (those that are in questions but not in answers)
        for question in questions:
            if question not in answers:
                raised_qs.append(question)

    # Display Answered Questions
    if answered_qs:
        st.subheader("✅ Answered Questions")
        for question, answer in answered_qs:
            st.write(f"**Q:** {question}")
            st.write(f"**A:** {answer}")
    else:
        st.write("No answered questions available.")

    # Display Raised Questions
    if raised_qs:
        st.subheader("📌 Raised Questions")
        for question in raised_qs:
            st.write(f"**Q:** {question}")
    else:
        st.write("No raised questions available.")
def main():
    st.set_page_config(page_title="Nurse Management App", page_icon="🏥", layout="wide")

    # Login Page
    if 'logged_in' not in st.session_state:
        st.title("Nurse Login")
        nurse_id = st.text_input("Enter Nurse ID")
        
        if st.button("Login"):
            # Check nurse ID in Firestore
            nurse_ref = db.collection('NURSE').document('nurse_ids')
            nurse_data = nurse_ref.get()

            if nurse_data.exists:
                nurse_data = nurse_data.to_dict()
                if nurse_id.strip() in nurse_data.get('nid', []):
                    st.session_state.logged_in = True
                    st.session_state.nurse_id = nurse_id.strip()  # Initialize nurse_id
                    st.rerun()
                else:
                    st.error("Invalid Nurse ID")
            else:
                st.error("Nurse data not found.")

            # Check if the entered nurse ID corresponds to a doctor
            doctor_ref = db.collection("DOC").document("ID")  
            doctor_data = doctor_ref.get()

            if nurse_id.strip()=='1004':
                st.session_state.logged_in = True
                st.session_state.nurse_id = nurse_id.strip()  # Initialize nurse_id
                st.session_state.is_doctor = True  # Set a flag for doctor
                st.rerun()
            else:
                st.error("Invalid Doctor ID or not a doctor.")

    # Main App
    if st.session_state.get('logged_in'):
        st.sidebar.title(f"Welcome, Nurse {st.session_state.nurse_id}")

        # Check if the logged-in user is a doctor
        if st.session_state.get('is_doctor', False):  # Check if the user is a doctor
            from doctor_dashboard import doctor_dashboard  # Import the doctor dashboard function
            doctor_dashboard()  # Call the doctor dashboard function
        else:
            # Existing nurse dashboard logic
            app_mode = st.sidebar.radio("Choose an option", 
                                         ["Clinical Test", "Download Reports","FAQ and Raised Queries"])
            
            if app_mode == "Clinical Test":
                run_clinical_test()  # Your existing function for clinical tests
            elif app_mode == "Download Reports":
                download_reports()  # Your existing function for downloading reports
            elif app_mode == "FAQ and Raised Queries":
                display_faq_and_queries()

            if st.sidebar.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.is_doctor = False  # Reset doctor flag
                st.rerun()
            
if __name__ == "__main__":
    main()
       