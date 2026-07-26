import os
import time
import json
from typing import List, Optional, Dict, Any
from google import genai
from google.genai import types

from ..device.adb_wrapper import ADBWrapper
from ..device.ui_parser import UIParser, UIElement
from ..utils.visualizer import draw_element_boxes
from ..utils.logger import logger
from .actions import AgentAction, ActionType
from .prompts import SYSTEM_PROMPT

class AndroidAgent:
    """Autonomous agent operating on an Android device via ADB and Gemini AI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-flash-latest",
        serial: Optional[str] = None,
        adb_wrapper: Optional[ADBWrapper] = None
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("[WARNING] GEMINI_API_KEY environment variable is not set! Set it or pass api_key parameter.")
        
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.model_name = model_name
        self.adb = adb_wrapper or ADBWrapper(serial=serial)
        self.history: List[Dict[str, Any]] = []

    def get_current_state(self):
        """Captures screenshot, dumps XML hierarchy, parses UI elements and creates annotated image."""
        screenshot = self.adb.screencap()
        xml_dump = self.adb.dump_hierarchy()
        elements = UIParser.parse_xml(xml_dump, filter_interactive=True)
        
        elements_dict = [e.to_dict() for e in elements]
        annotated_image = draw_element_boxes(screenshot, elements_dict)
        
        return screenshot, annotated_image, elements, elements_dict

    def execute_action(self, action: AgentAction, elements: List[UIElement], screen_width: int, screen_height: int):
        """Executes selected action via ADBWrapper."""
        logger.info(f"[ACTION] {action.action_type.value}: {action.thought}")

        if action.action_type == ActionType.TAP_ELEMENT:
            if action.element_id is None:
                logger.error("TAP_ELEMENT specified without element_id")
                return
            target = next((e for e in elements if e.id == action.element_id), None)
            if target:
                self.adb.tap(target.center[0], target.center[1])
            else:
                logger.error(f"Element ID {action.element_id} not found in current UI tree.")

        elif action.action_type == ActionType.TAP_COORDINATE:
            if action.x is not None and action.y is not None:
                self.adb.tap(action.x, action.y)

        elif action.action_type == ActionType.TYPE_TEXT:
            if action.element_id is not None:
                target = next((e for e in elements if e.id == action.element_id), None)
                if target:
                    self.adb.tap(target.center[0], target.center[1])
                    time.sleep(0.5)
            if action.text:
                self.adb.type_text(action.text)

        elif action.action_type == ActionType.SWIPE:
            direction = (action.direction or "UP").upper()
            cx, cy = screen_width // 2, screen_height // 2
            dx, dy = screen_width // 3, screen_height // 3

            if direction == "UP": # Scroll down
                self.adb.swipe(cx, cy + dy, cx, cy - dy)
            elif direction == "DOWN": # Scroll up
                self.adb.swipe(cx, cy - dy, cx, cy + dy)
            elif direction == "LEFT":
                self.adb.swipe(cx + dx, cy, cx - dx, cy)
            elif direction == "RIGHT":
                self.adb.swipe(cx - dx, cy, cx + dx, cy)

        elif action.action_type == ActionType.PRESS_KEY:
            if action.keycode:
                self.adb.press_key(action.keycode)

        elif action.action_type == ActionType.LAUNCH_APP:
            if action.package_name:
                self.adb.launch_app(action.package_name)

        elif action.action_type == ActionType.WAIT:
            time.sleep(action.duration_seconds or 1.0)

    def run_step(self, task: str) -> AgentAction:
        """Executes a single step of perception -> reasoning -> action execution."""
        screenshot, annotated_img, elements, elements_dict = self.get_current_state()
        w, h = screenshot.size

        # Format elements text summary for Gemini
        elements_text_lines = []
        for e in elements:
            info = f"ID {e.id}: [{e.class_name}] bounds={e.bounds}"
            if e.text:
                info += f" text={repr(e.text)}"
            if e.content_desc:
                info += f" desc={repr(e.content_desc)}"
            if e.resource_id:
                info += f" id={repr(e.resource_id)}"
            elements_text_lines.append(info)

        elements_summary = "\n".join(elements_text_lines)

        history_summary = ""
        if self.history:
            history_summary = "Prior Action History:\n" + "\n".join(
                [f"- Step {h['step']}: {h['action']} (Thought: {h['thought']})" for h in self.history]
            )

        prompt = f"""
Goal: {task}

{history_summary}

Current Interactive UI Elements on Screen:
{elements_summary if elements_summary else "(No text/interactive elements parsed from hierarchy)"}

Observing the annotated screenshot and elements list, output the structured AgentAction to perform next.
"""

        if not self.client:
            raise RuntimeError("GEMINI_API_KEY is not set. Please set GEMINI_API_KEY environment variable.")

        # Generate content with retry for 429 rate limits
        max_retries = 3
        backoff_seconds = 5
        response = None

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt, annotated_img],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=AgentAction,
                        temperature=0.2,
                    ),
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries:
                    logger.warning(f"API Rate limit (429) hit. Retrying in {backoff_seconds}s (attempt {attempt}/{max_retries})...")
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                else:
                    raise e

        action: AgentAction = response.parsed
        
        # Log and record step
        self.history.append({
            "step": len(self.history) + 1,
            "thought": action.thought,
            "action": action.action_type.value,
            "details": action.model_dump(exclude_none=True)
        })

        if action.action_type != ActionType.FINISH:
            self.execute_action(action, elements, w, h)

        return action

    def run_task(self, task: str, max_steps: int = 15) -> str:
        """Runs autonomous agent loop until goal is finished or max_steps reached."""
        logger.info(f"Starting Android Agent task: '{task}' (max_steps={max_steps})")
        self.history.clear()

        for step in range(1, max_steps + 1):
            logger.info(f"\n--- Step {step}/{max_steps} ---")
            action = self.run_step(task)

            if action.action_type == ActionType.FINISH:
                msg = action.result_message or "Task finished successfully."
                logger.info(f"[SUCCESS] {msg}")
                return msg

            time.sleep(1.5) # Wait for device UI animation to settle

        logger.warning(f"Reached max steps ({max_steps}) without finishing.")
        return "Max steps reached."
