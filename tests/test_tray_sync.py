import unittest

from engine.config import Config
from engine.ui import TrayApp


class TestTraySync(unittest.TestCase):
    def test_hotkey_label_sync(self):
        """Verify that the tray menu label updates when the hotkey changes in config."""
        config = Config()
        config.hotkeys.hotkey = "ctrl+alt+v"

        # We need a real TrayApp but without the blocking run()
        app = TrayApp(config=config)

        def get_hotkey_label():
            # Traverse the menu to find the hotkey item
            # menu -> item(Settings) -> menu -> item(Change Hotkey)
            settings_item = next(item for item in app.icon.menu if item.text == "Settings")
            # The label is dynamic (lambda)
            for item in settings_item.submenu:
                text = item.text(item) if callable(item.text) else item.text
                if "Change Hotkey" in text:
                    return text
            return None

        initial_label = get_hotkey_label()
        self.assertIn("CTRL+ALT+V", initial_label)

        # Simulate a config change
        config.hotkeys.hotkey = "ctrl+space"

        # Manually trigger the handler in TrayApp (what we want to implement)
        # In a real app, UIBridge.update_settings triggers this.
        # We call the logic we are about to add.
        app._refresh_menu()

        updated_label = get_hotkey_label()
        self.assertIn("CTRL+SPACE", updated_label)


if __name__ == "__main__":
    unittest.main()
