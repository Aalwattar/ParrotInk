import unittest
from unittest.mock import patch

from engine.config import Config
from engine.ui import TrayApp


class TestTraySync(unittest.TestCase):
    def test_hotkey_label_sync(self):
        """Verify that the tray menu label updates when the hotkey changes in config."""
        config = Config()
        config.hotkeys.hotkey = "ctrl+alt+v"

        # We MUST mock pystray.Icon to avoid "Class already exists" errors in tests
        with patch("pystray.Icon") as mock_icon_class:
            mock_icon = mock_icon_class.return_value

            # Simple mock objects to simulate pystray structure
            class MockItem:
                def __init__(self, text, submenu=None, **kwargs):
                    self.text = text
                    self.submenu = submenu or []

            def create_mock_menu(*items):
                return list(items)

            # Patch pystray classes to return our simple mocks
            with (
                patch("pystray.Menu", side_effect=create_mock_menu),
                patch("pystray.MenuItem", side_effect=MockItem),
            ):
                # app = TrayApp(config=config) calls _create_icon, so it MUST be inside patch
                app = TrayApp(config=config)
                # TrayApp._create_icon calls _create_menu which now returns our list
                mock_icon.menu = app._create_menu()

            def get_hotkey_label():
                settings_item = next(item for item in mock_icon.menu if item.text == "Settings")
                for item in settings_item.submenu:
                    text = item.text(item) if callable(item.text) else item.text
                    if "Change Hotkey" in text:
                        return text
                return None

            initial_label = get_hotkey_label()
            self.assertIn("CTRL+ALT+V", initial_label)

            # Simulate a config change
            config.hotkeys.hotkey = "ctrl+space"

            # Manually trigger the handler in TrayApp
            with (
                patch("pystray.Menu", side_effect=create_mock_menu),
                patch("pystray.MenuItem", side_effect=MockItem),
            ):
                app._refresh_menu()

            # Since _refresh_menu sets self.icon.menu = self._create_menu()
            # and self.icon is our mock_icon:
            updated_label = get_hotkey_label()
            self.assertIn("CTRL+SPACE", updated_label)


if __name__ == "__main__":
    unittest.main()
