import os
import signal
import sys
import time


def handler(sig, frame):
    print("SUCCESS: Caught SIGINT!", flush=True)
    sys.exit(0)


signal.signal(signal.SIGINT, handler)
print("Waiting for SIGINT...", flush=True)

# Send SIGINT to self
os.kill(os.getpid(), signal.SIGINT)

# Keep alive for a moment
time.sleep(2)
print("FAILURE: Did not catch SIGINT.")
sys.exit(1)
