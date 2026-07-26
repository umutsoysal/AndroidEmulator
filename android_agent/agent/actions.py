"""
Action Pydantic schema for structured output decision making by the Android AI Agent.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ActionType(StrEnum):
    """Supported action types for the Android agent."""

    TAP_ELEMENT = "TAP_ELEMENT"
    TAP_COORDINATE = "TAP_COORDINATE"
    TYPE_TEXT = "TYPE_TEXT"
    SWIPE = "SWIPE"
    PRESS_KEY = "PRESS_KEY"
    LAUNCH_APP = "LAUNCH_APP"
    WAIT = "WAIT"
    FINISH = "FINISH"


class AgentAction(BaseModel):
    """Structured decision output from Gemini model for an Android Agent turn."""

    thought: str = Field(
        description=(
            "Step-by-step reasoning explaining what the agent sees and why it chose this action."
        )
    )
    action_type: ActionType = Field(description="The action type to perform.")
    element_id: int | None = Field(
        default=None, description="Numeric element ID from UI tree to interact with."
    )
    x: int | None = Field(default=None, description="X coordinate for TAP_COORDINATE.")
    y: int | None = Field(default=None, description="Y coordinate for TAP_COORDINATE.")
    text: str | None = Field(default=None, description="Text string to type for TYPE_TEXT action.")
    direction: str | None = Field(
        default=None, description="Swipe direction: UP, DOWN, LEFT, or RIGHT."
    )
    keycode: str | None = Field(
        default=None, description="Keycode name for PRESS_KEY: HOME, BACK, ENTER, APP_SWITCH."
    )
    package_name: str | None = Field(
        default=None, description="Package name to launch for LAUNCH_APP."
    )
    duration_seconds: float | None = Field(
        default=1.0, description="Duration in seconds for WAIT action."
    )
    result_message: str | None = Field(
        default=None, description="Final result message when action_type is FINISH."
    )
