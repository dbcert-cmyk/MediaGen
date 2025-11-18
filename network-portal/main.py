"""
Home Network Management Portal
Main FastAPI application
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import os
import logging
from typing import List

from routers import devices, monitoring, ai_agent, network_ops
from database import engine, Base
from ai.agent_manager import AgentManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize agent manager
agent_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global agent_manager

    # Startup
    logger.info("Starting Home Network Portal...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")

    # Initialize AI agent
    agent_manager = AgentManager()
    await agent_manager.initialize()
    logger.info("AI Agent initialized")

    # Set agent manager in router
    ai_agent.set_agent_manager(agent_manager)

    yield

    # Shutdown
    logger.info("Shutting down...")
    if agent_manager:
        await agent_manager.shutdown()

# Create FastAPI app
app = FastAPI(
    title="Home Network Management Portal",
    description="AI-powered network management for home labs and small businesses",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(ai_agent.router, prefix="/api/ai", tags=["ai"])
app.include_router(network_ops.router, prefix="/api/network", tags=["network"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "ollama": agent_manager.is_ready() if agent_manager else False,
            "netbox": os.getenv("NETBOX_URL", "not configured"),
            "librenms": os.getenv("LIBRENMS_URL", "not configured")
        }
    }

@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """WebSocket endpoint for real-time AI agent communication"""
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"Received: {data}")

            # Process with AI agent
            if agent_manager:
                response = await agent_manager.process_query(data)
                await websocket.send_json({"response": response})
            else:
                await websocket.send_json({"error": "Agent not initialized"})

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
