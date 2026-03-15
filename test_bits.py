import subprocess
import logging

def test_bits():
    ps_command = 'Start-BitsTransfer -Source "https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk-Setup.exe" -Destination "C:\\Users\\alwat\\AppData\\Local\\Temp\\ParrotInk-Setup-v0.2.28.exe" -DisplayName "ParrotInk Update" -Asynchronous -Priority Normal'
    try:
        result = subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
        print("Success:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr.decode())

test_bits()
