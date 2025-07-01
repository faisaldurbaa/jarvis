import streamlit as st # type: ignore
import ollama # type: ignore
from datetime import datetime
from llama_index.core import VectorStoreIndex # type: ignore
from llama_index.vector_stores.chroma import ChromaVectorStore # type: ignore
from llama_index.embeddings.ollama import OllamaEmbedding # type: ignore
from llama_index.llms.ollama import Ollama # type: ignore
from llama_index.core.llms import ChatMessage # type: ignore
import chromadb # type: ignore
import database
import os
import sys
import subprocess
from llama_index.core.tools import FunctionTool # type: ignore
import google_tools
from llama_index.core.agent import ReActAgent # type: ignore

st.set_page_config(page_title="JARVIS AI", page_icon="🤖", layout="centered", initial_sidebar_state="expanded")

# --- Constants & Model Config ---
DEFAULT_MODEL = 'phi4-mini:3.8b-q4_K_M'
MODELS = { "Fast": 'gemma3:1b-it-qat', "Primary": 'gemma3:4b-it-qat', "Smart": 'phi4-mini:3.8b-q4_K_M', "Genius": "qwen3:8b-Q4_K_M"}
CHROMA_DB_PATH = "./chroma_db"
EMBED_MODEL_NAME = 'nomic-embed-text'
KNOWLEDGE_VAULT_PATH = "./knowledge_vault"
CONSOLIDATED_MEM_PATH = os.path.join(KNOWLEDGE_VAULT_PATH, "consolidated_memories")
TOOL_KEYWORDS = ["calendar", "event", "schedule", "meeting", "email", "mail", "task", "to-do", "list", "gmail", "tasks"]
TITLE_LOCK_THRESHOLD = 10 

# --- NEW: Comprehensive CSS for a clean, minimalist sidebar ---
st.markdown("""
<style>
    /* Reduce top padding of the sidebar */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }
    
    /* Style all buttons within the sidebar for a uniform look */
    [data-testid="stSidebar"] button {
        background-color: transparent;
        border: none;
        outline: none;
        color: inherit;
        text-align: left;
        justify-content: flex-start;
        display: block;
        width: 100%;
        padding: 5px; /* Base padding */
        margin: 0;
        transition: background-color 0.2s;
        border-radius: 5px;
    }
    
    /* Specific style for the primary "New Chat" button */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        border: 1px solid rgba(255, 255, 255, 0.3);
        background-color: transparent;
    }

    [data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
        border-color: #ffffff;
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    /* Dynamic truncation for history titles */
    [data-testid="stSidebar"] button > div > p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Hover effect for feedback on all buttons */
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    /* Reduce gap between columns for action icons */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0.2rem; /* Tighter gap */
        padding: 0;
        margin: -5px 0; /* Reduce vertical space */
    }

    /* Reduce font size for the action icons */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button {
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

database.init_db()
os.makedirs(CONSOLIDATED_MEM_PATH, exist_ok=True)

# --- Core Functions (no changes from here down) ---
def get_current_datetime_string():
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")


@st.cache_data
def get_file_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except FileNotFoundError: return ""


def get_system_prompt():
    constitution = get_file_content('constitution.md')
    time_prompt = f"""The current date and time is: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}. 
    The user's timezone offset is +03:00. When you need to use a tool, use current date and time to convert 
    relative time statements like 'tomorrow, next wednesday, etc.'"""
    return f"{constitution}\n\n{time_prompt}"


@st.cache_resource
def get_index():
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = db.get_or_create_collection("jarvis_memory")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    embed_model = OllamaEmbedding(model_name=EMBED_MODEL_NAME)
    return VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)

def get_agent(chat_history):
    llm = Ollama(model="gemma3:4b-it-qat", request_timeout=120.0)
    
    return ReActAgent.from_tools(
        tools=all_tools,
        llm=llm,
        chat_history=chat_history,
        verbose=True
    )


def get_chat_engine(chat_history):
    system_prompt = get_system_prompt()
    llm = Ollama(model=st.session_state.selected_model, system_prompt=system_prompt)
    
    return get_index().as_chat_engine(
        chat_mode="context", 
        llm=llm, 
        chat_history=chat_history, 
        verbose=True
    )


def generate_text_with_model(model_name, prompt):
    messages = [{'role': 'user', 'content': prompt}]
    try:
        response = ollama.chat(model=model_name, messages=messages)
        return response['message']['content'].strip()
    except Exception as e:
        print(f"Error generating text with {model_name}: {e}")
        return None

def save_or_update_chat():
    if not st.session_state.messages or st.session_state.messages[-1]['role'] != 'assistant': return
    if st.session_state.chat_id is None:
        title = generate_text_with_model(MODELS["Fast"], f"Create a 3-7 word title for this conevrsation. Do not respond with any fillers. Do not use multiple lines or any formatting option. Respond only with the title.\n\n" + "\n".join([f"<{m['role']}>: {m['content']}" for m in st.session_state.messages]))
        if not title: title = f"Conversation ({datetime.now().strftime('%H:%M')})"
        new_id = database.save_chat_session(title, st.session_state.messages)
        st.session_state.chat_id, st.session_state.current_chat_title = new_id, title
    else:
        if len(st.session_state.messages) < TITLE_LOCK_THRESHOLD:
            new_title = generate_text_with_model(MODELS["Fast"], f"Create a 3-7 word title for this conevrsation. Do not add any fillers. Do not use multilpe lines or any formatting option. Respond only with the title.\n\n" + "\n".join([f"<{m['role']}>: {m['content']}" for m in st.session_state.messages]))
            if new_title: 
                database.update_chat_session(st.session_state.chat_id, new_title, st.session_state.messages)
                st.session_state.current_chat_title = new_title
        else:
            database.update_chat_session(st.session_state.chat_id, st.session_state.current_chat_title, st.session_state.messages)

def consolidate_memory(session_id, chat_title, current_time_str):
    messages = database.get_messages_for_session(session_id)
    if len(messages) <= 1:
        st.toast("Not enough content to consolidate.", icon="🤷")
        return
    user_messages = [m['content'] for m in messages if m['role'] == 'user']
    if not user_messages:
        st.toast("No user messages to consolidate.", icon="🤷")
        return
    user_conv_text = "\n".join(user_messages)
    consolidation_prompt = f"""
