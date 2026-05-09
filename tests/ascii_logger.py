import msvcrt
import sys
import time


def start_logger():
    print("=== ParrotInk ASCII Logger ===")
    print("1. Keep this terminal focused.")
    print("2. Start talking to ParrotInk.")
    print("3. Every character/key received will be logged below.")
    print("4. Press Ctrl+C when finished to save the report.")
    print("-" * 30)

    log_entries = []

    try:
        while True:
            if msvcrt.kbhit():
                # Get the raw byte
                char_byte = msvcrt.getch()

                # Handle special Windows keys (which start with 0x00 or 0xE0)
                if char_byte in (b"\x00", b"\xe0"):
                    next_byte = msvcrt.getch()
                    raw_hex = char_byte.hex() + next_byte.hex()
                    desc = "Special/Function Key"
                else:
                    raw_hex = char_byte.hex()
                    val = ord(char_byte)
                    if 32 <= val <= 126:
                        desc = f"'{char_byte.decode('ascii')}'"
                    elif val == 13:
                        desc = "CR (Carriage Return / Enter)"
                    elif val == 10:
                        desc = "LF (Line Feed)"
                    elif val == 8:
                        desc = "Backspace"
                    elif val == 9:
                        desc = "Tab"
                    else:
                        desc = "Control Char"

                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] HEX: {raw_hex.upper()} | {desc}")
                log_entries.append(f"{timestamp} | {raw_hex.upper()} | {desc}")

    except KeyboardInterrupt:
        print("\nStopping...")
        with open("raw_ascii_output.log", "w") as f:
            f.write("\n".join(log_entries))
        print(f"Full log saved to: {sys.path[0]}\\raw_ascii_output.log")


if __name__ == "__main__":
    start_logger()
