# Android GUI Automation Agent

An autonomous AI Agent that operates on Android emulators or physical Android smartphones. Powered by **Gemini Multimodal Vision** and **Android Debug Bridge (ADB)**, the agent interacts with Android applications directly through GUI inputs (clicking, typing, swiping, hardware keys) without requiring application source code or dedicated APIs.

---

## Key Features

- **Multimodal Visual & UI Tree Perception**: Combines screen images with parsed `uiautomator` XML element bounding boxes for high-accuracy element targeting.
- **Universal App Support**: Interacts with any Android app (third-party, banking, system settings, messaging, custom internal apps) using user credentials already signed in on the phone or emulator.
- **ADB & Emulator Support**: Works with standard Android Virtual Devices (AVDs) or real physical Android phones via USB or Wi-Fi ADB.
- **Structured Action Decisions**: Employs Pydantic schemas to output deterministic actions (`TAP_ELEMENT`, `TAP_COORDINATE`, `TYPE_TEXT`, `SWIPE`, `PRESS_KEY`, `LAUNCH_APP`, `FINISH`).
- **Visual Debugging**: Automatically generates annotated screenshot images with numbered bounding box badges.

---

## Architecture Overview

```
                               ┌──────────────────────────┐
                               │       User Goal          │
                               └────────────┬─────────────┘
                                            │
                                            ▼
┌──────────────────┐             ┌────────────────────────┐
│  Android Device  │ screencap & │      AndroidAgent      │
│  / Emulator      │ dump_xml    │   Perception & Loop    │
└────────┬─────────┘────────────►└──────────┬─────────────┘
         ▲                                  │
         │                                  │ Screenshot + UI Tree
         │ ADB Commands                     ▼
         │ (tap, swipe, text, key) ┌────────────────────────┐
         └─────────────────────────┤  Gemini 2.5 Multimodal │
                                   └────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.10+
- Android SDK / ADB installed (e.g. at `~/Library/Android/sdk/platform-tools/adb` or available in `PATH`)
- A valid `GEMINI_API_KEY` (Get one from [Google AI Studio](https://aistudio.google.com/app/api-keys))

### Setup Environment

```bash
# Clone or navigate to the repository
cd AndroidEmulator

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and package in editable mode
pip install -r requirements.txt
pip install -e .

# Export your Gemini API key
export GEMINI_API_KEY="your-gemini-api-key"
```

---

## CLI Usage

The package provides the `android-agent` CLI tool:

### 1. List Attached Devices & Emulators

```bash
# List online ADB devices / connected phones / running emulators
android-agent devices

# List available Android Virtual Devices (AVDs)
android-agent emulators
```

### 2. Launch an Emulator

```bash
android-agent start-emulator --name Pixel_3a_API_34
```

### 3. Capture & Inspect Screen Layout

```bash
# Dump parsed UI hierarchy elements
android-agent dump-ui

# Capture screenshot with visual bounding box badges
android-agent screenshot --output screen_annotated.png --annotate
```

### 4. Run Autonomous AI Agent Tasks

```bash
# Run a task on connected device/emulator
android-agent run --task "Open Settings and navigate to Display settings"

# Specify a target device serial number or model
android-agent run --task "Open Calculator and compute 125 * 8" --serial emulator-5554
```

---

## Python API Usage

```python
from android_agent import AndroidAgent, ADBWrapper

# 1. Initialize ADB connection
adb = ADBWrapper()

# 2. Instantiate agent
agent = AndroidAgent(
    model_name="gemini-2.5-flash"
)

# 3. Run autonomous task loop
result = agent.run_task(
    task="Open Settings and turn on Dark Mode",
    max_steps=10
)

print("Agent finished:", result)
```

---

## Directory Structure

```
AndroidEmulator/
├── requirements.txt
├── pyproject.toml
├── demo_agent.py               # Sample script
├── README.md
└── android_agent/
    ├── __init__.py
    ├── cli.py                  # Command-line interface
    ├── device/                 # ADB & Emulator control layer
    │   ├── adb_wrapper.py      # Low-level adb commands (screencap, tap, swipe, keyevent)
    │   ├── emulator_manager.py # AVD management
    │   └── ui_parser.py        # XML UI hierarchy parser & element bound calculator
    ├── agent/                  # Multimodal agent logic
    │   ├── actions.py          # Action schemas (Tap, Type, Swipe, PressKey, LaunchApp)
    │   ├── prompts.py          # System prompts
    │   └── core.py             # Main perception-reasoning-action execution loop
    └── utils/                  # Visualizer and logging utilities
        ├── visualizer.py       # Draws numbered bounding boxes on screenshots
        └── logger.py           # Structured console logging
```

---

## License

MIT
