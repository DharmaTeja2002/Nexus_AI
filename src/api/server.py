from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import shutil
import asyncio
from pathlib import Path
from src.memory.manager import MemoryManager
from src.api.llm import LLMClient
from src.ingestion.dispatcher import UnifiedIngestor
from src.core.config import settings

# Create our tools
manager = MemoryManager()
llm_client = LLMClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # What happens when the Waiter clocks in for their shift
    print("🌅 Waiter clocking in: Connecting to the PostgreSQL Memory Bank!")
    await manager.setup()
    yield
    # What happens when the Waiter clocks out
    print("🌙 Waiter clocking out.")

# This is our "Waiter". We are hiring them right now!
app = FastAPI(title="Nexus AI Backend", lifespan=lifespan)

# Add CORS Middleware to allow Streamlit to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this should be your Streamlit public URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This tells the Waiter: "If someone comes to the front door (/), say hello!"
@app.get("/")
def home():
    return {"message": "Hello! Welcome to Nexus AI."}

class AskRequest(BaseModel):
    question: str
    provider: str = "groq"

# This tells the Waiter: "If someone asks a question, go to the database!"
@app.post("/ask")
async def ask_ai(request: AskRequest):
    question = request.question
    provider = request.provider
    
    # 1. Take the question and translate it into "Vector Math"
    query_vector = await asyncio.to_thread(manager.embedder.embed_text, question)
    
    # 2. Run down to the PostgreSQL Vault and find the top 2 closest matches
    results = await manager.db.query(query_vector, top_k=2)
    
    # 3. Ask the Generative Brain (LLM) to read the matches and answer the question
    if not results:
        return {"answer": "I don't have any documents to answer that question."}
    
    answer = await llm_client.generate_rag_response(question, results, provider)
    
    # 4. Bring the final answer back to the customer
    return {
        "your_question": question, 
        "answer": answer,
        "sources_used": [res['source_file'] for res in results]
    }

# This tells the Waiter: "If someone brings a new file, process it and store it!"
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Save the file temporarily
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    filename = Path(file.filename).name
    file_path = settings.TEMP_DIR / filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # 2. Ingest the file using our Senses
    ingestor = UnifiedIngestor()
    elements = await ingestor.ingest_file(file_path)
    
    if not elements:
        if file_path.exists():
            file_path.unlink()
        return {"message": "File processed but no content could be extracted."}
    
    # 3. Create embeddings and save to Memory Bank
    texts = [el.content for el in elements]
    embeddings = await asyncio.to_thread(manager.embedder.embed_batch, texts)
    
    db_ready_data = []
    for j, el in enumerate(elements):
        db_ready_data.append({
            "content": el.content,
            "embedding": embeddings[j],
            "source": el.source_file,
            "metadata": el.metadata or {}
        })
        
    await manager.db.add_documents(db_ready_data)
    
    # Cleanup
    if file_path.exists():
        file_path.unlink()
        
    return {
        "message": f"Successfully ingested {file.filename}",
        "chunks_saved": len(db_ready_data)
    }
