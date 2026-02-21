"""
Native Input Monitoring and Interaction Layer for Windows.
Coordinates low-level keyboard hooks and bridge events to the main thread.
"""

from __future__ import annotations

import ctypes
import queue
import threading
import time
from ctypes import wintypes
from typing import Callable, Optional, Set

from engine.constants import SESSION_QUIT_TIMEOUT, TOGGLE_DEBOUNCE_COOLDOWN
from engine.logging import get_logger

from .platform_win.keys import (
    HOOKPROC,
    INPUT,
    KBDLLHOOKSTRUCT,
    KEYBDINPUT,
    KEYEVENTF_KEYUP,
    LLKHF_EXTENDED,
    LLKHF_INJECTED,
    VK_CONTROL,
    VK_LCONTROL,
    VK_LMENU,
    VK_LSHIFT,
    VK_MENU,
    VK_RCONTROL,
    VK_RMENU,
    VK_RSHIFT,
    VK_SHIFT,
    WH_KEYBOARD_LL,
    WM_KEYDOWN,
    WM_KEYUP,
    WM_SYSKEYDOWN,
    WM_SYSKEYUP,
    InputUnion,
)

logger = get_logger("Interaction")

# Windows API Function Setup
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Define argtypes to prevent OverflowError on 64-bit Windows
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = wintypes.LPARAM  # LRESULT

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK

user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL

user32.GetKeyNameTextW.argtypes = [wintypes.LONG, wintypes.LPWSTR, ctypes.c_int]
user32.GetKeyNameTextW.restype = ctypes.c_int

# State Constants
STATE_IDLE = 0
STATE_DICTATING = 1


