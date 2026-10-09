"""Lazy exports keep the model catalog independent of runtime dependencies."""

from importlib import import_module

__all__ = ["BaseProvider", "OpenAIProvider", "AssemblyAIProvider", "TranscriptionFactory"]


def __getattr__(name):
    modules = {
        "BaseProvider": "base",
        "OpenAIProvider": "openai_provider",
        "AssemblyAIProvider": "assemblyai_provider",
        "TranscriptionFactory": "factory",
    }
    if name not in modules:
        raise AttributeError(name)
    return getattr(import_module(f"{__name__}.{modules[name]}"), name)
