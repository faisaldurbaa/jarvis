# JARVIS AI Assistant

This is the codebase for JARVIS, a personalized AI Life Coach and assistant. It's a web-based chat application built with Streamlit that leverages the power of large language models (LLMs) to provide a conversational AI experience. JARVIS can remember past conversations, access a knowledge base, and interact with Google services like Calendar, Tasks, and Gmail.

## Project Philosophy

The primary goal of this project was to develop a **privacy-first, local, and proactive digital assistant** that is genuinely useful in daily life. Unlike many existing AI assistants that rely on cloud infrastructure and often have opaque privacy policies, JARVIS was designed to operate locally, ensuring that your data remains your own.

The core focus was on creating a secure and trustworthy assistant, free from the data privacy concerns associated with cloud-based solutions.

**Development is currently paused** due to the significant hardware requirements needed to run high-quality large language models with complex reasoning capabilities locally. The project is planned to resume in the near future once the necessary hardware is acquired.

---

## Features

*   **Conversational AI:** A simple and intuitive chat interface to interact with the AI assistant.
*   **Chat History:** Your conversations are saved and can be revisited later. You can also rename and delete past conversations.
*   **Model Selection:** You can choose from different LLMs to suit your needs, from fast and lightweight models to more powerful ones.
*   **Knowledge Vault:** JARVIS has a long-term memory feature. You can add markdown files to the `knowledge_vault` directory, and the AI will be able to access the information in them.
*   **Google Integration:** JARVIS can interact with your Google Calendar, Google Tasks, and Gmail. It can read your upcoming events, create new ones, list your tasks, create new tasks, and read your unread emails.
*   **Memory Consolidation:** JARVIS can consolidate important facts from your conversations into its knowledge base, allowing it to learn and remember key information about you over time.

## Technologies Used

*   **Python:** The primary programming language used.
*   **Streamlit:** For building the web application's user interface.
*   **Ollama:** To run and interact with the large language models locally.
*   **LlamaIndex:** A data framework for building LLM applications. It's used for the RAG (Retrieval-Augmented Generation) pipeline and agent-based tool usage.
*   **ChromaDB:** A vector store for storing and retrieving embeddings of the knowledge base documents.
*   **SQLite:** For storing the chat history.
*   **Google API Client Library for Python:** To interact with Google services.

## How it Works

The application is composed of several key components:

1.  **Streamlit Web App (`jarvis_app.py`):** This is the main entry point of the application. It handles the user interface, chat history, and the main chat loop. When a user sends a message, the app decides whether to use the RAG chat engine or the Google Tools agent based on keywords in the user's prompt.

2.  **Database (`database.py`):** This module manages the SQLite database where all chat sessions and messages are stored.

3.  **Google Tools (`google_tools.py`):** This file contains the functions that interact with the Google APIs for Calendar, Tasks, and Gmail. It handles authentication and the logic for fetching and creating data.

4.  **Ingestion Script (`ingest.py`):** This script is responsible for populating the ChromaDB vector store with the content of the `knowledge_vault` directory. It reads the markdown files, splits them into chunks, generates embeddings using an Ollama embedding model, and stores them in ChromaDB. It uses a hashing mechanism to only process new or modified files, making the ingestion process efficient.

5.  **Constitution (`constitution.md`):** This file serves as the AI's "brain." It contains the core instructions for the AI, including its personality, how to address the user, and the rules for using the available tools.

6.  **Knowledge Vault (`knowledge_vault/`):** This directory is the AI's long-term memory. You can add any markdown files with information you want the AI to remember. The `ingest.py` script will automatically process them and make them available to the AI.

## Setup and Usage

1.  **Prerequisites:**
    *   Python 3.x
    *   Ollama installed and running. You can download it from [ollama.ai](https://ollama.ai/).
    *   The required models downloaded and available in Ollama. The models used in this project are `gemma3:1b-it-qat`, `gemma3:4b-it-qat`, `phi4-mini:3.8b-q4_K_M`, and `qwen3:8b-Q4_K_M`. You can download them by running `ollama pull <model_name>`.
    *   Google Cloud project with the Calendar, Tasks, and Gmail APIs enabled. You will need to download your `credentials.json` file and place it in the root directory of the project.

2.  **Installation:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file is not provided in the repository. You will need to create one based on the imports in the Python files.)*

3.  **Run the Ingestion Script:**
    Before running the application for the first time, you need to populate the knowledge base.
    ```bash
    python ingest.py
    ```

4.  **Run the Application:**
    ```bash
    streamlit run jarvis_app.py
    ```

## Knowledge Vault

To add new knowledge to JARVIS, simply create a new markdown file (`.md`) in the `knowledge_vault` directory. The next time you run the `ingest.py` script, the new file will be processed and its content will be available to the AI.

For example, you can create a file named `my_project.md` with the following content:
```markdown
# My Project

My project is about building a personalized AI assistant. The goal is to create an AI that can help me with my daily tasks and remember important information.
```

After running `python ingest.py`, you can ask JARVIS questions about your project, and it will be able to answer them based on the information you provided.

## Future Improvements

*   **More Tools:** Add more tools to the AI, such as web search, weather, or integration with other services.
*   **User Authentication:** Implement user authentication to allow multiple users to use the application with their own chat history and knowledge bases.
*   **Improved UI:** Enhance the user interface with more features and a more polished design.
*   **Automated Ingestion:** Set up a process to automatically run the ingestion script whenever a new file is added to the knowledge vault.
*   **Automatic Memory Consolidation:** Develop a system where the AI can autonomously decide when and what to consolidate from conversations into its long-term memory, making the learning process seamless.
