from engine.onboarding_ui import show_onboarding_blocking


def test_onboarding_ui_import():
    """Verify that the onboarding UI module can be imported and the function exists."""
    assert callable(show_onboarding_blocking)


# We cannot easily test the blocking UI call in a non-interactive environment
# but we've verified the code structure.
