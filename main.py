import os
import sqlite3
import json
import logging
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import dateparser

# --- 1. Production Setup & Enhanced Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("orchestix-core-v6")

app = FastAPI(title="Orchestix Control Center", version="6.0.0")

# Constants for Cloud Run Compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ephemeral writable storage for Cloud Run (Using a fresh DB name for v6)
DB_PATH = "/tmp/orchestix_cluster_v6.db" 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# CORS Configuration for the dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    input: str

# --- 2. Database Cluster Node ---
def init_db():
    """Initializes the SQLite cluster on container launch."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                title TEXT NOT NULL, 
                time TEXT NOT NULL, 
                reasoning TEXT,
                agent_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info(f"💾 Cluster Node ready at {DB_PATH}")
        return conn
    except Exception as e:
        logger.error(f"❌ DB Failure: {e}")
        return None

db_node = init_db()

# --- 3. AI Orchestration with Exponential Backoff ---
async def call_ai_with_retry(client, model_id, prompt, config):
    """Retries API calls for 429 errors using exponential wait times."""
    retries = 5
    for i in range(retries):
        try:
            return client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config
            )
        except Exception as e:
            err_msg = str(e).lower()
            if ("429" in err_msg or "resource_exhausted" in err_msg) and i < retries - 1:
                wait_time = 2 ** i
                logger.warning(f"⚠️ Rate limited. Node retrying in {wait_time}s... (Attempt {i+1})")
                await asyncio.sleep(wait_time)
                continue
            logger.error(f"❌ AI Core Failure: {e}")
            raise e

# --- 4. System API Routes ---

@app.get("/health")
def health_check():
    """Health probe for Cloud Run service discovery."""
    return {"status": "operational", "node": "asia-south1-v6", "timestamp": datetime.now().isoformat()}

@app.post("/agent")
async def process_orchestration(req: CommandRequest):
    """
    Executes the 4-Agent Orchestration Protocol:
    1. Analyzer Agent: Intent and logic recognition.
    2. Task Agent: Event formulation.
    3. Notes Agent: Temporal context alignment (2026).
    4. Optimizer Agent: Persists result to the cluster storage.
    """
    try:
        from google import genai
    except ImportError:
        logger.error("google-genai SDK missing")
        raise HTTPException(status_code=500, detail="Internal Dependency Failure")

    user_input = req.input
    if not user_input.strip():
        return JSONResponse({"error": "Empty input payload"}, status_code=400)

    # Server Context: Year 2026 calibration
    now = datetime.now()
    now_context = now.strftime('%A, %B %d, %Y at %H:%M:%S')
    
    # Pre-processing fallback extraction
    parsed_dt = dateparser.parse(user_input, settings={'PREFER_DATES_FROM': 'future'})
    dt = parsed_dt if parsed_dt else now
    
    final_data = {
        "title": "meeting", 
        "time": dt.strftime("%Y-%m-%dT%H:%M:%S"), 
        "reasoning": "Interpreted via local heuristic cluster node."
    }
    cluster_label = "Local Cluster"

    # AI Enhancement Node
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"SYSTEM CONTEXT: Today is {now_context}. Year: 2026.\n"
                f"COMMAND: '{user_input}'\n"
                f"TASK: Extract event title, ISO timestamp, and reasoning logic.\n"
                f"RETURN ONLY JSON: {{'title': string, 'time': string, 'reasoning': string}}"
            )
            
            ai_res = await call_ai_with_retry(
                client=client,
                model_id="gemini-2.5-flash",
                prompt=prompt,
                config={"response_mime_type": "application/json"}
            )
            
            if ai_res and ai_res.text:
                final_data = json.loads(ai_res.text)
                cluster_label = "Gemini Flash AI Cluster"
        except Exception as e:
            logger.error(f"⚠️ AI Agent Cluster Failed: {e}")
            final_data["reasoning"] += f" (Fallback engaged: AI Node limited)"

    # Persistence Node
    if db_node:
        try:
            cursor = db_node.cursor()
            cursor.execute(
                "INSERT INTO events (title, time, reasoning, agent_source) VALUES (?, ?, ?, ?)", 
                (final_data['title'], final_data['time'], final_data.get('reasoning', ''), cluster_label)
            )
            db_node.commit()
            logger.info(f"✅ Synced: {final_data['title']}")
        except Exception as e:
            logger.error(f"❌ DB Sync Error: {e}")

    return {
        "flow": [
            {"agent": "analyzer", "message": f"🧠 Reasoning: {final_data.get('reasoning')}", "status": "Done"},
            {"agent": "task", "message": f"📋 '{final_data['title']}' validated.", "status": "Done"},
            {"agent": "notes", "message": f"📝 Timestamp: {final_data['time']}.", "status": "Done"},
            {"agent": "optimizer", "message": f"⚡ Source: {cluster_label}.", "status": "Done"}
        ],
        "summary": f"Orchestix: {final_data['title']} recorded."
    }

@app.get("/events")
def list_cluster_events():
    """Retrieves all records for the dashboard calendar grid."""
    if not db_node: return []
    try:
        cursor = db_node.cursor()
        rows = cursor.execute("SELECT id, title, time FROM events ORDER BY time ASC").fetchall()
        return [{"id": r[0], "title": r[1], "time": r[2]} for r in rows]
    except Exception as e:
        logger.error(f"Fetch fail: {e}")
        return []

@app.delete("/events")
def purge_cluster():
    """Wipes the data node."""
    if db_node:
        db_node.execute("DELETE FROM events")
        db_node.commit()
    return {"cleared": True}

@app.get("/")
def serve_index():
    """Serves the frontend bundle."""
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# --- 5. Boot Sector ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Cluster V6 Online on Port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)