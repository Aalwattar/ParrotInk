import threading
import time
from engine.ui import TrayApp
from engine.config import load_config
from engine.ui_bridge import UIBridge

def test_tray_exit_repro():
    config = load_config()
    bridge = UIBridge()
    
    # We want to see if stop() from a DIFFERENT thread causes the crash
    # Main loop exited message usually comes from gui_main
    
    def on_quit():
        print("Quit callback triggered.")
        # Simulating the gui_main trigger_shutdown logic
        # Which eventually calls app.stop() from the main thread
        
    app = TrayApp(config, bridge, on_quit_callback=on_quit)
    
    # Run UI in its own thread as gui_main does
    ui_thread = threading.Thread(target=app.run, daemon=False)
    ui_thread.start()
    
    # Let it initialize
    time.sleep(2)
    
    print("Simulating exit call from MAIN thread...")
    app.stop()
    
    ui_thread.join(timeout=5)
    print("Test finished successfully.")

if __name__ == "__main__":
    test_tray_exit_repro()
