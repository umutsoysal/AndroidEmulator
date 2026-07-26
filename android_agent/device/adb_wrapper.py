"""
Wrapper module for low-level Android Debug Bridge (ADB) operations.
"""

import io
import os
import shutil
import subprocess
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
        """Finds adb binary location on SDK paths, environment variables, or system PATH."""
        system_adb = shutil.which("adb")
        if system_adb:
            return system_adb

        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "Library", "Android", "sdk", "platform-tools", "adb"),
            os.path.join(home, "Android", "Sdk", "platform-tools", "adb"),
        ]

        android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if android_home:
            candidates.insert(0, os.path.join(android_home, "platform-tools", "adb"))

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

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
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
            if res.returncode != 0 and res.stderr:
                logger.debug("ADB command %s failed: %s", " ".join(cmd), res.stderr.strip())
            return res
        except subprocess.TimeoutExpired:
            logger.error("ADB command %s timed out after %ds", " ".join(cmd), timeout)
            raise

    def get_devices(self) -> List[Tuple[str, str]]:
        """Returns list of (serial, status) tuples for attached ADB devices."""
        cmd = [self.adb_path, "devices"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
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

        res = subprocess.run(cmd, capture_output=True, check=False)
        if res.returncode != 0 or not res.stdout:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"Failed to capture screencap: {err_msg}")

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
        logger.info("ADB Tap: (%d, %d)", x, y)
        self.execute(["shell", "input", "tap", str(x), str(y)])

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        """Simulates a touch drag/swipe from (x1, y1) to (x2, y2)."""
        logger.info("ADB Swipe: (%d, %d) -> (%d, %d) [%dms]", x1, y1, x2, y2, duration_ms)
        self.execute(
            ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)]
        )

    def type_text(self, text: str):
        """Inputs string into focused text field. Escapes special characters for adb shell."""
        logger.info("ADB Type text: %r", text)
        escaped_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        self.execute(["shell", "input", "text", escaped_text])

    def press_key(self, keycode: str):
        """Presses hardware key (HOME, BACK, ENTER, APP_SWITCH, etc.)."""
        logger.info("ADB Press Key: %s", keycode)
        code = self.KEYCODES.get(keycode.upper())
        if code is not None:
            self.execute(["shell", "input", "keyevent", str(code)])
        else:
            try:
                self.execute(["shell", "input", "keyevent", str(int(keycode))])
            except ValueError:
                logger.error("Unknown keycode: %s", keycode)

    def launch_app(self, package_or_activity: str):
        """Launches an app by package name or component activity."""
        logger.info("ADB Launch app: %s", package_or_activity)
        if "/" in package_or_activity:
            self.execute(["shell", "am", "start", "-n", package_or_activity])
        else:
            self.execute([
                "shell", "monkey", "-p", package_or_activity,
                "-c", "android.intent.category.LAUNCHER", "1"
            ])

    def stop_app(self, package_name: str):
        """Force stops an app package."""
        logger.info("ADB Stop app: %s", package_name)
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
