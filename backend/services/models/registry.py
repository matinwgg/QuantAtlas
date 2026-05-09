"""Simple in-memory model registry for development.

Later this can persist metadata to disk or a DB and track model artifacts.
"""

from typing import Dict, Any


class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, meta: Dict[str, Any]):
        self._models[name] = meta

    def list(self):
        return self._models

    def get(self, name: str):
        return self._models.get(name)


# module-level registry instance
registry = ModelRegistry()
