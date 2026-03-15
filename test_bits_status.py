import subprocess

class BITSClient:
    JOB_NAME = "ParrotInk Update Test"

    def start_download(self, url: str, dest_path: str) -> bool:
        ps_command = (
            f'Start-BitsTransfer -Source "{url}" -Destination "{dest_path}" '
            f'-DisplayName "{self.JOB_NAME}" -Asynchronous -Priority Normal'
        )
        try:
            result = subprocess.run(["powershell", "-Command", ps_command], check=True, capture_output=True)
            print("Start success")
            return True
        except subprocess.CalledProcessError as e:
            print("Start error:", e.stderr.decode())
            return False

    def get_status(self) -> dict:
        ps_command = (
            f'Get-BitsTransfer -Name "{self.JOB_NAME}" | '
            "Select-Object JobState, BytesTransferred, TotalBytesToTransfer | "
            "ForEach-Object { 'JobState=' + $_.JobState + ';BytesTransferred=' + "
            "$_.BytesTransferred + ';TotalBytesToTransfer=' + $_.TotalBytesToTransfer }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True,
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()
            if not output:
                return {"state": "NotFound", "percent": 0, "is_complete": False}

            # If there are multiple jobs, just take the first one
            first_job = output.splitlines()[0].strip()

            # Parse simple semicolon-delimited output
            data = {}
            for item in first_job.split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    data[k] = v

            state = data.get("JobState", "Unknown")
            transferred_str = data.get("BytesTransferred", "0").strip()
            total_str = data.get("TotalBytesToTransfer", "0").strip()
            
            transferred = int(transferred_str) if transferred_str else 0
            total = int(total_str) if total_str else 0

            percent = 0
            if total > 0:
                percent = int((transferred / total) * 100)
            elif state == "Transferred":
                percent = 100

            return {
                "state": state,
                "percent": percent,
                "is_complete": state == "Transferred",
            }
        except subprocess.CalledProcessError as e:
            # If the job is missing, Get-BitsTransfer outputs an error about not finding it
            err_msg = e.stderr.decode()
            if "Cannot find a BITS transfer" in err_msg:
                return {"state": "NotFound", "percent": 0, "is_complete": False}
            return {"state": "Error", "percent": 0, "is_complete": False, "error": err_msg}
        except Exception as e:
            return {"state": "Error", "percent": 0, "is_complete": False, "error": str(e)}

import time
client = BITSClient()
client.start_download("https://github.com/Aalwattar/ParrotInk/releases/download/v0.2.28/ParrotInk-Setup.exe", "C:\\Users\\alwat\\AppData\\Local\\Temp\\ParrotInk-Setup-v0.2.28.exe")
time.sleep(1)
print(client.get_status())
