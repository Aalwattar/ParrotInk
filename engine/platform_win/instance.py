import ctypes
from ctypes import wintypes
from typing import Optional

# Win32 Constants
ERROR_ALREADY_EXISTS = 183
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040

# DLLs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Function Signatures
CreateMutexW = kernel32.CreateMutexW
CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
CreateMutexW.restype = wintypes.HANDLE

GetLastError = kernel32.GetLastError
GetLastError.restype = wintypes.DWORD

MessageBoxW = user32.MessageBoxW
MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
MessageBoxW.restype = ctypes.c_int


class SingleInstance:
    """
    Ensures only one instance of the application runs at a time using a Win32 Mutex.
    """

    def __init__(self, mutex_name: str):
        self.mutex_name = mutex_name
        self.mutex_handle: Optional[wintypes.HANDLE] = None
        self._already_running = False

        # Create the mutex
        # Security attributes = None, Initial owner = True, Name = mutex_name
        self.mutex_handle = CreateMutexW(None, True, self.mutex_name)

        if not self.mutex_handle:
            # Handle creation failed (unlikely but possible)
            self._already_running = False
            return

        # Check if it already existed
        if GetLastError() == ERROR_ALREADY_EXISTS:
            self._already_running = True
        else:
            self._already_running = False

    @property
    def already_running(self) -> bool:
        return self._already_running

    def show_warning(self):
        """Shows a standard Win32 MessageBox indicating the app is already running."""
        from .paths import APP_NAME

        message = (
            f"{APP_NAME} is already running.\n\n"
            "Please check the system tray icon for the active instance."
        )
        MessageBoxW(
            None,
            message,
            APP_NAME,
            MB_OK | MB_ICONINFORMATION,
        )

    def __del__(self):
        # We generally want to hold the mutex for the life of the process,
        # but we should be tidy on normal cleanup.
        if self.mutex_handle:
            kernel32.CloseHandle(self.mutex_handle)
            self.mutex_handle = None
