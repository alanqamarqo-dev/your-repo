"""Minimal sentence-transformers stub for tests.
"""

class SentenceTransformer:
    def __init__(self, model_name_or_path):
        self.model_name_or_path = model_name_or_path

    def encode(self, texts, **kwargs):
        # return simple numeric vectors
        if isinstance(texts, str):
            texts = [texts]
        return [[float(len(t))] for t in texts]


def util_placeholder():
    return None
