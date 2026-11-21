from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.models import Priority, Task, TaskCreate, TaskFilters, TaskSort, TaskStatus, TaskUpdate
from src.storage import JsonTaskStore, TaskNotFound


class TaskService:
    def __init__(self, store: JsonTaskStore) -> None:
        self.store = store

    def create_task(self, request: TaskCreate) -> Task:
        task = Task(
            id=uuid4(),
            title=request.title,
            description=request.description,
            priority=request.priority,
            tags=request.tags,
            status=TaskStatus.PENDING,
            createdAt=datetime.now(UTC),
        )

        def append(tasks: list[Task]) -> Task:
            tasks.append(task)
            return task

        return self.store.transact(append)

    def list_tasks(self, filters: TaskFilters | None = None) -> list[Task]:
        tasks = self.store.list_tasks()
        if filters is None:
            return tasks

        if filters.tags is not None:
            requested_tags = {tag.casefold() for tag in filters.tags}
            tasks = [
                task
                for task in tasks
                if requested_tags.intersection(tag.casefold() for tag in task.tags)
            ]

        if filters.sort is TaskSort.PRIORITY:
            tasks.sort(key=self.priority_key)

        return tasks

    def get_task(self, task_id: UUID) -> Task:
        return self.store.get_task(task_id)

    def update_task(self, task_id: UUID, request: TaskUpdate) -> Task:
        changes = request.model_dump(exclude_unset=True)

        def update(tasks: list[Task]) -> Task:
            for index, existing in enumerate(tasks):
                if existing.id == task_id:
                    updated_data = existing.model_dump()
                    updated_data.update(changes)
                    updated = Task.model_validate(updated_data)
                    tasks[index] = updated
                    return updated
            raise TaskNotFound

        return self.store.transact(update)

    def delete_task(self, task_id: UUID) -> None:
        def delete(tasks: list[Task]) -> None:
            for index, task in enumerate(tasks):
                if task.id == task_id:
                    del tasks[index]
                    return
            raise TaskNotFound

        self.store.transact(delete)

    def set_status(self, task_id: UUID, status: TaskStatus) -> Task:
        def update(tasks: list[Task]) -> Task:
            for index, existing in enumerate(tasks):
                if existing.id == task_id:
                    updated = existing.model_copy(update={"status": status})
                    tasks[index] = updated
                    return updated
            raise TaskNotFound

        return self.store.transact(update)

    @staticmethod
    def priority_key(task: Task) -> tuple[int, datetime, str]:
        priority_order = {
            Priority.HIGH: 0,
            Priority.MEDIUM: 1,
            Priority.LOW: 2,
        }
        return priority_order[task.priority], task.created_at, str(task.id)
