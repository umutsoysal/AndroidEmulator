import os
import shutil
import subprocess
import time
import io
from typing import List, Optional, Tuple
from PIL import Image
from ..utils.logger import logger

class ADBWrapper:
    """Wrapper for low-level Android Debug Bridge (ADB) operations."""
    
    KEYCODES = {
        "HOME": 3,
        "BACK": 4,
        "ENTER": 66,
        "DELETE": 67,
        "TAB": 61,
        "APP_SWITCH": 187,
        "POWER": 26,
        "VOLUME_UP": 24,
        "VOLUME_DOWN": 25,
    }

    def __init__(self, serial: Optional[str] = None, adb_path: Optional[str] = None):
        self.adb_path = adb_path or self._find_adb()
        self.serial = serial or self._get_default_device()

    def _find_adb(self) -> str:
        """Finds adb binary location on standard SDK paths or PATH."""
        custom_sdk_path = "/Users/umutsoysal/Library/Android/sdk/platform-tools/adb"
        if os.path.exists(custom_sdk_path):
            return custom_sdk_path
        
        system_adb = shutil.which("adb")
        if system_adb:
            return system_adb
            
        home = os.path.expanduser("~")
        mac_sdk = os.path.join(home, "Library", "Android", "sdk", "platform-tools", "adb")
        if os.path.exists(mac_sdk):
            return mac_sdk

        return "adb"

    def _get_default_device(self) -> Optional[str]:
        """Gets the serial of the first connected online device or emulator."""
        devices = self.get_devices()
        if devices:
            return devices[0][0]
        return None

    def execute(self, args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Executes an adb command line."""
        cmd = [self.adb_path]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if res.returncode != 0 and res.stderr:
                logger.debug(f"ADB command {' '.join(cmd)} failed: {res.stderr.strip()}")
            return res
        except subprocess.TimeoutExpired:
            logger.error(f"ADB command {' '.join(cmd)} timed out after {timeout}s")
            raise

    def get_devices(self) -> List[Tuple[str, str]]:
        """Returns list of (serial, status) tuples for attached ADB devices."""
        cmd = [self.adb_path, "devices"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        devices = []
        for line in res.stdout.strip().splitlines()[1:]:
            if "\t" in line:
                serial, state = line.split("\t")
                devices.append((serial, state))
        return devices

    def screencap(self) -> Image.Image:
        """Captures device screen as a PIL Image."""
        cmd = [self.adb_path]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(["exec-out", "screencap", "-p"])
        
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0 or not res.stdout:
            raise RuntimeError(f"Failed to capture screencap: {res.stderr.decode('utf-8', errors='ignore')}")
            
        return Image.open(io.BytesIO(res.stdout))

    def dump_hierarchy(self) -> str:
        """Dumps UI hierarchy XML string via uiautomator."""
        remote_path = "/sdcard/window_dump.xml"
        self.execute(["shell", "uiautomator", "dump", remote_path])
        res = self.execute(["shell", "cat", remote_path])
        if res.returncode == 0 and res.stdout:
            return res.stdout
        return ""

    def tap(self, x: int, y: int):
        """Simulates a single touch tap at (x, y)."""
        logger.info(f"ADB Tap: ({x}, {y})")
        self.execute(["shell", "input", "tap", str(x), str(y)])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        """Simulates a touch drag/swipe from (x1, y1) to (x2, y2)."""
        logger.info(f"ADB Swipe: ({x1}, {y1}) -> ({x2}, {y2}) [{duration_ms}ms]")
        self.execute(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)])

    def type_text(self, text: str):
        """Inputs string into focused text field. Escapes special characters for adb shell."""
        logger.info(f"ADB Type text: {repr(text)}")
        # Escaping spaces and special characters for adb shell input text
        escaped_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        self.execute(["shell", "input", "text", escaped_text])

    def press_key(self, keycode: str):
        """Presses hardware key (HOME, BACK, ENTER, APP_SWITCH, etc.)."""
        logger.info(f"ADB Press Key: {keycode}")
        code = self.KEYCODES.get(keycode.upper())
        if code is not None:
            self.execute(["shell", "input", "keyevent", str(code)])
        else:
            # Check if keycode is integer
            try:
                self.execute(["shell", "input", "keyevent", str(int(keycode))])
            except ValueError:
                logger.error(f"Unknown keycode: {keycode}")

    def launch_app(self, package_or_activity: str):
        """Launches an app by package name or component activity."""
        logger.info(f"ADB Launch app: {package_or_activity}")
        if "/" in package_or_activity:
            self.execute(["shell", "am", "start", "-n", package_or_activity])
        else:
            self.execute(["shell", "monkey", "-p", package_or_activity, "-c", "android.intent.category.LAUNCHER", "1"])

    def stop_app(self, package_name: str):
        """Force stops an app package."""
        logger.info(f"ADB Stop app: {package_name}")
        self.execute(["shell", "am", "force-stop", package_name])

    def list_packages(self, third_party_only: bool = True) -> List[str]:
        """Lists installed package names on device."""
        args = ["shell", "pm", "list", "packages"]
        if third_party_only:
            args.append("-3")
        res = self.execute(args)
        packages = []
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if line.startswith("package:"):
                    packages.append(line.replace("package:", "").strip())
        return packages
