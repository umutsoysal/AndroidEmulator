---
name: android-gui-agent
description: Autonomous GUI automation agent operating on Android emulators and physical Android devices using ADB and Gemini AI.
---

# Android GUI Automation Agent Skill

This skill provides instructions for running, debugging, and extending the `android-agent` tool in this codebase. The agent uses ADB and Gemini Multimodal vision to interact with Android applications on emulators or connected physical phones without needing app source code or dedicated APIs.

## Prerequisites

1. **ADB**: Android Debug Bridge must be available in PATH or at `~/Library/Android/sdk/platform-tools/adb`.
2. **Environment Setup**: Ensure the virtual environment is activated: `source .venv/bin/activate`.
3. **Gemini API Key**: Ensure `GEMINI_API_KEY` is set in environment or in `.env`.

## Key Commands

### 1. Device Management

- **List active ADB devices/emulators**:
  ```bash
  android-agent devices
  ```
- **List available Android Virtual Devices (AVDs)**:
  ```bash
  android-agent emulators
  ```
- **Start an emulator**:
  ```bash
  android-agent start-emulator --name Pixel_3a_API_34
  ```

### 2. UI Inspection & Debugging

- **Dump current interactive UI elements**:
  ```bash
  android-agent dump-ui
  ```
- **Capture screenshot with visual element badges**:
  ```bash
  android-agent screenshot --output screen.png --annotate
  ```

### 3. Running Autonomous Agent Tasks

- **Run task on default connected device**:
  ```bash
  android-agent run --task "Open Settings and click on Display"
  ```
- **Specify device serial or max steps**:
  ```bash
  android-agent run --task "Open Settings" --serial emulator-5554 --max-steps 20
  ```

## Programmatic Usage in Python

```python
from android_agent import AndroidAgent, ADBWrapper

# Initialize wrapper and agent
adb = ADBWrapper()
agent = AndroidAgent(model_name="gemini-flash-latest")

# Run task loop
result = agent.run_task(task="Open Settings and navigate to Display", max_steps=15)
print("Result:", result)
```

## Troubleshooting & Best Practices

- **429 Rate Limit**: If hit by API rate limits, the agent automatically retries with backoff.
- **Element Grounding**: Prefer using `TAP_ELEMENT` with the element's numeric `element_id` over raw coordinates whenever UI bounds are parsed.
- **Scroll Directions**: Note that `SWIPE` with direction `UP` scrolls down, while direction `DOWN` scrolls up.
