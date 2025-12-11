"""Minimal peft stub for tests.
"""

__all__ = ["PeftModel", "prepare_model_for_kbit_training"]

class PeftModel:
    def __init__(self, model, config=None):
        self.model = model


def prepare_model_for_kbit_training(model, **kwargs):
    return model
