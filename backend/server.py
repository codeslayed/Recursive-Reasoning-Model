from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime, timezone

from models import ReasoningSession, SessionCreate, ReasoningStep
from services.recursive_engine import RecursiveEngine

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize LLM
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()


@api_router.post("/sessions", response_model=ReasoningSession)
async def create_session(input: SessionCreate):
    """Create a new reasoning session."""
    session = ReasoningSession(
        query=input.query,
        max_depth=input.max_depth,
        model=input.model,
        status="pending"
    )
    
    doc = session.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['steps'] = []
    
    await db.reasoning_sessions.insert_one(doc)
    return session


@api_router.get("/sessions", response_model=List[ReasoningSession])
async def get_sessions():
    """Get all reasoning sessions."""
    sessions = await db.reasoning_sessions.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    for session in sessions:
        if isinstance(session['created_at'], str):
            session['created_at'] = datetime.fromisoformat(session['created_at'])
        if session.get('completed_at') and isinstance(session['completed_at'], str):
            session['completed_at'] = datetime.fromisoformat(session['completed_at'])
    
    return sessions


@api_router.get("/sessions/{session_id}", response_model=ReasoningSession)
async def get_session(session_id: str):
    """Get a specific reasoning session."""
    session = await db.reasoning_sessions.find_one({"id": session_id}, {"_id": 0})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if isinstance(session['created_at'], str):
        session['created_at'] = datetime.fromisoformat(session['created_at'])
    if session.get('completed_at') and isinstance(session['completed_at'], str):
        session['completed_at'] = datetime.fromisoformat(session['completed_at'])
    
    return session


@api_router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time reasoning updates."""
    await manager.connect(session_id, websocket)
    
    try:
        # Get session from DB
        session = await db.reasoning_sessions.find_one({"id": session_id}, {"_id": 0})
        if not session:
            try:
                await websocket.send_json({"type": "error", "message": "Session not found"})
            except:
                pass
            manager.disconnect(session_id)
            return
        
        # Update session status
        await db.reasoning_sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "processing"}}
        )
        
        await manager.send_message(session_id, {
            "type": "status_change",
            "data": {"status": "processing"}
        })
        
        # Initialize reasoning engine
        engine = RecursiveEngine(EMERGENT_KEY, session['model'])
        
        # Callback for step updates
        async def step_callback(event_type: str, data: dict):
            try:
                if event_type == "step_start":
                    await manager.send_message(session_id, {
                        "type": "step_start",
                        "data": data
                    })
                elif event_type == "step_complete":
                    # Save step to database
                    step = ReasoningStep(
                        step_type=data['type'],
                        content=data['content'],
                        tokens_used=data.get('tokens', 0),
                        latency_ms=data.get('latency_ms', 0),
                        confidence=data.get('confidence', 0.0)
                    )
                    
                    step_dict = step.model_dump()
                    step_dict['timestamp'] = step_dict['timestamp'].isoformat()
                    
                    await db.reasoning_sessions.update_one(
                        {"id": session_id},
                        {"$push": {"steps": step_dict}}
                    )
                    
                    await manager.send_message(session_id, {
                        "type": "step_complete",
                        "data": step_dict
                    })
            except Exception as e:
                logging.error(f"Step callback error: {str(e)}")
        
        # Process query
        result = await engine.process_query(
            session['query'],
            session_id,
            session['max_depth'],
            step_callback
        )
        
        # Update session with final result
        await db.reasoning_sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "status": "completed",
                    "final_answer": result['final_answer'],
                    "total_tokens": result['total_tokens'],
                    "total_latency_ms": result['total_latency_ms'],
                    "recursion_depth": result['recursion_depth'],
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        await manager.send_message(session_id, {
            "type": "completion",
            "data": result
        })
        
        # Keep connection open to prevent immediate close
        try:
            while True:
                data = await websocket.receive_text()
                if data == "close":
                    break
        except WebSocketDisconnect:
            pass
    
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        try:
            await manager.send_message(session_id, {
                "type": "error",
                "data": {"message": str(e)}
            })
        except:
            pass
    finally:
        manager.disconnect(session_id)


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
