import os
import json
import hashlib
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
import chromadb

# --- Configuration ---
KNOWLEDGE_VAULT_PATH = "./knowledge_vault"
CHROMA_DB_PATH = "./chroma_db"
HASHES_FILE_PATH = "./hashes.json"
EMBED_MODEL_NAME = 'nomic-embed-text'

# --- Functions ---
def get_file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(h.block_size)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def load_hashes():
    if os.path.exists(HASHES_FILE_PATH):
        with open(HASHES_FILE_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_hashes(hashes):
    with open(HASHES_FILE_PATH, 'w') as f:
        json.dump(hashes, f, indent=4)

# --- Main Ingestion Logic ---
print("Starting ingestion process...")

# 1. Initialize ChromaDB client and collection
db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
chroma_collection = db.get_or_create_collection("jarvis_memory")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
print("ChromaDB connection established.")

# 2. Handle Deletions ("Orphan" Cleanup)
print("Scanning for deleted files...")
# Get all files currently in the database
db_files = set()
all_docs_in_db = chroma_collection.get(include=["metadatas"])
for metadata in all_docs_in_db['metadatas']:
    if 'file_name' in metadata:
        db_files.add(metadata['file_name'])

# Get all files currently on disk
disk_files = set()
for dirpath, _, filenames in os.walk(KNOWLEDGE_VAULT_PATH):
    for filename in filenames:
        disk_files.add(filename)

# Find files that are in the DB but not on disk
files_to_delete = db_files - disk_files
if files_to_delete:
    print(f"Found {len(files_to_delete)} file(s) to delete from memory: {files_to_delete}")
    for filename in files_to_delete:
        chroma_collection.delete(where={"file_name": filename})
    print("Deleted orphan files from ChromaDB.")
else:
    print("No files to delete.")

# 3. Handle New and Modified Files
previous_hashes = load_hashes()
current_hashes = {}
files_to_process = []
print(f"Scanning '{KNOWLEDGE_VAULT_PATH}' for new or modified files...")
for dirpath, _, filenames in os.walk(KNOWLEDGE_VAULT_PATH):
    for filename in filenames:
        if filename.endswith(('.md', '.txt')):
            filepath = os.path.join(dirpath, filename)
            file_hash = get_file_hash(filepath)
            current_hashes[filepath] = file_hash
            if previous_hashes.get(filepath) != file_hash:
                files_to_process.append(filepath)
                print(f"  - Found new/changed file: {filename}")

if not files_to_process:
    print("No new or modified files to process.")
else:
    print(f"Processing {len(files_to_process)} file(s)...")
    reader = SimpleDirectoryReader(
        input_files=files_to_process,
        file_metadata=lambda filename: {"file_name": os.path.basename(filename)}
    )
    documents = reader.load_data()
    print(f"Loaded {len(documents)} document(s).")
    
    node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = node_parser.get_nodes_from_documents(documents, show_progress=True)
    print(f"Split documents into {len(nodes)} nodes (chunks).")
    
    embed_model = OllamaEmbedding(model_name=EMBED_MODEL_NAME)
    index = VectorStoreIndex(
        nodes, 
        embed_model=embed_model,
        storage_context=StorageContext.from_defaults(vector_store=vector_store)
    )
    print("Ingestion complete. Memory has been updated.")

# 4. Save the new hashes for the next run
save_hashes(current_hashes)
print("File hashes have been updated.")