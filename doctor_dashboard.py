# doctor_dashboard.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase (Only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("nursebot.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def doctor_dashboard():
    st.title("🏥 Doctor Dashboard")

    # Reference to the doctor document
    doctor_doc_ref = db.collection("DOCTOR").document("1")  # Adjust the document path as needed

    # Fetch data from Firestore
    doc = doctor_doc_ref.get()
    data = doc.to_dict() if doc.exists else {}

    qn_list = data.get("qn", [])
    ans_dict = data.get("ans", {})

    # ✅ Fix: Ensure ans_dict is always a dictionary
    if not isinstance(ans_dict, dict):
        ans_dict = {}

    # Separate Answered & Unanswered Questions
    answered_qs = {q: ans_dict[q] for q in qn_list if q in ans_dict}
    unanswered_qs = [q for q in qn_list if q not in ans_dict]

    # Display Unanswered Questions with Input Box
    if unanswered_qs:
        st.subheader("📌 Unanswered Questions")
        for q in unanswered_qs:
            st.write(f"**Q:** {q}")
            answer = st.text_input(f"Enter answer:", key=q)
            if st.button(f"Submit Answer", key=f"btn_{q}"):
                if answer.strip():
                    doctor_doc_ref.set({
                        "ans": {**ans_dict, q: answer}  # ✅ Now always a dictionary
                    }, merge=True)
                    st.success("Answer saved successfully!")
                    st.rerun()
                else:
                    st.warning("Please enter a valid answer.")
    else:
        st.write("✅ No pending questions.")

    # Display Answered Questions without Input Fields
    if answered_qs:
        st.subheader("✅ Answered Questions")
        for q, a in answered_qs.items():
            st.write(f"**Q:** {q}")
            st.write(f"**A:** {a}")


# Call the doctor dashboard function if this file is run directly
if __name__ == "__main__":
    doctor_dashboard()