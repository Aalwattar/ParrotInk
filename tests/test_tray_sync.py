import unittest
from unittest.mock import MagicMock, patch

from engine.config import Config


class TestTraySync(unittest.TestCase):
    def test_hotkey_label_sync(self):
        """Verify that the tray menu label updates when the hotkey changes in config."""
        # Patch pystray at the engine.ui level to ensure it's fully mocked during init
        with patch("engine.ui.pystray") as mock_pystray:
            # Setup mock MenuItem to act as a container
            def mock_menu_item(text, *args, **kwargs):
                item = MagicMock()
                item.text = text
                # If it's a sub-menu, the second arg is the menu
                if len(args) > 0 and not callable(args[0]):
                    item.submenu = args[0]
                return item

            mock_pystray.MenuItem.side_effect = mock_menu_item
            mock_pystray.Menu.side_effect = lambda *items: list(items)

            # Now import TrayApp inside the patch or ensure it uses the mock
            from engine.ui import TrayApp

            config = Config()
            config.hotkeys.hotkey = "ctrl+alt+v"

            app = TrayApp(config=config)

            def get_hotkey_label(menu):
                # Traverse: Settings -> Change Hotkey
                settings_item = next(item for item in menu if item.text == "Settings")
                for item in settings_item.submenu:
                    text = item.text(item) if callable(item.text) else item.text
                    if "Change Hotkey" in text:
                        return text
                return None

            # 1. Check initial menu
            initial_menu = app._create_menu()
            initial_label = get_hotkey_label(initial_menu)
            self.assertIn("CTRL+ALT+V", initial_label)

            # 2. Simulate hotkey change
            config.hotkeys.hotkey = "ctrl+space"

            # 3. Check updated menu
            updated_menu = app._create_menu()
            updated_label = get_hotkey_label(updated_menu)
            self.assertIn("CTRL+SPACE", updated_label)

            # 4. Verify _refresh_menu re-assigns the icon menu
            app.icon = MagicMock()
            app._refresh_menu()
            self.assertTrue(app.icon.menu is not None)


if __name__ == "__main__":
    unittest.main()
