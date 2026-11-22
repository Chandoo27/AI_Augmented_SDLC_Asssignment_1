from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from threading import RLock
from typing import TypeVar
from uuid import UUID

from pydantic import ValidationError

from src.models import Task

T = TypeVar("T")


class PersistenceError(Exception):
    pass


class TaskNotFound(Exception):
    pass


class JsonTaskStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = RLock()

    def list_tasks(self) -> list[Task]:
        with self._lock:
            return self._read()

    def get_task(self, task_id: UUID) -> Task:
        with self._lock:
            for task in self._read():
                if task.id == task_id:
                    return task
        raise TaskNotFound

    def transact(self, operation: Callable[[list[Task]], T]) -> T:
        with self._lock:
            tasks = self._read()
            result = operation(tasks)
            self._write(tasks)
            return result

    def _read(self) -> list[Task]:
        try:
            raw_data = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError) as error:
            raise PersistenceError("Could not read task data") from error

        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError as error:
            raise PersistenceError("Task data is not valid JSON") from error

        if not isinstance(payload, list):
            raise PersistenceError("Task data must be a JSON array")

        try:
            return [Task.model_validate(item) for item in payload]
        except (ValidationError, TypeError, ValueError) as error:
            raise PersistenceError("Task data is invalid") from error

    def _write(self, tasks: list[Task]) -> None:
        temporary_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f"{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(
                    [task.model_dump(mode="json", by_alias=True) for task in tasks],
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
        except (OSError, TypeError, ValueError) as error:
            raise PersistenceError("Could not save task data") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
