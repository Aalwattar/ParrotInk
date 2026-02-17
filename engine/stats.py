import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from engine.logging import get_logger

logger = get_logger("Stats")


class StatsManager:
    """
    Manages persistent usage statistics with atomic writes and thread safety.
    """

    SCHEMA_VERSION = 1

    def __init__(self, stats_file_path: Optional[Path] = None):
        if stats_file_path is None:
            # Default to AppData/Roaming/ParrotInk/stats.json
            app_data = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming")))
            self.file_path = app_data / "ParrotInk" / "stats.json"
        else:
            self.file_path = stats_file_path

        self._lock = threading.Lock()
        self._stats = self._get_default_stats()
        self._ensure_dir()
        self.load()

    def _ensure_dir(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_default_stats(self) -> Dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "lifetime": {
                "total_transcriptions": 0,
                "total_duration_seconds": 0,
                "total_words": 0,
                "error_count": 0,
                "provider_usage": {},
            },
            "history": [],  # Individual session records for Daily/Monthly rollup
        }

    def load(self):
        """Loads stats from disk with corruption recovery."""
        with self._lock:
            if not self.file_path.exists():
                return

            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("schema_version") == self.SCHEMA_VERSION:
                        self._stats = data
                    else:
                        v = data.get("schema_version")
                        logger.warning(
                            f"Stats schema mismatch. Expected {self.SCHEMA_VERSION}, got {v}"
                        )
                        # Future: Handle migrations here
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Failed to load stats (corrupted): {e}")
                self._handle_corruption()

    def _handle_corruption(self):
        """Backs up corrupted file and resets stats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupt_path = self.file_path.with_suffix(f".json.corrupt.{timestamp}")
        try:
            if self.file_path.exists():
                os.replace(self.file_path, corrupt_path)
                logger.info(f"Corrupted stats file moved to {corrupt_path}")
        except Exception as e:
            logger.error(f"Failed to move corrupted stats file: {e}")
        self._stats = self._get_default_stats()

    def save(self):
        """Atomically saves stats to disk."""
        with self._lock:
            tmp_path = self.file_path.with_suffix(".tmp")
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(self._stats, f, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, self.file_path)
            except Exception as e:
                logger.error(f"Failed to save stats: {e}")
                if tmp_path.exists():
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    def record_session(
        self, duration_seconds: float, words: int, provider: str, error: bool = False
    ):
        """Records a single transcription session."""
        with self._lock:
            # 1. Update Lifetime
            lt = self._stats["lifetime"]
            if error:
                lt["error_count"] += 1
            else:
                lt["total_transcriptions"] += 1
                lt["total_duration_seconds"] += duration_seconds
                lt["total_words"] += words

                # Provider Usage
                lt["provider_usage"][provider] = lt["provider_usage"].get(provider, 0) + 1

            # 2. Add to history for daily/monthly rollup
            self._stats["history"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration_seconds,
                    "words": words,
                    "provider": provider,
                    "error": error,
                }
            )

            # 3. Trim history (Optional: keep only last 90 days if file gets too big)
            # For now, we'll keep it simple as requested.

    def get_report(self) -> Dict[str, Any]:
        """Returns a snapshot of the current stats with daily/weekly/monthly aggregations."""
        with self._lock:
            import copy

            stats = copy.deepcopy(self._stats)

            # Initialize buckets
            today_stats = self._get_empty_bucket()
            week_stats = self._get_empty_bucket()
            month_stats = self._get_empty_bucket()

            now = datetime.now()
            today_str = now.date().isoformat()
            month_str = now.strftime("%Y-%m")
            # ISO year, week number
            week_key = now.isocalendar()[:2]

            for entry in stats.get("history", []):
                try:
                    entry_dt = datetime.fromisoformat(entry["timestamp"])
                    entry_date_str = entry_dt.date().isoformat()
                    entry_month_str = entry_dt.strftime("%Y-%m")
                    entry_week_key = entry_dt.isocalendar()[:2]

                    is_error = entry.get("error", False)
                    duration = entry.get("duration", 0)
                    words = entry.get("words", 0)
                    provider = entry.get("provider", "unknown")

                    # Aggregate Today
                    if entry_date_str == today_str:
                        self._update_bucket(today_stats, is_error, duration, words, provider)

                    # Aggregate This Week
                    if entry_week_key == week_key:
                        self._update_bucket(week_stats, is_error, duration, words, provider)

                    # Aggregate This Month
                    if entry_month_str == month_str:
                        self._update_bucket(month_stats, is_error, duration, words, provider)
                except Exception as e:
                    logger.error(f"Error aggregating stat entry: {e}")
                    continue

            stats["today"] = today_stats
            stats["this_week"] = week_stats
            stats["this_month"] = month_stats
            return stats

    def _get_empty_bucket(self) -> Dict[str, Any]:
        return {
            "total_transcriptions": 0,
            "total_duration_seconds": 0,
            "total_words": 0,
            "error_count": 0,
            "provider_usage": {},
        }

    def _update_bucket(
        self,
        bucket: Dict[str, Any],
        error: bool,
        duration: float,
        words: int,
        provider: str,
    ):
        if error:
            bucket["error_count"] += 1
        else:
            bucket["total_transcriptions"] += 1
            bucket["total_duration_seconds"] += duration
            bucket["total_words"] += words
            bucket["provider_usage"][provider] = bucket["provider_usage"].get(provider, 0) + 1
