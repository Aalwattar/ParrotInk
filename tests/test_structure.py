import importlib


def test_engine_import():
    """Verify that the engine package can be imported."""
    engine = importlib.import_module("engine")
    assert engine is not None
