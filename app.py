import streamlit as st
import streamlit as st
import assemblyai as aai
from st_audiorec import st_audiorec
import requests
import ollama
import pdfplumber
import PyPDF2
# import docx
import os
from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.tools.tavily_search import TavilySearchResults
from pdfminer.high_level import extract_text

os.environ["TAVILY_API_KEY"] = "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"
aai.settings.api_key = "efbd737ee08d4fe382d3ae96897690a2"
eleven_labs_id = "031f62084b0c89447515566a18b09b64"
# Home Page
def home_page():
    # Define CSS styles
    css = """
    <style>
        .header {
            text-align: center;
            padding: 20px;
            background-color: #333333;
            color: #ffffff;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .feature-card {
            text-align: center;
            padding: 20px;
            background-color: #f0f0f0;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # Add a header section
    st.markdown(
        '<div class="header"><h1>📚 Activate Academics</h1><p>Your personal assistant for academic success</p></div>',
        unsafe_allow_html=True
    )

    # Home page content
    st.write("""
    Welcome to Activate Academics, a comprehensive platform designed to empower students in their academic journey. Our web app offers powerful features to help you excel in your studies and achieve your full potential.
    """)

    st.write("""
    Explore the features in the sidebar to discover our offerings.
    """)

# Personalized Learning Assistant
def personalized_learning_assistant():
    st.markdown('<div class="feature-container">', unsafe_allow_html=True)

    st.title("💬 Personalized Learning Assistant")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you with your personalized learning?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Load initial prompt from Agent 3 response file
    initial_prompt_file = "agent3_initial_prompt.txt"
    if os.path.exists(initial_prompt_file):
        with open(initial_prompt_file, "r") as f:
            initial_prompt = f.read()
    else:
        initial_prompt = "I'm ready to learn! What can you teach me?"

    if prompt := st.chat_input():
        # Save Agent 3 response to file
        def save_agent3_response(response):
            with open(initial_prompt_file, "w") as f:
                f.write(response)

        # AGENT 1
        print(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # Initialize the ollama model
        response_1 = ollama.chat(model='llama3', messages=[
            {
                "role": "user",
                "content": prompt+ "##### This is saved memory about the user which he entered in previous sessions (No need to message something about this until asked):"+ initial_prompt,
            }
        ])
        msg = response_1['message']['content']
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write("Agent1: "+msg)

        # AGENT 2
        prompt_02 = f"User: {prompt} #### Agent1: {response_1['message']['content']} ##### This is saved memory about the user which he entered in previous sessions (No need to message something about this until asked):+ {initial_prompt}"

        # Get the output from Agent 2 - HR
        response_2 = ollama.chat(model='llama3', messages=[
            {
                "role":"user",
                "content": prompt_02,
            }
        ])

        msg = response_2['message']['content']
        st.session_state.messages.append({"role": "assistant1", "content": "Agent2: "+msg})
        st.chat_message("assistant").write("Agent2: "+msg)

        # AGENT 3
        prompt_03 = f"{prompt} #### You are the users personalization agent. You keep note of all things things the user is good at or bad at along with his likes and dislikes. Whenever you find something unique about your agent you will note it down. Your output is always crisp, clear and short."

        # Get the output from Agent 3
        response_3 = ollama.chat(model='llama3', messages=[
            {
                "role":"user",
                "content": prompt_03,
            }
        ])

        save_msg = response_3['message']['content']
        save_agent3_response(save_msg)  # Save Agent 3 response to file

    st.markdown('</div>', unsafe_allow_html=True)

# Other feature functions
def academic_advisor_integration():
    st.markdown('<div class="feature-container">', unsafe_allow_html=True)
    st.title("📘 Talk to your pdfs")
    # st.header("Talk to your pdfs")

    uploaded_file = st.file_uploader(
        "Upload a pdf, docx, or txt file", type=["pdf", "txt"],
        help="Scanned documents are not supported yet!"
    )

    if not uploaded_file:
        st.stop()
    
    with st.spinner("Indexing document... This may take a while⏳"):
        if uploaded_file.type == "application/pdf":
            # Read the PDF file
            pdf_reader = pdfplumber.open(uploaded_file)
            # Extract the content
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text()
            pdf_reader.close()
        elif uploaded_file.type == "text/plain":
            # Read the TXT file
            content = uploaded_file.read().decode("utf-8")

    if content:
        st.success("Document loaded successfully")
    else:
        st.error("Document not loaded or is empty")
    

    search = TavilySearchAPIWrapper()
    tavily_tool = TavilySearchResults(api_wrapper=search)

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "What questions do you want to ask from the uploaded document?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():

        # PDF Agent
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # Initialize the ollama model
        response_1 = ollama.chat(model='llama3', messages=[
            {
                "role": "user",
                "content": f"{data} #### You are a QnA bot and answer the userinput question from the content provided? ##### User input: {prompt} #### If the question asked in not found in the provided data then Write 'No relevant information found in the document'",
            }
        ])
        msg = response_1['message']['content']

        if "No relevant information found in the document" not in msg:
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
        else:
            # Tavily Search Agent
            st.session_state.messages.append({"role": "assistant", "content": "No relevant information found in the document. Do you want to search the internet for an answer?"})
            st.chat_message("assistant").write("No relevant information found in the document. Do you want to search the internet for an answer?")

            if st.button("Search Internet"):
                tavily_tool.run(prompt)

    st.markdown('</div>', unsafe_allow_html=True)

def voice_chat_mental_health():
    st.markdown('<div class="feature-container">', unsafe_allow_html=True)
    API_KEY = 'enter-openai-api-key-here'

    API_KEY = 'enter-openai-api-key-here'



    def transcribe_text_to_voice(wav_audio_data):
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(wav_audio_data)
        return transcript.text


    def chat_completion_call(text):
        client = OpenAI(api_key=API_KEY)
        messages = [{"role": "user", "content": text}]
        response = client.chat.completions.create(model="gpt-3.5-turbo-1106", messages=messages)
        return response.choices[0].message.content


    def text_to_speech_ai(speech_file_path, api_response):
        client = OpenAI(api_key=API_KEY)
        response = client.audio.speech.create(model="tts-1",voice="nova",input=api_response)
        response.stream_to_file(speech_file_path)



    st.title("🧑‍💻 Skolo Online 💬 Talking Assistant")

    """
    Hi🤖 just click on the voice recorder and let me know how I can help you today?
    """

    wav_audio_data = st_audiorec()
    if wav_audio_data is not None:
        
        st.audio(wav_audio_data, format='audio/wav')

        #Transcribe the saved file to text
        text = transcribe_text_to_voice(wav_audio_data)
        st.write("Transcribed Text: "+text)

        #Use API to get an AI response
        api_response = chat_completion_call(text)
        st.write(api_response)

        # Read out the text response using tts
        speech_file_path = 'audio_response.mp3'
        text_to_speech_ai(speech_file_path, api_response)
        st.audio(speech_file_path)

    st.markdown('</div>', unsafe_allow_html=True)

# Set page configuration
st.set_page_config(
    page_title="Activate Academics",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define features and their corresponding functions
features = {
    "Home": home_page,
    "Personalized Learning Assistant": personalized_learning_assistant,
    "Academic Advisor Integration": academic_advisor_integration,
    "Mental Health Support": voice_chat_mental_health,
}

# Sidebar
with st.sidebar:
    # Display dropdown menu
    selected_feature = st.selectbox("Select a feature", list(features.keys()))

# Display feature function
if selected_feature:
    features[selected_feature]()
