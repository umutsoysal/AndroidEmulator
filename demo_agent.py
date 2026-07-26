#!/usr/bin/env python3
"""
Sample script demonstrating how to run the Android AI Agent programmatically.
"""

import os
from android_agent import AndroidAgent, ADBWrapper, EmulatorManager


def main():
    """Main execution function for demo script."""
    print("=== Android AI Agent Demo ===")

    # 1. Check attached devices
    adb = ADBWrapper()
    devices = adb.get_devices()
    print(f"Connected devices: {devices}")

    if not devices:
        emu_mgr = EmulatorManager()
        avds = emu_mgr.list_avds()
        print(f"No active device found. Available AVDs: {avds}")
        if avds:
            print(f"Launching emulator '{avds[0]}'...")
            emu_mgr.start_emulator(avds[0])
            print("Waiting for emulator to boot up...")
        else:
            print("Please connect an Android phone with USB debugging or create an AVD.")
            return

    # 2. Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("Note: GEMINI_API_KEY is not set. Set it before running agent tasks.")

    # 3. Initialize Agent
    agent = AndroidAgent(model_name="gemini-flash-latest")

    # Example task
    result = agent.run_task("Open Settings and check Battery percentage", max_steps=10)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
