import json

import pytest

from engine.stats import StatsManager


@pytest.fixture
def temp_stats_file(tmp_path):
    return tmp_path / "stats.json"


def test_stats_initialization_defaults(temp_stats_file):
    """Verify that a new StatsManager initializes with empty/zero values."""
    manager = StatsManager(temp_stats_file)
    stats = manager.get_report()

    assert stats["lifetime"]["total_transcriptions"] == 0
    assert stats["lifetime"]["total_duration_seconds"] == 0
    assert stats["lifetime"]["total_words"] == 0
    assert stats["schema_version"] == 2


def test_stats_atomic_save(temp_stats_file):
    """Verify that saving creates the file and it contains correct data."""
    manager = StatsManager(temp_stats_file)
    manager.record_session(duration_seconds=10, words=5, provider="openai")
    manager.save()

    assert temp_stats_file.exists()
    with open(temp_stats_file, "r") as f:
        data = json.load(f)
    assert data["lifetime"]["total_transcriptions"] == 1
    assert data["lifetime"]["total_words"] == 5


def test_stats_corruption_recovery(temp_stats_file):
    """Verify that corrupted JSON is moved to .corrupt and a new file is started."""
    temp_stats_file.write_text("NOT JSON CONTENT")

    manager = StatsManager(temp_stats_file)
    stats = manager.get_report()

    # Should have re-initialized
    assert stats["lifetime"]["total_transcriptions"] == 0
    # Original should have been renamed
    corrupt_files = list(temp_stats_file.parent.glob("stats.json.corrupt.*"))
    assert len(corrupt_files) == 1


def test_stats_persistence_across_restarts(temp_stats_file):
    """Verify that stats survive a 'restart' of the StatsManager."""
    m1 = StatsManager(temp_stats_file)
    m1.record_session(duration_seconds=120, words=100, provider="assemblyai")
    m1.save()

    # Simulate restart
    m2 = StatsManager(temp_stats_file)
    stats = m2.get_report()
    assert stats["lifetime"]["total_transcriptions"] == 1
    assert stats["lifetime"]["total_words"] == 100
    assert stats["lifetime"]["provider_usage"]["assemblyai"] == 1


def test_stats_aggregation_logic(temp_stats_file):
    """Verify that get_report correctly rolls up daily and monthly stats."""
    manager = StatsManager(temp_stats_file)

    # We'll use the record_session as is, but we need to ensure get_report
    # processes the 'history' into buckets.
    manager.record_session(duration_seconds=60, words=50, provider="openai")

    report = manager.get_report()

    assert "today" in report
    assert "this_week" in report
    assert "this_month" in report

    assert report["today"]["total_transcriptions"] == 1
    assert report["today"]["total_words"] == 50
    assert report["this_week"]["total_words"] == 50
    assert report["this_month"]["total_words"] == 50
    assert report["lifetime"]["total_words"] == 50
