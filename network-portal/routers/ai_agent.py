"""
AI Agent API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db, AgentTask
from ai.agent_manager import AgentManager

router = APIRouter()

# Global agent manager (initialized in main.py)
agent_manager: Optional[AgentManager] = None

def set_agent_manager(manager: AgentManager):
    """Set the global agent manager instance"""
    global agent_manager
    agent_manager = manager

class QueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None

class TaskResponse(BaseModel):
    id: int
    task_type: str
    query: str
    response: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/query")
async def query_agent(request: QueryRequest, db: Session = Depends(get_db)):
    """Send a query to the AI agent"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="AI agent not initialized")

    # Create task record
    task = AgentTask(
        task_type="query",
        query=request.query,
        status="running",
        metadata=request.context or {}
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        # Process query with agent
        response = await agent_manager.process_query(request.query, request.context)

        # Update task
        task.response = response
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        db.commit()

        return {
            "task_id": task.id,
            "response": response,
            "status": "completed"
        }
    except Exception as e:
        task.status = "failed"
        task.response = str(e)
        task.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(limit: int = 50, db: Session = Depends(get_db)):
    """List recent AI agent tasks"""
    tasks = db.query(AgentTask).order_by(AgentTask.created_at.desc()).limit(limit).all()
    return tasks

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get specific task details"""
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/status")
async def agent_status():
    """Get AI agent status"""
    if not agent_manager:
        return {"status": "not_initialized", "ready": False}

    return {
        "status": "ready" if agent_manager.is_ready() else "initializing",
        "ready": agent_manager.is_ready(),
        "model": agent_manager.get_model_info()
    }
