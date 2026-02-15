import time
from typing import Dict, Set

def parse_hotkey(hotkey_str: str) -> Set[str]:
    parts = hotkey_str.lower().split("+")
    norm_map = {
        "ctrl": "ctrl",
        "control": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "win": "cmd",
        "cmd": "cmd",
    }
    return {norm_map.get(p.strip(), p.strip()) for p in parts if p.strip()}

class MockCoordinator:
    def __init__(self, hotkey_str: str):
        self.target_hotkey = parse_hotkey(hotkey_str)
        self.current_keys: Dict[str, float] = {}
        self.hotkey_pressed = False
        self.trigger_count = 0

    def on_press(self, name: str):
        now = time.time()
        
        # 1. First, evict REALLY stale keys and reset hotkey_pressed if needed
        # We do this BEFORE updating the current key's timestamp
        stale_keys = [k for k, ts in self.current_keys.items() if now - ts > 3.0]
        for k in stale_keys:
            print(f"Evicting stale key: {k}")
            self.current_keys.pop(k)

        if self.hotkey_pressed:
            all_stale = True
            for k in self.target_hotkey:
                ts = self.current_keys.get(k, 0)
                if now - ts <= 3.0:
                    all_stale = False
                    break
            if all_stale:
                print("Hotkey state reset (staleness)")
                self.hotkey_pressed = False

        # 2. Update current key
        self.current_keys[name] = now

        # 3. Check for match
        pressed_set = set(self.current_keys.keys())
        if pressed_set == self.target_hotkey:
            if not self.hotkey_pressed:
                self.hotkey_pressed = True
                self.trigger_count += 1
                print(f"HOTKEY TRIGGERED! Total: {self.trigger_count}")

    def on_release(self, name: str):
        if name in self.current_keys:
            self.current_keys.pop(name, None)
        
        if name in self.target_hotkey:
            if self.hotkey_pressed:
                self.hotkey_pressed = False
                print("Hotkey state reset (released)")

# Test Case 4: Missed Release of Hotkey
print("\n--- Test 4: Missed Release Recovery ---")
coord = MockCoordinator("ctrl+alt+space")
coord.on_press("ctrl")
coord.on_press("alt")
coord.on_press("space")
assert coord.trigger_count == 1
# Missed on_release for all!
time.sleep(3.1)
# Now try to press again
coord.on_press("ctrl")
coord.on_press("alt")
coord.on_press("space")
assert coord.trigger_count == 2
print("\nAll tests passed!")
