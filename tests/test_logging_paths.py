import engine.logging
import engine.platform_win.paths
from engine.logging import get_default_log_path


def test_get_default_log_path(tmp_path, monkeypatch):
    # Mock get_log_path
    fake_log_path = tmp_path / "logs" / "test.log"
    monkeypatch.setattr(engine.logging, "get_log_path", lambda: str(fake_log_path))
    monkeypatch.setattr(engine.platform_win.paths, "get_log_path", lambda: str(fake_log_path))

    path = get_default_log_path()
    assert str(path) == str(fake_log_path)
    assert path.parent.exists()
