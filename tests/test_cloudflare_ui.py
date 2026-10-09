import json
import os
import subprocess
import sys

import pytest

from engine.cloudflare_ui import validate_gateway_settings


def test_valid_gateway_settings():
    assert validate_gateway_settings("a" * 32, "my-gateway", "@cf/deepgram/nova-3") is None


def test_invalid_gateway_settings():
    assert validate_gateway_settings("missing", "default", "@cf/deepgram/nova-3")
    assert validate_gateway_settings("a" * 32, "../other", "@cf/deepgram/nova-3")
    assert validate_gateway_settings("a" * 32, "default", "unknown")


def test_catalog_menu_callbacks_bind_each_model(mocker, config):
    from engine.ui import TrayApp
    from engine.ui_menu import build_tray_menu

    mocker.patch("engine.ui.pystray.Icon")
    mocker.patch.object(TrayApp, "_ensure_indicator")
    selected = mocker.Mock()
    settings = mocker.Mock()
    app = TrayApp(
        config,
        initial_provider="cloudflare",
        on_model_change=selected,
        on_cloudflare_settings=settings,
    )
    menu = list(build_tray_menu(app))
    transcription = next(item for item in menu if item.text.startswith("Transcription"))
    model_menu = next(item for item in transcription.submenu if item.text == "Model")
    models = list(model_menu.submenu)
    models[0](None)
    selected.assert_called_with("cloudflare", "@cf/deepgram/nova-3")
    models[1](None)
    selected.assert_called_with("cloudflare", "@cf/deepgram/flux")
    settings_menu = next(item for item in menu if item.text == "Settings")
    gateway = next(
        item for item in settings_menu.submenu if item.text == "Configure Cloudflare Gateway..."
    )
    assert gateway.enabled
    gateway(None)
    settings.assert_called_once()


@pytest.mark.parametrize(
    "provider,model,mic_enabled,speed_enabled",
    [
        ("assemblyai", "universal-3-6-pro", True, True),
        ("assemblyai", "universal-streaming-english", False, True),
        ("cloudflare", "@cf/deepgram/nova-3", False, False),
        ("cloudflare", "openai/gpt-live-transcribe", True, True),
    ],
)
def test_menu_controls_follow_model_capabilities(
    mocker, config, provider, model, mic_enabled, speed_enabled
):
    from engine.transcription.catalog import model_config_update
    from engine.ui import TrayApp
    from engine.ui_menu import build_tray_menu

    field, value = next(
        iter(model_config_update(provider, model)["providers"][provider]["core"].items())
    )
    setattr(getattr(config.providers, provider).core, field, value)
    mocker.patch("engine.ui.pystray.Icon")
    mocker.patch.object(TrayApp, "_ensure_indicator")
    app = TrayApp(config, initial_provider=provider)
    transcription = next(
        item for item in build_tray_menu(app) if item.text.startswith("Transcription")
    )
    controls = {item.text: item for item in transcription.submenu}
    assert controls["Microphone Profile"].enabled is mic_enabled
    assert controls["Transcription Speed"].enabled is speed_enabled
    if provider == "assemblyai" and model == "universal-3-6-pro":
        assert controls["Punctuation (automatic)"].checked
        assert not controls["Punctuation (automatic)"].enabled


@pytest.mark.parametrize("submit", [False, True])
@pytest.mark.skipif(
    os.getenv("RUN_DESKTOP_UI_TESTS") != "1",
    reason="Real desktop windows require an explicit opt-in",
)
def test_gateway_dialog_visible_with_withdrawn_tray_master(submit):
    """Use a fresh Tcl interpreter and the production after/mainloop path."""
    script = r"""
import json
import sys
import ttkbootstrap as tb
from engine.cloudflare_ui import ask_cloudflare_settings
from engine.config import Config

root = tb.Window(themename="darkly")
root.withdraw()
observed = {}

def inspect_and_close():
    dialog = next(child for child in root.winfo_children() if isinstance(child, tb.Toplevel))
    observed.update(state=dialog.state(), viewable=dialog.winfo_viewable(),
                    master_state=root.state())
    content = dialog.winfo_children()[0]
    fields = {child.grid_info().get("row"): child for child in content.winfo_children()
              if isinstance(child, tb.Entry)}
    observed["token_masked"] = fields[6].cget("show") == "*"
    if sys.argv[1] == "save":
        fields[2].delete(0, "end")
        fields[2].insert(0, "a" * 32)
        fields[6].insert(0, "synthetic-test-token")
        buttons = next(child for child in content.winfo_children()
                       if child.grid_info().get("row") == 10)
        next(child for child in buttons.winfo_children() if child.cget("text") == "Save").invoke()
    else:
        dialog.destroy()

def show():
    observed["result"] = ask_cloudflare_settings(root, Config())
    root.quit()

root.after(0, show)
root.after(300, inspect_and_close)
root.after(1500, root.destroy)
root.mainloop()
print(json.dumps(observed))
root.destroy()
"""
    process = subprocess.run(
        [sys.executable, "-c", script, "save" if submit else "cancel"],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    state = json.loads(process.stdout)
    assert state["state"] == "normal"
    assert state["viewable"] == 1
    assert state["master_state"] == "withdrawn"
    assert state["token_masked"]
    if submit:
        assert state["result"]["api_token"] == "synthetic-test-token"
        assert "api_token" not in state["result"]["core"]
    else:
        assert state["result"] is None


def test_gateway_dialog_never_grabs_desktop_input(mocker, config):
    from engine import cloudflare_ui

    parent = mocker.Mock()
    parent.winfo_viewable.return_value = False
    window = mocker.Mock()
    window.winfo_viewable.return_value = False
    window.winfo_exists.return_value = True
    window.winfo_screenwidth.return_value = 1920
    window.winfo_screenheight.return_value = 1080
    window.winfo_width.return_value = 600
    window.winfo_height.return_value = 400
    mocker.patch.object(cloudflare_ui.tb, "Toplevel", return_value=window)
    for widget in ("Frame", "Label", "Combobox", "Entry", "Checkbutton", "Button"):
        mocker.patch.object(cloudflare_ui.tb, widget)
    mocker.patch.object(cloudflare_ui.tk, "StringVar")
    mocker.patch.object(cloudflare_ui.tk, "BooleanVar")
    assert cloudflare_ui.ask_cloudflare_settings(parent, config) is None
    window.transient.assert_not_called()
    window.deiconify.assert_called_once()
    window.wait_visibility.assert_called_once()
    window.grab_set.assert_not_called()
    window.destroy.assert_called_once()
