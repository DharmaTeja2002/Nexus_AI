import streamlit as st
import requests
import os

# Configure the API URL (Localhost by default, but configurable for Render)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Setup the page layout and title
st.set_page_config(page_title="Nexus AI", page_icon="🧠", layout="wide")

st.title("🧠 Nexus AI: Universal Knowledge Assistant")
st.markdown("""
**Welcome to your personal multimodal AI researcher.** 
Nexus AI allows you to ingest up to 14 different formats of unstructured data (PDFs, Videos, Audio, Code) into a PostgreSQL Vector Memory Bank, and instantly query that knowledge using blazing-fast LLMs.

👈 **Upload your files in the sidebar to get started!**
""")

# --- SIDEBAR: File Uploads & Settings ---
with st.sidebar:
    st.header("⚙️ AI Settings")
    
    # Model Selection Dropdown
    selected_model = st.selectbox(
        "Select AI Model:",
        options=["Groq (Llama-3)", "Google (Gemini 1.5)", "Together AI (Llama-3.1)"],
        index=0,
        help="Choose which AI engine will answer your questions."
    )
    
    # Map the dropdown selection to our backend provider ID
    provider_map = {
        "Groq (Llama-3)": "groq",
        "Google (Gemini 1.5)": "gemini",
        "Together AI (Llama-3.1)": "together"
    }
    selected_provider = provider_map[selected_model]
    
    st.divider()
    
    st.header("📂 Ingest Knowledge")
    st.markdown("Upload architecture PDFs, meeting audio, or code files to the Vector Memory Bank.")
    
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "png", "jpg", "jpeg", "txt", "mp3", "wav", "mp4"])
    
    if st.button("Upload to Nexus AI"):
        if uploaded_file is not None:
            with st.spinner("Processing and vectorizing..."):
                try:
                    # We send the file to our FastAPI backend using requests
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        st.success(f"✅ Successfully ingested {uploaded_file.name}!")
                    else:
                        st.error(f"❌ Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Failed to connect to backend: {e}")
        else:
            st.warning("Please select a file first.")

# --- MAIN AREA: Chat Interface ---
# Initialize the chat history in Streamlit's Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new user input
if prompt := st.chat_input(f"Ask a technical question (using {selected_model})..."):
    # 1. Display the user's question
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Add the question to the session state memory
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. Ask the FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner(f"Asking {selected_model}..."):
            try:
                # Send the question AND the selected provider to our FastAPI /ask endpoint
                payload = {
                    "question": prompt,
                    "provider": selected_provider
                }
                response = requests.post(f"{API_URL}/ask", json=payload)
                
                if response.status_code == 200:
                    answer = response.json().get("answer", "No answer found.")
                    st.markdown(answer)
                    # Add the AI's response to the session state memory
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Error from server: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
