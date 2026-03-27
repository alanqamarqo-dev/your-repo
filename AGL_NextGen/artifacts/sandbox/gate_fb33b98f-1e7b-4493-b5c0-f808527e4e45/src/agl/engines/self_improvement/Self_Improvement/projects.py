import json
import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


PROJECTS_DIR = os.path.join("artifacts", "projects")


def _ensure_projects_dir():
    os.makedirs(PROJECTS_DIR, exist_ok=True)


@dataclass
class ProjectTask:
    id: str
    description: str
    status: str = "pending"  # pending / running / done / failed
    result_summary: Optional[str] = None


@dataclass
class AGLProject:
    id: str
    goal: str
    tasks: List[ProjectTask] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_ts: float = field(default_factory=time.time)
    updated_ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "tasks": [t.__dict__ for t in self.tasks],
            "state": self.state,
            "history": self.history,
            "created_ts": self.created_ts,
            "updated_ts": self.updated_ts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AGLProject":
        tasks = [ProjectTask(**t) for t in data.get("tasks", [])]
        return cls(
            id=data["id"],
            goal=data["goal"],
            tasks=tasks,
            state=data.get("state", {}),
            history=data.get("history", []),
            created_ts=data.get("created_ts", time.time()),
            updated_ts=data.get("updated_ts", time.time()),
        )


class ProjectStore:
    """
    تخزين/تحميل مشاريع AGI على هيئة JSON تحت artifacts/projects.
    """

    def __init__(self):
        _ensure_projects_dir()

    def _path_for(self, project_id: str) -> str:
        safe_id = project_id.replace(" ", "_")
        return os.path.join(PROJECTS_DIR, f"{safe_id}.json")

    def save(self, project: AGLProject) -> None:
        project.updated_ts = time.time()
        path = self._path_for(project.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self, project_id: str) -> Optional[AGLProject]:
        path = self._path_for(project_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AGLProject.from_dict(data)


# واجهة عالية المستوى

def create_project(project_id: str, goal: str) -> AGLProject:
    store = ProjectStore()
    project = AGLProject(id=project_id, goal=goal)
    store.save(project)
    return project


def add_task(project_id: str, task_id: str, description: str) -> AGLProject:
    store = ProjectStore()
    project = store.load(project_id)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found")
    project.tasks.append(ProjectTask(id=task_id, description=description))
    store.save(project)
    return project


def run_next_task(project_id: str) -> Optional[AGLProject]:
    """
    نسخة بسيطة جدًا: تبحث عن أول pending task وتحوّله إلى done
    مع تلخيص وهمي. لاحقًا نربطه فعليًا بـ agl_pipeline.
    """
    store = ProjectStore()
    project = store.load(project_id)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found")

    next_task = None
    for t in project.tasks:
        if t.status == "pending":
            next_task = t
            break

    if next_task is None:
        return project  # لا يوجد مهام معلّقة

    # هنا لاحقًا نستدعي agl_pipeline لتنفيذ وصف المهمة
    next_task.status = "done"
    next_task.result_summary = f"تم تنفيذ المهمة: {next_task.description[:60]}"

    project.history.append(
        {
            "ts": time.time(),
            "task_id": next_task.id,
            "note": next_task.result_summary,
        }
    )

    store.save(project)
    return project
