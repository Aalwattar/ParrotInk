import asyncio
import sys

import websockets


async def check_url(name, url):
    print(f"Checking {name} at {url}...")
    try:
        async with websockets.connect(url, open_timeout=2):
            print(f"  SUCCESS: Handshake complete for {name}")
            return True
    except Exception as e:
        print(f"  FAILED: Could not connect to {name}: {e}")
        return False


async def main():
    success = True
    if not await check_url("OpenAI Mock", "ws://127.0.0.1:8081"):
        success = False
    if not await check_url("AssemblyAI Mock", "ws://127.0.0.1:8082"):
        success = False

    if success:
        print("\nAll connections are healthy.")
        sys.exit(0)
    else:
        print("\nSome connections FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
