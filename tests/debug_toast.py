import time

from win11toast import toast

print("Testing win11toast...")
try:
    toast(
        title="ParrotInk Test",
        body="If you see this, win11toast is working!",
        app_id="ParrotInk Test",
    )
    print("Toast triggered. Check your Windows notifications.")
    time.sleep(5)
except Exception as e:
    print(f"Error: {e}")
