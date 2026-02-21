import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from engine.logging import get_logger
from engine.platform_win.paths import get_stats_path

logger = get_logger("Stats")


class StatsManager:
    """
    Manages persistent usage statistics with atomic writes and thread safety.
    Uses pre-aggregated buckets (Daily/Monthly/Lifetime) to ensure O(1) performance.

    Safety features:
    - Atomic writes via temporary files.
    - Automatic .bak backup before every write.
    - Periodic background flushing (debounced) to minimize disk wear.
    """

    SCHEMA_VERSION = 2
    DAILY_RETENTION_DAYS = 90
    SAVE_INTERVAL_SECONDS = 60

    def __init__(self, stats_file_path: Optional[Path] = None):
        if stats_file_path is None:
            self.file_path = Path(get_stats_path())
        else:
            self.file_path = stats_file_path

        self._lock = threading.Lock()
        self._stats = self._get_default_stats()
        self._dirty = False
        self._ensure_dir()

        # Background saving thread
        self._stop_event = threading.Event()
        self._save_thread: Optional[threading.Thread] = None

        self.load()
        self.start_background_saver()

    def _ensure_dir(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def start_background_saver(self):
        """Starts a daemon thread that flushes dirty stats periodically."""
        if self._save_thread and self._save_thread.is_alive():
            return

        def saver_loop():
            while not self._stop_event.wait(self.SAVE_INTERVAL_SECONDS):
                if self._dirty:
                    logger.debug("Background stats flush triggered.")
                    self.save()

        self._save_thread = threading.Thread(target=saver_loop, name="StatsSaver", daemon=True)
        self._save_thread.start()

    def stop(self):
        """Stops the background saver and performs a final flush."""
        self._stop_event.set()
        if self._dirty:
            logger.info("Final stats flush before shutdown.")
            self.save()

    def _get_default_stats(self) -> Dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "lifetime": self._get_empty_bucket(),
            "daily": {},  # "YYYY-MM-DD": bucket
            "monthly": {},  # "YYYY-MM": bucket
        }

    def _get_empty_bucket(self) -> Dict[str, Any]:
        return {
            "total_transcriptions": 0,
            "total_duration_seconds": 0,
            "total_words": 0,
            "error_count": 0,
            "provider_usage": {},
        }

    def load(self):
        """Loads stats from disk with corruption recovery and migration."""
        with self._lock:
            # Check for .bak if main file is missing or corrupt
            paths_to_try = [self.file_path, self.file_path.with_suffix(".json.bak")]

            loaded = False
            for path in paths_to_try:
                if not path.exists():
                    continue

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        version = data.get("schema_version", 0)

                        if version == self.SCHEMA_VERSION:
                            self._stats = data
                            loaded = True
                            break
                        elif version == 1:
                            logger.info(
                                f"Migrating stats from V1 (history) to V2 (buckets) from {path}..."
                            )
                            self._migrate_v1_to_v2(data)
                            self._dirty = True  # Trigger a save in the new format
                            loaded = True
                            break
                except (json.JSONDecodeError, Exception) as e:
                    logger.error(f"Failed to load stats from {path}: {e}")
                    continue

            if not loaded and self.file_path.exists():
                # Both main and bak failed, handle corruption
                self._handle_corruption()

    def _migrate_v1_to_v2(self, v1_data: Dict[str, Any]):
        """Converts V1 history log into V2 pre-aggregated buckets."""
        self._stats = self._get_default_stats()
        # Transfer lifetime
        self._stats["lifetime"] = v1_data.get("lifetime", self._get_empty_bucket())

        # Aggregate history into buckets
        for entry in v1_data.get("history", []):
            try:
                dt = datetime.fromisoformat(entry["timestamp"])
                day_key = dt.date().isoformat()
                month_key = dt.strftime("%Y-%m")

                is_error = entry.get("error", False)
                duration = entry.get("duration", 0)
                words = entry.get("words", 0)
                provider = entry.get("provider", "unknown")

                # Update Daily
                if day_key not in self._stats["daily"]:
                    self._stats["daily"][day_key] = self._get_empty_bucket()
                self._update_bucket(
                    self._stats["daily"][day_key], is_error, duration, words, provider
                )

                # Update Monthly
                if month_key not in self._stats["monthly"]:
                    self._stats["monthly"][month_key] = self._get_empty_bucket()
                self._update_bucket(
                    self._stats["monthly"][month_key], is_error, duration, words, provider
                )
            except Exception as e:
                logger.error(f"Migration error for entry: {e}")
                continue

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
        """Atomically saves stats to disk with a safety backup."""
        with self._lock:
            if not self._dirty and self.file_path.exists():
                return

            # 1. Create safety backup of existing file
            bak_path = self.file_path.with_suffix(".json.bak")
            if self.file_path.exists():
                try:
                    import shutil

                    shutil.copy2(self.file_path, bak_path)
                except Exception as e:
                    logger.warning(f"Could not create stats backup: {e}")

            # 2. Prune daily history before saving
            self._prune_daily_stats()

            # 3. Write new file atomically
            tmp_path = self.file_path.with_suffix(".tmp")
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(self._stats, f, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, self.file_path)
                self._dirty = False
            except Exception as e:
                logger.error(f"Failed to save stats: {e}")
                if tmp_path.exists():
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    def _prune_daily_stats(self):
        """Removes daily buckets older than retention period."""
        if "daily" not in self._stats:
            return

        now = datetime.now()
        keys_to_delete = []
        for day_key in self._stats["daily"].keys():
            try:
                dt = datetime.fromisoformat(day_key)
                if (now - dt).days > self.DAILY_RETENTION_DAYS:
                    keys_to_delete.append(day_key)
            except (ValueError, TypeError):
                continue

        for key in keys_to_delete:
            del self._stats["daily"][key]

    def record_session(
        self, duration_seconds: float, words: int, provider: str, error: bool = False
    ):
        """Records a single transcription session into memory and marks as dirty."""
        with self._lock:
            now = datetime.now()
            day_key = now.date().isoformat()
            month_key = now.strftime("%Y-%m")

            # 1. Update Lifetime
            self._update_bucket(self._stats["lifetime"], error, duration_seconds, words, provider)

            # 2. Update Daily
            if day_key not in self._stats["daily"]:
                self._stats["daily"][day_key] = self._get_empty_bucket()
            self._update_bucket(
                self._stats["daily"][day_key], error, duration_seconds, words, provider
            )

            # 3. Update Monthly
            if month_key not in self._stats["monthly"]:
                self._stats["monthly"][month_key] = self._get_empty_bucket()
            self._update_bucket(
                self._stats["monthly"][month_key], error, duration_seconds, words, provider
            )

            self._dirty = True

    def get_report(self) -> Dict[str, Any]:
        """Returns a snapshot of the current stats including active time windows."""
        with self._lock:
            import copy

            stats = copy.deepcopy(self._stats)

            now = datetime.now()
            today_key = now.date().isoformat()
            month_key = now.strftime("%Y-%m")

            # Helper to get week key (ISO Year, ISO Week)
            current_week = now.isocalendar()[:2]

            # Populate reports for UI
            stats["today"] = stats["daily"].get(today_key, self._get_empty_bucket())
            stats["this_month"] = stats["monthly"].get(month_key, self._get_empty_bucket())

            # Calculate "This Week" by summing recent days (since buckets are small)
            week_bucket = self._get_empty_bucket()
            for day_key, bucket in stats.get("daily", {}).items():
                try:
                    dt = datetime.fromisoformat(day_key)
                    if dt.isocalendar()[:2] == current_week:
                        self._merge_buckets(week_bucket, bucket)
                except ValueError:
                    continue

            stats["this_week"] = week_bucket
            return stats

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

    def _merge_buckets(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Sums source bucket into target bucket."""
        target["total_transcriptions"] += source.get("total_transcriptions", 0)
        target["total_duration_seconds"] += source.get("total_duration_seconds", 0)
        target["total_words"] += source.get("total_words", 0)
        target["error_count"] += source.get("error_count", 0)

        src_usage = source.get("provider_usage", {})
        for provider, count in src_usage.items():
            target["provider_usage"][provider] = target["provider_usage"].get(provider, 0) + count
