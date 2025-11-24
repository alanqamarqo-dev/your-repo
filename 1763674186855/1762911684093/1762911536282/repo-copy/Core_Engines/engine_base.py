from __future__ import annotations
from typing import Protocol, Any, Dict, Optional

class Engine(Protocol):
    name: str
    version: str
    def configure(self, **kwargs: Any) -> None: ...
    def healthcheck(self) -> Dict[str, Any]: ...

class EngineRegistry:
    _engines: Dict[str, Engine] = {}
    @classmethod
    def register(cls, engine: Engine) -> None: cls._engines[engine.name] = engine
    @classmethod
    def get(cls, name: str) -> Optional[Engine]: return cls._engines.get(name)
    @classmethod
    def list_names(cls) -> list[str]: return list(cls._engines.keys())
