import os
import signal
import subprocess
import sys
import time


def test_shutdown_crash():
    """
    Attempts to reproduce the 'Fatal Python error' by starting the app
    and sending SIGINT shortly after.
    """
    print("Starting ParrotInk for shutdown test...")
    # Start the app in a subprocess
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags,
    )

    # Wait for it to start up
    time.sleep(5)

    print("Sending CTRL_C_EVENT (Ctrl+C)...")
    if os.name == "nt":
        # Windows requires creation_flags to handle signals properly in sub-processes
        # but for a simple kill/term we can just use process.terminate()
        # and see if it triggers the same crash.
        # Actually, let's use send_signal(signal.CTRL_C_EVENT)
        process.send_signal(signal.CTRL_C_EVENT)
    else:
        process.send_signal(signal.SIGINT)

    try:
        stdout, stderr = process.communicate(timeout=10)
        print("STDOUT:", stdout)
        print("STDERR:", stderr)

        if "_enter_buffered_busy" in stderr or "Fatal Python error" in stderr:
            print("\n!!! REPRODUCED CRASH !!!")
            return True
        else:
            print("\nShutdown appeared clean.")
            return False

    except subprocess.TimeoutExpired:
        print("Process timed out during shutdown. Killing.")
        process.kill()
        return False


if __name__ == "__main__":
    repro = test_shutdown_crash()
    sys.exit(1 if repro else 0)
