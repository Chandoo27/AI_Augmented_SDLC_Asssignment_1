from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from src.models import ErrorResponse, Task, TaskCreate, TaskUpdate
from src.services import TaskService

router = APIRouter()

ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Task not found"},
    422: {"model": ErrorResponse, "description": "Invalid request"},
    500: {"model": ErrorResponse, "description": "Task data is unavailable"},
}


def get_task_service(request: Request) -> TaskService:
    return TaskService(request.app.state.store)


@router.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
def create_task(
    request: TaskCreate,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    return service.create_task(request)


@router.get(
    "/tasks",
    response_model=list[Task],
    responses={422: ERROR_RESPONSES[422], 500: ERROR_RESPONSES[500]},
)
def list_tasks(service: Annotated[TaskService, Depends(get_task_service)]) -> list[Task]:
    return service.list_tasks()


@router.get(
    "/tasks/{task_id}",
    response_model=Task,
    responses=ERROR_RESPONSES,
)
def get_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    return service.get_task(task_id)


@router.patch(
    "/tasks/{task_id}",
    response_model=Task,
    responses=ERROR_RESPONSES,
)
def update_task(
    task_id: UUID,
    request: TaskUpdate,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    return service.update_task(task_id, request)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: ERROR_RESPONSES[404], 422: ERROR_RESPONSES[422], 500: ERROR_RESPONSES[500]},
)
def delete_task(
    task_id: UUID,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> Response:
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
