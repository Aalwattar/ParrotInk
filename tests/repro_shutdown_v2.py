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
        [sys.executable, "main.py", "-v"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=creationflags,
        encoding='utf-8',
        bufsize=1
    )
    
    # Wait for startup
    print("Waiting for startup (looking for 'Application running')...")
    start_ts = time.time()
    found_startup = False
    while True:
        if time.time() - start_ts > 20: # Increased timeout
            print("Startup timed out!")
            break
            
        line = process.stdout.readline()
        if line:
            print(f"MAIN: {line.strip()}")
            if "Application running" in line:
                found_startup = True
                break
        else:
            if process.poll() is not None:
                print(f"Process exited early with code {process.returncode}!")
                return False
            time.sleep(0.1)

    if not found_startup:
        print("Killing process due to startup failure...")
        process.kill()
        return False

    # Wait for monitors to settle
    time.sleep(3)
    
    print("Sending CTRL_BREAK_EVENT...")
    if os.name == "nt":
        # On Windows, sending CTRL_BREAK_EVENT is more reliable for process groups.
        os.kill(process.pid, signal.CTRL_BREAK_EVENT)
    else:
        process.send_signal(signal.SIGINT)
    
    try:
        combined_output, _ = process.communicate(timeout=15)
        print("OUTPUT:", combined_output)
        
        # Check for the specific fatal error string
        if combined_output and ("_enter_buffered_busy" in combined_output or "Fatal Python error" in combined_output):
            print("\n!!! FAILURE: Crash detected in v2 architecture !!!")
            return False
        
        print("\nSUCCESS: Shutdown was clean.")
        return True
            
    except subprocess.TimeoutExpired as e:
        print("Process timed out. Forcing kill.")
        if e.stdout: print("STDOUT (Partial):", e.stdout)
        if e.stderr: print("STDERR (Partial):", e.stderr)
        process.kill()
        return False

if __name__ == "__main__":
    success = test_shutdown_crash_v2()
    sys.exit(0 if success else 1)