class Win32InputMonitor:
    """
    Native Win32 Keyboard Monitor using WH_KEYBOARD_LL.
    Resolves the 'Stale Hook' and 'Stuck Modifier' issues.
    """

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ):
        self._on_press_callback = on_press
        self._on_release_callback = on_release
        self._any_key_callback: Optional[Callable[[str], None]] = None
        self._is_any_key_enabled = False

        self._hotkey_str = ""
        self._hold_mode = False
        self._is_running = False
        self._state = STATE_IDLE
        self._last_event_ts = time.time()
        self._last_toggle_ts = 0.0  # Cooldown for toggle mode
        self._toggle_cooldown = TOGGLE_DEBOUNCE_COOLDOWN

        # Hook Management
        self._hook = None
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._stop_event = threading.Event()

        # Keyboard State
        self._hotkey_vk = 0
        self._modifier_vks: Set[int] = set()
        self._pressed_modifiers: Set[int] = set()
        self._lock = threading.Lock()

        # Event Queue for bridge back to AsyncIO/Main thread
        self._event_queue: queue.Queue = queue.Queue()

    def set_hotkey(self, hotkey_str: str, hold_mode: bool = False):
        """Parses hotkey string into VK codes and sets mode."""
        was_running = False
        with self._lock:
            if self._hotkey_str == hotkey_str and self._hold_mode == hold_mode:
                return
            self._hotkey_str = hotkey_str
            self._hold_mode = hold_mode
            was_running = self._is_running
            self._modifier_vks, self._hotkey_vk = self._parse_hotkey(hotkey_str)
            logger.debug(
                f"Hotkey Parsed: {hotkey_str} -> Modifiers: {self._modifier_vks}, "
                f"Main: {self._hotkey_vk}"
            )

        if was_running:
            self.restart()

    def _parse_hotkey(self, hotkey_str: str) -> tuple[Set[int], int]:
        """Maps hotkey names to Virtual Key codes."""
        parts = [p.strip().lower() for p in hotkey_str.split("+")]
        modifiers = set()
        main_key = 0

        # Mapping common names to VKs
        vk_map = {
            "ctrl": VK_CONTROL,
            "shift": VK_SHIFT,
            "alt": VK_MENU,
            "space": 0x20,
            "v": ord("V"),
            "k": ord("K"),
            "r": ord("R"),
            "z": ord("Z"),
        }

        for part in parts:
            vk = vk_map.get(part)
            if vk in (VK_CONTROL, VK_SHIFT, VK_MENU):
                modifiers.add(vk)
            elif vk:
                main_key = vk
            elif len(part) == 1:
                main_key = ord(part.upper())

        return modifiers, main_key

    def set_any_key_callback(self, callback: Callable[[str], None]):
        self._any_key_callback = callback

    def enable_any_key_monitoring(self, enabled: bool):
        self._is_any_key_enabled = enabled

    def reset_state(self):
        with self._lock:
            self._state = STATE_IDLE
            self._pressed_modifiers.clear()

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def hotkey(self) -> str:
        return self._hotkey_str

    @property
    def hold_mode(self) -> bool:
        return self._hold_mode

    def _release_stuck_modifiers(self):
        """Injects synthetic KEYUP to clear modifier state in focused apps."""
        for vk in list(self._pressed_modifiers):
            inp = INPUT(
                type=1,  # INPUT_KEYBOARD
                union=InputUnion(ki=KEYBDINPUT(wVk=vk, dwFlags=KEYEVENTF_KEYUP)),
            )
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            logger.debug(f"Released stuck modifier vk=0x{vk:02X}")

    def _get_key_name(self, vk: int, scan_code: int, is_extended: bool) -> str:
        """Retrieves a human-readable name for a VK code."""
        # 1. Check common overrides for consistency with hotkey parsing
        overrides = {
            VK_CONTROL: "ctrl",
            VK_SHIFT: "shift",
            VK_MENU: "alt",
            0x20: "space",
        }
        if vk in overrides:
            return overrides[vk]

        # 2. Use Win32 API for others
        l_param = (scan_code << 16) | (1 << 24 if is_extended else 0)
        buf = ctypes.create_unicode_buffer(32)
        if user32.GetKeyNameTextW(l_param, buf, 32) > 0:
            return buf.value.lower()

        return f"key_{vk}"

    def _ll_keyboard_handler(self, n_code, w_param, l_param):
        """Native Keyboard Hook Procedure."""
        if n_code < 0:
            return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

        kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk = kb.vkCode
        flags = kb.flags
        is_injected = bool(flags & LLKHF_INJECTED)
        is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
        is_up = w_param in (WM_KEYUP, WM_SYSKEYUP)

        self._last_event_ts = time.time()

        # 1. Skip synthetic/injected events to prevent recursion
        if is_injected:
            return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

        # 2. Track modifier state for chord detection
        modifier_keys = {
            VK_CONTROL,
            VK_LCONTROL,
            VK_RCONTROL,
            VK_SHIFT,
            VK_LSHIFT,
            VK_RSHIFT,
            VK_MENU,
            VK_LMENU,
            VK_RMENU,
        }

        # Mapping specific keys back to base modifiers for chord matching
        base_vk = vk
        if vk in (VK_LCONTROL, VK_RCONTROL):
            base_vk = VK_CONTROL
        elif vk in (VK_LSHIFT, VK_RSHIFT):
            base_vk = VK_SHIFT
        elif vk in (VK_LMENU, VK_RMENU):
            base_vk = VK_MENU

        if base_vk in modifier_keys:
            if is_down:
                self._pressed_modifiers.add(base_vk)
            elif is_up:
                self._pressed_modifiers.discard(base_vk)

        # 3. Chord Detection
        combo_fired = (
            is_down
            and base_vk == self._hotkey_vk
            and self._modifier_vks.issubset(self._pressed_modifiers)
        )

        # 4. State Machine Logic
        if not self._hold_mode:  # TOGGLE MODE
            if self._state == STATE_IDLE:
                if combo_fired:
                    # Debounce
                    now = time.time()
                    if now - self._last_toggle_ts < self._toggle_cooldown:
                        return 1  # Suppress jitter

                    self._last_toggle_ts = now
                    self._state = STATE_DICTATING
                    self._release_stuck_modifiers()
                    # We call the callback (bridge) later to keep hook thread fast
                    self._event_queue.put("start")
                    return 1  # Suppress

                # Idle: pass through everything
                return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

            else:  # STATE_DICTATING
                # Any KeyDown stops dictation (including modifiers)
                if is_down:
                    # 1. If it's the hotkey combo, trigger toggle stop (via start event)
                    if combo_fired:
                        self._event_queue.put("start")
                        return 1

                    # 2. If 'any key' is enabled, notify the coordinator
                    if self._is_any_key_enabled:
                        name = self._get_key_name(vk, kb.scanCode, bool(flags & LLKHF_EXTENDED))
                        self._event_queue.put(f"any_key:{name}")
                        return 1

                    return 1  # Suppress everything else while dictating

        else:  # HOLD MODE
            if self._state == STATE_IDLE:
                if combo_fired:
                    self._state = STATE_DICTATING
                    self._release_stuck_modifiers()
                    self._event_queue.put("start")
                    return 1  # Suppress

                return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

            else:  # STATE_DICTATING
                # Release of ANY part of the hotkey stops dictation
                if is_up and (base_vk == self._hotkey_vk or base_vk in self._modifier_vks):
                    self._state = STATE_IDLE
                    self._pressed_modifiers.discard(base_vk)
                    self._event_queue.put("stop")
                    return 1  # Suppress the KEYUP

                return 1  # Suppress all keys during dictation

        return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

    def _hook_loop(self):
        """Owner thread for the Low-Level Keyboard Hook."""
        self._thread_id = kernel32.GetCurrentThreadId()

        # CRITICAL: Hook MUST be installed on the thread that runs the loop
        self._hook_proc = HOOKPROC(self._ll_keyboard_handler)
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._hook_proc, None, 0)

        if not self._hook:
            err = kernel32.GetLastError()
            logger.error(f"Failed to install native WH_KEYBOARD_LL hook. Error: {err}")
            return

        logger.debug(f"Native hook installed. Thread ID: {self._thread_id}")

        # Start the queue polling sidecar thread for callbacks
        threading.Thread(target=self._poll_events, name="HookCallbackThread", daemon=True).start()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # Cleanup
        user32.UnhookWindowsHookEx(self._hook)
        self._hook = None
        logger.debug("Native hook uninstalled.")

    def _poll_events(self):
        """Bridges hook events back to the coordinator callbacks."""
        while self._is_running:
            try:
                event = self._event_queue.get(timeout=0.1)
                if event == "start":
                    self._on_press_callback()
                elif event == "stop":
                    self._on_release_callback()
                elif isinstance(event, str) and event.startswith("any_key:"):
                    if self._any_key_callback:
                        self._any_key_callback(event.split(":", 1)[1])
            except queue.Empty:
                continue

    def start(self):
        """Launches the dedicated hook thread."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._hook_loop, name="Win32HookThread", daemon=False
        )
        self._thread.start()

    def stop(self):
        """Stops the hook and joins the thread."""
        with self._lock:
            if not self._is_running:
                return
            self._is_running = False

        if self._thread_id:
            logger.debug("Posting WM_QUIT to hook thread...")
            user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT
            if self._thread:
                self._thread.join(timeout=SESSION_QUIT_TIMEOUT)
            self._thread_id = None

        # Final cleanup for the queue
        self._event_queue.put(None)

    def restart(self):
        """Native restart for desktop recovery or watchdog recovery."""
        self.stop()
        self.reset_state()
        self.start()


# For Backward Compatibility during the transition
InputMonitor = Win32InputMonitor
