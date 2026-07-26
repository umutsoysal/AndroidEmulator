import os
import shutil
import subprocess
import time
from typing import List, Optional
from ..utils.logger import logger

class EmulatorManager:
    """Manages Android Virtual Device (AVD) lifecycle."""

    def __init__(self, emulator_path: Optional[str] = None):
        self.emulator_path = emulator_path or self._find_emulator()

    def _find_emulator(self) -> str:
        """Finds path to emulator binary."""
        custom_emulator = "/Users/umutsoysal/Library/Android/sdk/emulator/emulator"
        if os.path.exists(custom_emulator):
            return custom_emulator
        
        system_emulator = shutil.which("emulator")
        if system_emulator:
            return system_emulator
            
        home = os.path.expanduser("~")
        mac_emulator = os.path.join(home, "Library", "Android", "sdk", "emulator", "emulator")
        if os.path.exists(mac_emulator):
            return mac_emulator

        return "emulator"

    def list_avds(self) -> List[str]:
        """Lists available Android Virtual Device names."""
        try:
            res = subprocess.run([self.emulator_path, "-list-avds"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return [line.strip() for line in res.stdout.splitlines() if line.strip()]
        except Exception as e:
            logger.error(f"Failed to list AVDs: {e}")
        return []

    def start_emulator(self, avd_name: str, headless: bool = False) -> subprocess.Popen:
        """Launches an emulator process asynchronously."""
        cmd = [self.emulator_path, "-avd", avd_name]
        if headless:
            cmd.append("-no-window")
            
        logger.info(f"Starting emulator '{avd_name}' (headless={headless})...")
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return process
