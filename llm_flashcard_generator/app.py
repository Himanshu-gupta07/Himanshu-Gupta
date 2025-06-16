import streamlit as st
from groq import Groq
import requests
import PyPDF2
import io
import csv
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 🔑 Set your Groq API key here (temporary for testing)
GROQ_API_KEY="xai-xCsrWVncJXLtPbTDTuqe1Q6U63t6reRACb9Wu2wXr5ViyuJIvEWpx4MMFsGfgeEGaPqjTQWCuLtmq56l"  # Replace this with your actual key from https://console.groq.com

class Website:
    def __init__(self):
        self.system_message = "You are a helpful assistant"
        # Use the direct API key for now
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "mixtral-8x7b-32768"  # Using a supported Groq model

    def generate_flashcards(self, content, subject=None):
        prompt = f'''
You are a helpful assistant that generates question-answer flashcards from educational content.

Subject: {subject or "General"}

Content:
\"\"\"
{content}
\"\"\"

Generate 10-15 flashcards in the format:
Q: ...
A: ...
Group under topics if possible.
'''
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

# Initialize the website instance
website = Website()

# 📄 Extract text from PDF
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# 🧹 Parse Q&A format from LLM output
def parse_flashcards(raw_output):
    lines = raw_output.strip().split("\n")
    flashcards = []
    question, answer = "", ""
    for line in lines:
        if line.startswith("Q:"):
            question = line[2:].strip()
        elif line.startswith("A:"):
            answer = line[2:].strip()
            if question and answer:
                flashcards.append((question, answer))
                question, answer = "", ""
    return flashcards

# 💾 Convert flashcards to CSV
def download_csv(data):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", "Answer"])
    writer.writerows(data)
    return output.getvalue()

# 🌐 Streamlit UI
st.set_page_config(page_title="LLM Flashcard Generator", page_icon="🧠")
st.title("📚 LLM-Powered Flashcard Generator")
st.markdown("Generate smart question-answer flashcards from your notes or PDFs.")

subject = st.text_input("Optional Subject (e.g., Biology, History, CS)")
uploaded_file = st.file_uploader("Upload a .pdf or .txt file", type=["pdf", "txt"])
pasted_text = st.text_area("Or paste text here", height=200)

if st.button("🚀 Generate Flashcards"):
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            input_text = extract_text_from_pdf(uploaded_file)
        else:
            input_text = uploaded_file.read().decode("utf-8")
    elif pasted_text.strip():
        input_text = pasted_text
    else:
        st.warning("Please upload a file or paste content.")
        st.stop()

    try:
        with st.spinner("Generating flashcards..."):
            raw_output = website.generate_flashcards(input_text, subject)
            flashcards = parse_flashcards(raw_output)

        st.success("✅ Flashcards generated!")
        for i, (q, a) in enumerate(flashcards, 1):
            st.markdown(f"**Q{i}:** {q}\n\n**A:** {a}\n")

        csv_data = download_csv(flashcards)
        st.download_button("📥 Download CSV", data=csv_data, file_name="flashcards.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
