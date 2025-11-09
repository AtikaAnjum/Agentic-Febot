from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import asyncio
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import time

# Import custom modules
from enhanced_agent import EnhancedSheGuardiaAgent
from location_services import LocationServices
from rag_knowledge import setup_knowledge_base
from models import HospitalSearchResult

# Load environment variables
load_dotenv()

# Global services
agent = None
location_service = None
knowledge_base = None

# -------------------------------------------------------------------------
# 🌐 FastAPI Lifespan (Startup / Shutdown)
# -------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent, location_service, knowledge_base
    try:
        agent = EnhancedSheGuardiaAgent()
        print("✅ Enhanced SheGuardia Agent initialized")

        location_service = LocationServices()
        print("✅ Location Services initialized")

        knowledge_base = setup_knowledge_base()
        print("✅ Knowledge Base initialized")

    except Exception as e:
        print(f"❌ Error during startup: {e}")

    yield
    print("🔄 Shutting down services...")

# -------------------------------------------------------------------------
# 🚀 FastAPI App
# -------------------------------------------------------------------------
app = FastAPI(
    title="SheGuardia API",
    description="Women's Safety Assistant with RAG and Agentic AI",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# 📦 Pydantic Models
# -------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    intent: str
    sources: Optional[List[str]] = []

class LocationRequest(BaseModel):
    query: str
    location: Optional[str] = None

class LocationResponse(BaseModel):
    results: List[Dict]
    query: str
    location: str

class KnowledgeRequest(BaseModel):
    query: str
    k: Optional[int] = 3

class KnowledgeResponse(BaseModel):
    knowledge: str
    sources: List[str]

# -------------------------------------------------------------------------
# 🌍 Endpoints
# -------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "SheGuardia API - Women's Safety Assistant",
        "version": "1.0.0",
        "endpoints": ["/chat", "/location/search", "/knowledge/search", "/health"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent_available": agent is not None,
        "location_service_available": location_service is not None,
        "knowledge_base_available": knowledge_base is not None,
        "api_keys": {
            "deepseek": bool(os.getenv("DEEPSEEK_API_KEY")),
            "google_places": bool(os.getenv("GOOGLE_PLACES_API_KEY"))
        }
    }

# -------------------------------------------------------------------------
# 💬 Chat Endpoint (Graceful Errors + Timeout)
# -------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat with the Enhanced SheGuardia Agent"""
    if not agent:
        return ChatResponse(
            response="Hey lovely 💜, I’m still getting ready to chat. Please try again in a few moments!",
            intent="system",
            sources=[]
        )

    try:
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

        # Run with timeout protection
        response = await asyncio.wait_for(
            asyncio.to_thread(agent.process_query, request.message, conversation_history),
            timeout=170
        )

        intent = agent.classify_intent(request.message, conversation_history)
        return ChatResponse(response=response, intent=intent, sources=[])

    except asyncio.TimeoutError:
        # Graceful user-facing timeout message
        return ChatResponse(
            response="I'm so sorry 💜 it’s taking a bit longer than usual. Can you please try again?",
            intent="timeout",
            sources=[]
        )

    except Exception as e:
        # Graceful fallback message for all unexpected errors
        print(f"⚠️ Chat endpoint error: {e}")
        return ChatResponse(
            response="Oops! Something went wrong while processing your request 💜 Please try again.",
            intent="error",
            sources=[]
        )

# -------------------------------------------------------------------------
# 📍 Location Search (Graceful Errors)
# -------------------------------------------------------------------------
@app.post("/location/search", response_model=LocationResponse)
async def location_search(request: LocationRequest):
    if not location_service:
        return LocationResponse(
            results=[],
            query=request.query,
            location=request.location or "Not specified"
        )

    try:
        results = (
            location_service.search_places(request.query, request.location)
            if request.location
            else location_service.search_places(request.query)
        )

        return LocationResponse(
            results=results,
            query=request.query,
            location=request.location or "Not specified"
        )
    except Exception as e:
        print(f"⚠️ Location search error: {e}")
        return LocationResponse(
            results=[],
            query=request.query,
            location=request.location or "Not specified"
        )

# -------------------------------------------------------------------------
# 🧠 Knowledge Base Search (Graceful Errors)
# -------------------------------------------------------------------------
@app.post("/knowledge/search", response_model=KnowledgeResponse)
async def knowledge_search(request: KnowledgeRequest):
    if not knowledge_base:
        return KnowledgeResponse(
            knowledge="Sorry 💜 I can’t access the knowledge base right now. Please try again later.",
            sources=[]
        )

    try:
        docs = knowledge_base.similarity_search(request.query, k=request.k)
        knowledge = "\n\n".join([doc.page_content for doc in docs])
        sources = [doc.metadata.get("source", "Unknown") for doc in docs]

        return KnowledgeResponse(knowledge=knowledge, sources=sources)
    except Exception as e:
        print(f"⚠️ Knowledge search error: {e}")
        return KnowledgeResponse(
            knowledge="Hmm, I couldn’t retrieve that info right now 💜 Please try again later.",
            sources=[]
        )

# -------------------------------------------------------------------------
# 🧾 Agent Info
# -------------------------------------------------------------------------
@app.get("/agent/info")
async def agent_info():
    if not agent:
        return {"status": "Agent not initialized"}
    return agent.get_agent_info()

# -------------------------------------------------------------------------
# 🏥 Structured Hospital Data
# -------------------------------------------------------------------------
@app.get("/api/hospitals/{location}", response_model=HospitalSearchResult)
async def get_hospitals_structured(location: str, radius: int = 5000):
    try:
        location_service = LocationServices()
        return location_service.find_nearby_hospitals_structured(location, radius)
    except Exception as e:
        print(f"⚠️ Hospital search error: {e}")
        return HospitalSearchResult(hospitals=[], location=location)

# -------------------------------------------------------------------------
# 🚀 FastAPI Server Runner
# -------------------------------------------------------------------------
def run_fastapi_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=180,
        timeout_graceful_shutdown=30,
        limit_concurrency=100,
        log_level="info"
    )

# -------------------------------------------------------------------------
# 🏁 Entry Point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("🚀 Starting FastAPI server...")
        run_fastapi_server()
    else:
        print("🚀 Starting FastAPI server (default)...")
        run_fastapi_server()
