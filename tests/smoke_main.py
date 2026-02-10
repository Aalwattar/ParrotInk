import subprocess
import time
import sys
import os

def test_main_startup():
    print("Running main.py startup check...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    
    # Start main.py
    process = subprocess.Popen(
        ["uv", "run", "python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP # Needed for signal handling simulation if we were doing it
    )
    
    try:
        # If it's going to crash on init (like the AttributeError), it will happen immediately
        # We wait 5 seconds to be sure
        for i in range(5):
            time.sleep(1)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"main.py crashed with exit code {process.returncode}")
                print(f"STDERR:\n{stderr}")
                sys.exit(1)
        
        print("SUCCESS: main.py is running and didn't crash on startup.")
        process.terminate() # Graceful-ish on windows for subprocess
        
    except Exception as e:
        process.kill()
        print(f"Test runner error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_main_startup()