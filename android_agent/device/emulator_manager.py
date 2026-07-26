"""
Manager module for listing and launching Android Virtual Devices (AVDs).
"""

import os
import shutil
import subprocess

from ..utils.logger import logger


class EmulatorManager:
    """Manages Android Virtual Device (AVD) lifecycle."""

    def __init__(self, emulator_path: str | None = None):
        self.emulator_path = emulator_path or self._find_emulator()

    def _find_emulator(self) -> str:
        """Finds path to emulator binary on SDK paths, environment variables, or system PATH."""
        system_emulator = shutil.which("emulator")
        if system_emulator:
            return system_emulator

        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "Library", "Android", "sdk", "emulator", "emulator"),
            os.path.join(home, "Android", "Sdk", "emulator", "emulator"),
        ]

        android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if android_home:
            candidates.insert(0, os.path.join(android_home, "emulator", "emulator"))

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        return "emulator"

    def list_avds(self) -> list[str]:
        """Lists available Android Virtual Device names."""
        try:
            res = subprocess.run(
                [self.emulator_path, "-list-avds"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if res.returncode == 0:
                return [line.strip() for line in res.stdout.splitlines() if line.strip()]
        except (subprocess.SubprocessError, OSError) as e:
            logger.error("Failed to list AVDs: %s", e)
        return []

    def start_emulator(self, avd_name: str, headless: bool = False) -> subprocess.Popen:
        """Launches an emulator process asynchronously."""
        cmd = [self.emulator_path, "-avd", avd_name]
        if headless:
            cmd.append("-no-window")

        logger.info("Starting emulator '%s' (headless=%s)...", avd_name, headless)
        # pylint: disable=consider-using-with
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return process