You are a data extraction bot. Your task is to convert a transcript of a user's statements into a structured list of key facts about the user.
You MUST ignore conversational filler and only extract permanent facts, goals, and decisions.
CRITICAL: You MUST convert all relative dates and times into absolute dates and times based on the provided current time.
--- PERFECT EXAMPLE ---
CURRENT TIME: Sunday, June 22, 2025 at 03:00 PM
USER STATEMENTS (INPUT):
"I need to prepare for my meeting tomorrow morning with the Globex team."
"Okay, my main goal is to secure the new budget."
"Also, remind me that the presentation slides are due next Friday."
CORRECT OUTPUT:
*   Has a meeting with the Globex team on June 23, 2025.
*   Primary goal for the Globex meeting is to secure the new budget.
*   A presentation slide deck is due on June 27, 2025.
--- END OF EXAMPLE ---
Now, perform the exact same task on the following real user statements. Provide only the Markdown list of facts.
CURRENT TIME: {current_time_str}
USER STATEMENTS (INPUT):
{user_conv_text}
CORRECT OUTPUT:
"""
    key_facts = generate_text_with_model(MODELS["Primary"], consolidation_prompt)
    if not key_facts:
        st.error("Memory consolidation failed. The AI returned an empty response.")
        return
    filename_prompt = f"Generate a single, short, descriptive, snake_case filename for these facts. Example: 'project_phoenix_deadline'. 3 words max. Filename only. No commentary.\n\nFacts:\n{key_facts}"
    filename_base = generate_text_with_model(MODELS["Fast"], filename_prompt)
    if filename_base:
        clean_filename = filename_base.split('\n')[0].strip().replace("`", "").replace("*", "")
        clean_filename = "".join(c if c.isalnum() or c in ['_'] else '_' for c in clean_filename)
    else:
        clean_filename = "consolidated_memory"
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"{timestamp}_{clean_filename}.md"
    filepath = os.path.join(CONSOLIDATED_MEM_PATH, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Memory from chat: {chat_title}\n\n{key_facts}")
    try:
        subprocess.run([sys.executable, "ingest.py"], capture_output=True, text=True, check=True)
        st.toast(f"Memory consolidated to '{filename}'!", icon="🧠")
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to update knowledge base: {e.stderr}")

all_tools = [
    FunctionTool.from_defaults(fn=google_tools.get_calendar_events, name="get_calendar_events", description="Use this to get a list of upcoming events from Google Calendar."),
    FunctionTool.from_defaults(fn=google_tools.create_calendar_event, name="create_calendar_event", description="Use this to create a new event on Google Calendar. Requires a summary, start_time, and end_time in full ISO 8601 format including timezone offset."),
    FunctionTool.from_defaults(fn=google_tools.list_google_tasks, name="list_google_tasks", description="Use this to get a list of current tasks from Google Tasks."),
    FunctionTool.from_defaults(fn=google_tools.create_google_task, name="create_google_task", description="Use this to create a new task in Google Tasks. Requires a title."),
    FunctionTool.from_defaults(fn=google_tools.read_emails, name="read_emails", description="Use this to read a summary of the latest unread emails from Gmail."),
]

if "messages" not in st.session_state: st.session_state.messages = []
if "selected_model" not in st.session_state: st.session_state.selected_model = DEFAULT_MODEL
if "chat_id" not in st.session_state: st.session_state.chat_id = None
if "current_chat_title" not in st.session_state: st.session_state.current_chat_title = "New Chat"
if "editing_title_id" not in st.session_state: st.session_state.editing_title_id = None
if "consolidating_id" not in st.session_state: st.session_state.consolidating_id = None

with st.sidebar:
    st.title("Settings")
    model_keys, model_values = list(MODELS.keys()), list(MODELS.values())
    try: current_model_index = model_values.index(st.session_state.selected_model)
    except ValueError: current_model_index = 0
    selected_model_name = st.selectbox("Choose a Model", options=model_keys, index=current_model_index)
    if MODELS[selected_model_name] != st.session_state.selected_model:
        st.session_state.selected_model = MODELS[selected_model_name]
        st.rerun()
    
    st.title("Actions")
    if st.button("New Chat", type="primary"):
        save_or_update_chat()
        st.session_state.messages, st.session_state.chat_id, st.session_state.current_chat_title = [], None, "New Chat"
        st.rerun()
    
    st.title("History")
    past_sessions = database.get_chat_sessions()
    for session_id, title, timestamp in past_sessions:
        col1, col2, col3, col4 = st.columns([0.6, 0.13, 0.13, 0.13])
        with col1:
            if st.button(f"{title}", key=f"session_{session_id}", help=f"{title}\nUpdated on {timestamp}", use_container_width=True):
                save_or_update_chat()
                st.session_state.messages = database.get_messages_for_session(session_id)
                st.session_state.chat_id, st.session_state.current_chat_title = session_id, title
                st.session_state.editing_title_id = None
                st.rerun()
        with col2:
            is_consolidating = (st.session_state.consolidating_id == session_id)
            if is_consolidating:
                st.button("⏳", key=f"consolidate_spin_{session_id}", help="Consolidating...", disabled=True)
            else:
                if st.button("🧠", key=f"consolidate_{session_id}", help="Consolidate Memory"):
                    st.session_state.consolidating_id = session_id
                    st.rerun()
        with col3:
            if st.button("✏️", key=f"edit_{session_id}", help="Rename chat"):
                st.session_state.editing_title_id = session_id
                st.rerun()
        with col4:
            if st.button("🗑️", key=f"delete_{session_id}", help="Delete chat"):
                database.delete_chat_session(session_id)
                if st.session_state.chat_id == session_id:
                    st.session_state.messages, st.session_state.chat_id, st.session_state.current_chat_title = [], None, "New Chat"
                st.rerun()

if st.session_state.editing_title_id is not None:
    session_to_edit = next((s for s in past_sessions if s[0] == st.session_state.editing_title_id), None)
    if session_to_edit:
        st.title("Rename Chat")
        new_title = st.text_input("Enter new title:", value=session_to_edit[1])
        if st.button("Save Title"):
            database.rename_chat_session(st.session_state.editing_title_id, new_title)
            if st.session_state.chat_id == st.session_state.editing_title_id:
                st.session_state.current_chat_title = new_title
            st.session_state.editing_title_id = None
            st.rerun()
        if st.button("Cancel"):
            st.session_state.editing_title_id = None
            st.rerun()
else:
    st.title(st.session_state.current_chat_title)

st.caption("JARVIS, Your Assistant.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("How can I help you, Sir?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            latest_prompt = st.session_state.messages[-1]["content"]
            chat_history = [ChatMessage(role=m["role"], content=m["content"]) for m in st.session_state.messages[:-1]]
            
            # --- The Router Logic ---
            use_agent = any(keyword in latest_prompt.lower() for keyword in TOOL_KEYWORDS)

            if use_agent:
                st.info("Using Google Tools Agent...", icon="🛠️")
                agent = get_agent(chat_history)
                streaming_response = agent.stream_chat(latest_prompt)
            else:
                # Default to the simple, reliable RAG Chat Engine
                chat_engine = get_chat_engine(chat_history)
                streaming_response = chat_engine.stream_chat(latest_prompt)

            # --- Display Response Stream ---
            message_placeholder = st.empty()
            full_response = ""
            # This robustly handles both agent and chat engine responses
            if hasattr(streaming_response, 'response_gen'):
                for token in streaming_response.response_gen:
                    full_response += token
                    message_placeholder.markdown(full_response + "▌")
            else: # Handle non-streaming tool outputs
                full_response = str(streaming_response)
            
            message_placeholder.markdown(full_response)
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_or_update_chat()
    st.rerun()

# --- Background Consolidation Trigger ---
if st.session_state.consolidating_id is not None:
    session_to_consolidate = next((s for s in past_sessions if s[0] == st.session_state.consolidating_id), None)
    if session_to_consolidate:
        consolidate_memory(st.session_state.consolidating_id, session_to_consolidate[1], get_current_datetime_string())
    st.session_state.consolidating_id = None
    st.rerun()