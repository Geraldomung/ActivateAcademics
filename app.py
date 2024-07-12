import streamlit as st
from huggingface_hub import InferenceClient
from requests.exceptions import RequestException
import datetime
import json
import pdfplumber
import io

class StudentLearningAssistant:
    def __init__(self):
        self.history = []
        self.mistral_client = self.get_inference_client()

    @staticmethod
    @st.cache_resource
    def get_inference_client():
        return InferenceClient("mistralai/Mistral-7B-Instruct-v0.2")

    def generate_mistral_response(self, prompt, max_new_tokens=500):
        try:
            response = self.mistral_client.text_generation(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.0,
                do_sample=True,
                seed=42,
            )
            return response
        except RequestException as e:
            return f"Error: {str(e)}"

    def answer_question(self, question, context):
        prompt = f"""Given the following context, please answer the question:

Context:
{context}

Question: {question}

Please provide a concise and accurate answer based solely on the information given in the context."""

        return self.generate_mistral_response(prompt)

    def summarize_text(self, text):
        prompt = f"""Please summarize the following text in about 3-5 sentences:

{text}

Summary:"""

        return self.generate_mistral_response(prompt)

    def generate_quiz(self, context):
        prompt = f"""Generate a quiz with 6 multiple-choice questions based on the following context:

{context}

For each question, provide:
1. The question
2. Four answer choices (A, B, C, D)
3. The correct answer
4. A brief explanation

Format each question as follows:
Question: [question text]
A) [choice A]
B) [choice B]
C) [choice C]
D) [choice D]
Answer: [correct letter]
Explanation: [brief explanation]
"""

        return self.generate_mistral_response(prompt, max_new_tokens=1000)

    def explain_concept(self, concept):
        prompt = f"""Provide a detailed explanation of the concept '{concept}' in simple terms. 
Your explanation should be at least 100 words long and cover the following:
1. Definition of the concept
2. Key aspects or components
3. Real-world examples or applications
4. Why it's important or relevant

Concept: {concept}"""

        return self.generate_mistral_response(prompt)

    def add_to_history(self, item):
        item['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append(item)

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []

def load_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Streamlit App
st.set_page_config(page_title="Activate Academics", page_icon="📚", layout="wide")

# Initialize session state
if 'assistant' not in st.session_state:
    st.session_state.assistant = StudentLearningAssistant()
if 'context' not in st.session_state:
    st.session_state.context = ""

# Sidebar
st.sidebar.title("Activate Academics")
st.sidebar.caption("Your AI-powered learning companion")
page = st.sidebar.selectbox("Select a learning tool:", ["Study Assistant", "Summary Generator", "Quiz Creator", "Concept Explainer"])

if st.sidebar.button("Clear History"):
    st.session_state.assistant.clear_history()
    st.sidebar.success("History cleared!")

# Main content
if page == "Study Assistant":
    st.title("📚 AI Study Assistant")
    st.caption("Ask questions about your study material")

    input_method = st.radio("Choose input method:", ["Text", "PDF"])

    if input_method == "Text":
        st.session_state.context = st.text_area("Enter your study material here:", value=st.session_state.context, height=200)
    else:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        if uploaded_file:
            st.session_state.context = load_pdf(uploaded_file)
            st.success("PDF uploaded successfully!")

    st.write("Current context length:", len(st.session_state.context))

    question = st.text_input("What would you like to know about your study material?")

    if st.button("Ask"):
        if not st.session_state.context or not question:
            st.warning("Please provide both study material and a question.")
        else:
            answer = st.session_state.assistant.answer_question(question, st.session_state.context)
            st.session_state.assistant.add_to_history({'type': 'qa', 'question': question, 'answer': answer})
            st.success(f"Answer: {answer}")

elif page == "Summary Generator":
    st.title("📝 Summary Generator")
    st.caption("Create concise summaries of your study material")

    input_method = st.radio("Choose input method:", ["Text", "PDF"])

    if input_method == "Text":
        text_to_summarize = st.text_area("Enter the text you want to summarize:", height=300)
    else:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        if uploaded_file:
            text_to_summarize = load_pdf(uploaded_file)
            st.success("PDF uploaded successfully!")
        else:
            text_to_summarize = ""

    if st.button("Generate Summary"):
        if not text_to_summarize:
            st.warning("Please enter some text or upload a PDF to summarize.")
        else:
            summary = st.session_state.assistant.summarize_text(text_to_summarize)
            st.session_state.assistant.add_to_history({'type': 'summary', 'original': text_to_summarize, 'summary': summary})
            st.success("Summary:")
            st.write(summary)

elif page == "Quiz Creator":
    st.title("🧠 Quiz Creator")
    st.caption("Generate quizzes from your study material")

    input_method = st.radio("Choose input method:", ["Text", "PDF"])

    if input_method == "Text":
        quiz_context = st.text_area("Enter the material you want to create a quiz from:", height=300)
    else:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        if uploaded_file:
            quiz_context = load_pdf(uploaded_file)
            st.success("PDF uploaded successfully!")
        else:
            quiz_context = ""

    if st.button("Generate Quiz"):
        if not quiz_context:
            st.warning("Please enter some material or upload a PDF to create a quiz from.")
        else:
            quiz = st.session_state.assistant.generate_quiz(quiz_context)
            st.session_state.assistant.add_to_history({'type': 'quiz', 'context': quiz_context, 'quiz': quiz})
            st.success("Generated Quiz:")
            st.write(quiz)

elif page == "Concept Explainer":
    st.title("💡 Concept Explainer")
    st.caption("Get detailed explanations for complex concepts")

    concept = st.text_input("Enter a concept you want explained:")

    if st.button("Explain Concept"):
        if not concept:
            st.warning("Please enter a concept to explain.")
        else:
            explanation = st.session_state.assistant.explain_concept(concept)
            st.session_state.assistant.add_to_history({'type': 'explanation', 'concept': concept, 'explanation': explanation})
            st.success(f"Explanation of '{concept}':")
            st.write(explanation)

# Display history
st.sidebar.title("Study History")
history = st.session_state.assistant.get_history()
for item in history:
    if item['type'] == 'qa':
        st.sidebar.info(f"Q: {item['question']}")
        st.sidebar.success(f"A: {item['answer']}")
    elif item['type'] == 'summary':
        st.sidebar.info("Summary generated")
    elif item['type'] == 'quiz':
        st.sidebar.info("Quiz generated")
    elif item['type'] == 'explanation':
        st.sidebar.info(f"Concept explained: {item['concept']}")
    st.sidebar.caption(f"Time: {item['timestamp']}")
    st.sidebar.markdown("---")

# Download history
if st.sidebar.button("Download Study History"):
    history_json = json.dumps(history, indent=2)
    st.sidebar.download_button(
        label="Download JSON",
        file_name="study_history.json",
        mime="application/json",
        data=history_json
    )

# Footer
st.markdown("---")
st.markdown("Built with ❤️ to enhance your learning experience")