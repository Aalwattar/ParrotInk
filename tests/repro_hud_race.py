import threading
import unittest
from unittest.mock import MagicMock, patch

from engine.config import Config
from engine.ui import TrayApp


class TestHudRace(unittest.TestCase):
    def test_ensure_indicator_race(self):
        config = Config()
        config.ui.floating_indicator.enabled = True

        # We patch IndicatorWindow where it is DEFINED
        with patch("engine.indicator_ui.IndicatorWindow") as mock_indicator:
            # Setup the mock instance
            mock_inst = MagicMock()
            mock_inst.is_healthy.return_value = True
            mock_indicator.return_value = mock_inst

            # Initialize app
            # We must also mock building the tray menu as it depends on more icons/assets
            with patch("engine.ui.build_tray_menu"), patch("engine.ui.TrayApp._create_icon"):
                app = TrayApp(config=config)

                # Reset mock to clear __init__ call
                mock_indicator.reset_mock()

                # Try to trigger race by calling _ensure_indicator from multiple threads
                # We nullify the existing indicator to force creation
                app.indicator = None

                def call_ensure():
                    for _ in range(50):
                        app._ensure_indicator()

                threads = []
                for _ in range(10):
                    t = threading.Thread(target=call_ensure)
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

                # IndicatorWindow should have been instantiated exactly ONCE despite 10 threads
                self.assertEqual(mock_indicator.call_count, 1)


if __name__ == "__main__":
    unittest.main()
