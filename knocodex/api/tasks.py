"""Task management API endpoints"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from ..models.mcp_task import (
    MCPTaskRequest, MCPTaskUpdate, MCPTaskResponse, MCPTaskListResponse,
    MCPTaskFilter, TaskStatus, TaskType, TaskPriority
)
from ..workflow_engine import WorkflowEngine
from ..utils.redis_utils import get_project_queue_manager

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_workflow_engine():
    """Dependency to get workflow engine instance"""
    return WorkflowEngine()


def get_queue_manager():
    """Dependency to get queue manager instance"""
    return get_project_queue_manager()


@router.post("", response_model=MCPTaskResponse, status_code=201)
async def create_task(
    task_request: MCPTaskRequest,
    workflow: WorkflowEngine = Depends(get_workflow_engine),
    queue_manager = Depends(get_queue_manager)
):
    """Create a new task"""
    try:
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create task response object
        task = MCPTaskResponse(
            task_id=task_id,
            task_type=task_request.task_type,
            title=task_request.title,
            description=task_request.description,
            status=TaskStatus.PENDING,
            priority=task_request.priority,
            parameters=task_request.parameters,
            tags=task_request.tags,
            project_id=task_request.project_id,
            assignee=task_request.assignee,
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
            deadline=task_request.deadline,
            error_message=None,
            result=None,
            progress=0.0
        )
        
        # Submit task to workflow engine
        await workflow.submit_mcp_task(task)
        
        return task
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("", response_model=MCPTaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Tasks per page"),
    status: Optional[List[TaskStatus]] = Query(None, description="Filter by status"),
    task_type: Optional[List[TaskType]] = Query(None, description="Filter by type"),
    priority: Optional[List[TaskPriority]] = Query(None, description="Filter by priority"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """List tasks with filtering and pagination"""
    try:
        task_filter = MCPTaskFilter(
            status=status,
            task_type=task_type,
            priority=priority,
            project_id=project_id,
            assignee=assignee,
            search=search
        )
        
        tasks, total = await workflow.list_mcp_tasks(task_filter, page, per_page)
        pages = (total + per_page - 1) // per_page
        
        return MCPTaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/{task_id}", response_model=MCPTaskResponse)
async def get_task(
    task_id: str,
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get a specific task by ID"""
    try:
        task = await workflow.get_mcp_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.put("/{task_id}", response_model=MCPTaskResponse)
async def update_task(
    task_id: str,
    task_update: MCPTaskUpdate,
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Update a task"""
    try:
        task = await workflow.update_mcp_task(task_id, task_update)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.delete("/{task_id}", status_code=204)
async def cancel_task(
    task_id: str,
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Cancel a task"""
    try:
        success = await workflow.cancel_mcp_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/{task_id}/retry", response_model=MCPTaskResponse)
async def retry_task(
    task_id: str,
    workflow: WorkflowEngine = Depends(get_workflow_engine)
):
    """Retry a failed task"""
    try:
        task = await workflow.retry_mcp_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {str(e)}")