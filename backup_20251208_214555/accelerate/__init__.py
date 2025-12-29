"""Minimal accelerate stub for tests.
Provides thin helpers so imports succeed during test collection.
"""

__all__ = ["init", "Accelerator"]


def init():
    return None


class Accelerator:
    def __init__(self, **kwargs):
        pass

    def prepare(self, *args, **kwargs):
        return args

    def unwrap_model(self, model):
        return model
