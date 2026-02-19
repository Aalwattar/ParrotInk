import os
import signal
import subprocess
import time
import sys

def test_shutdown_crash_v2():
    """
    Verifies that the v2 architecture prevents the 'Fatal Python error'
    by cleanly joining non-daemon threads and closing logging.
    """
    print("Starting ParrotInk v2 for shutdown verification...")
    
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags
    )
    
    # Wait for the full stack to initialize (Hook thread, UI thread, Async loop)
    time.sleep(8)
    
    print("Sending CTRL_C_EVENT...")
    if os.name == "nt":
        process.send_signal(signal.CTRL_C_EVENT)
    else:
        process.send_signal(signal.SIGINT)
    
    try:
        stdout, stderr = process.communicate(timeout=15)
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        
        # Check for the specific fatal error string
        if "_enter_buffered_busy" in stderr or "Fatal Python error" in stderr:
            print("\n!!! FAILURE: Crash detected in v2 architecture !!!")
            return False
        
        print("\nSUCCESS: Shutdown was clean.")
        return True
            
    except subprocess.TimeoutExpired:
        print("Process timed out. Forcing kill.")
        process.kill()
        return False

if __name__ == "__main__":
    success = test_shutdown_crash_v2()
    sys.exit(0 if success else 1)
