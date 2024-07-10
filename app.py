import streamlit as st
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import json
import datetime
import pdfplumber
import io
import gc
from huggingface_hub import InferenceClient
from requests.exceptions import RequestException

st.set_page_config(page_title="Activate Academics", page_icon="📚", layout="wide")

class StudentLearningAssistant:
    def __init__(self):
        self.qa_pipe = pipeline("question-answering", model="deepset/roberta-base-squad2")
        self.summary_pipe = pipeline("summarization", model="facebook/bart-large-cnn")
        self.t2t_pipe = pipeline("text2text-generation", model="google/flan-t5-base")
        self.history = []
        self.quiz_client = get_inference_client()

    def answer_question(self, question, context):
        result = self.qa_pipe(question=question, context=context)
        return result['answer']

    def summarize_text(self, text):
        summary = self.summary_pipe(text, max_length=1500, min_length=300, do_sample=False)[0]['summary_text']
        return summary

    def generate_quiz(self, context):
        formatted_prompt = self.system_instructions(context)
        generate_kwargs = dict(
            temperature=0.1,
            max_new_tokens=2048,
            top_p=0.95,
            repetition_penalty=1.0,
            do_sample=True,
            seed=42,
        )
        try:
            response = self.quiz_client.text_generation(
                formatted_prompt,
                **generate_kwargs,
                stream=False,
                details=False,
                return_full_text=False,
            )
            return response
        except (RequestException, SystemExit) as e:
            return f"Error: {str(e)}"

    def system_instructions(self, context):
        return f"""<s> [INST] You are a great teacher and your task is to create 6 questions with answer and 4 choices based on the following context:

    {context}

    Each example should be like this:
    Question: ""
    Choices:
    A) ""
    B) ""
    C) ""
    D) ""
    Answer: "A" or "B" or "C" or "D" according to the right answer
    Explanation: ""
    [/INST] """

    def explain_concept(self, concept):
        prompt = f"""Provide a detailed explanation of the concept '{concept}' in simple terms. 
        Your explanation should be at least 100 words long and cover the following:
        1. Definition of the concept
        2. Key aspects or components
        3. Real-world examples or applications
        4. Why it's important or relevant

        Concept: {concept}"""
        
        explanation = self.t2t_pipe(prompt, max_length=500, min_length=200, do_sample=True, temperature=0.7)[0]['generated_text']
        return explanation

    def add_to_history(self, item):
        item['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append(item)

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []

@st.cache_resource
def get_inference_client():
    return InferenceClient("mistralai/Mistral-7B-Instruct-v0.2")

def load_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
            gc.collect()  # Force garbage collection after each page
    return text

def add_bg_from_url(image_url):
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("{image_url}");
             background-attachment: fixed;
             background-size: cover;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

# Initialize session state
if 'assistant' not in st.session_state:
    st.session_state.assistant = StudentLearningAssistant()
if 'context' not in st.session_state:
    st.session_state.context = ""



# Sidebar for page selection
page = st.sidebar.selectbox("Select a learning tool:", ["Study Assistant", "Summary Generator", "Quiz Creator", "Concept Explainer"])

# Common sidebar elements
with st.sidebar:
    st.title("Activate Academics")
    st.caption("Your AI-powered learning companion")
    if st.button("Clear History"):
        st.session_state.assistant.clear_history()
        st.success("History cleared!")

# Page-specific content
if page == "Study Assistant":
    add_bg_from_url("https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?auto=format&fit=crop&q=80&w=3546&ixlib=rb-4.0.3")
    st.title("📚 AI Study Assistant")
    st.caption("Ask questions about your study material")

    with st.sidebar:
        st.header("Study Material")
        context_input = st.text_area("Enter your study text here:", value=st.session_state.context, height=300)
        uploaded_file = st.file_uploader("Or upload a PDF of your study material", type="pdf")
        if uploaded_file:
            st.session_state.context = load_pdf(uploaded_file)
            st.success("Study material loaded from PDF!")

    st.header("Ask Questions")
    for item in st.session_state.assistant.get_history():
        if item.get('type') == 'qa':
            st.info(f"Q: {item['question']}")
            st.success(f"A: {item['answer']}")

    question = st.text_input("What would you like to know about your study material?")
    if st.button("Ask"):
        if not st.session_state.context:
            st.warning("Please provide some study material first!")
        elif not question:
            st.warning("Please enter a question!")
        else:
            answer = st.session_state.assistant.answer_question(question, st.session_state.context)
            st.session_state.assistant.add_to_history({'type': 'qa', 'question': question, 'answer': answer})
            st.info(f"Q: {question}")
            st.success(f"A: {answer}")

elif page == "Summary Generator":
    add_bg_from_url("https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&q=80&w=3546&ixlib=rb-4.0.3")
    st.title("📝 Summary Generator")
    st.caption("Create concise summaries of your study material")

    text_input_method = st.radio("Choose input method:", ["Text", "PDF"])

    if text_input_method == "Text":
        text_to_summarize = st.text_area("Enter the text you want to summarize:", height=300)
    else:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        if uploaded_file is not None:
            text_to_summarize = load_pdf(uploaded_file)
            st.success("PDF uploaded successfully!")
        else:
            text_to_summarize = ""

    if st.button("Generate Summary"):
        if not text_to_summarize:
            st.warning("Please enter some text or upload a PDF to summarize!")
        else:
            summary = st.session_state.assistant.summarize_text(text_to_summarize)
            st.session_state.assistant.add_to_history({'type': 'summary', 'original': text_to_summarize, 'summary': summary})
            st.success("Summary:")
            st.write(summary)

elif page == "Quiz Creator":
    add_bg_from_url("https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&q=80&w=3540&ixlib=rb-4.0.3")
    st.title("🧠 Quiz Creator")
    st.caption("Generate quizzes from your study material")

    text_input_method = st.radio("Choose input method:", ["Text", "PDF"])

    if text_input_method == "Text":
        quiz_text = st.text_area("Enter the text you want to create a quiz from:", height=300)
    else:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        if uploaded_file is not None:
            quiz_text = load_pdf(uploaded_file)
            st.success("PDF uploaded successfully!")
        else:
            quiz_text = ""

    if st.button("Generate Quiz"):
        if not quiz_text:
            st.warning("Please enter some text or upload a PDF to create a quiz from!")
        else:
            with st.spinner("Generating quiz..."):
                quiz = st.session_state.assistant.generate_quiz(quiz_text)
            st.session_state.assistant.add_to_history({'type': 'quiz', 'text': quiz_text, 'quiz': quiz})
            st.success("Quiz:")
            st.write(quiz)

elif page == "Concept Explainer":
    add_bg_from_url("https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&q=80&w=3309&ixlib=rb-4.0.3")
    st.title("💡 Concept Explainer")
    st.caption("Get simple explanations for complex concepts")

    concept = st.text_input("Enter a concept you want explained:")
    if st.button("Explain Concept"):
        if not concept:
            st.warning("Please enter a concept to explain!")
        else:
            explanation = st.session_state.assistant.explain_concept(concept)
            st.session_state.assistant.add_to_history({'type': 'explanation', 'concept': concept, 'explanation': explanation})
            st.success(f"Explanation of {concept}:")
            st.write(explanation)

# Download history
if st.sidebar.button("Download Study History"):
    history = st.session_state.assistant.get_history()
    if history:
        json_str = json.dumps(history, indent=2)
        st.sidebar.download_button(
            label="Download JSON",
            file_name="study_history.json",
            mime="application/json",
            data=json_str
        )
    else:
        st.sidebar.warning("No study history to download.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ to enhance your learning experience")