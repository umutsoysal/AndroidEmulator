"""
Unit tests for Android Agent components.
"""

import unittest
from PIL import Image
from android_agent.device.ui_parser import UIParser
from android_agent.device.adb_wrapper import ADBWrapper
from android_agent.device.emulator_manager import EmulatorManager
from android_agent.utils.visualizer import draw_element_boxes
from android_agent.agent.actions import AgentAction, ActionType


class TestAndroidAgentComponents(unittest.TestCase):
    """Unit test cases for UI parser, visualizer, ADB wrapper, and actions."""

    def test_ui_parser_bounds(self):
        """Tests parsing of bounds coordinate string."""
        bounds_str = "[100,200][300,500]"
        parsed = UIParser.parse_bounds(bounds_str)
        self.assertEqual(parsed, (100, 200, 300, 500))

    def test_ui_parser_xml(self):
        """Tests parsing of uiautomator XML string into UIElement objects."""
        sample_xml = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
        <hierarchy rotation="0">
            <node index="0" text="Settings" resource-id="com.android.settings:id/title"
                  class="android.widget.TextView" package="com.android.settings"
                  content-desc="" clickable="true" enabled="true" focused="false"
                  bounds="[50,100][400,200]" />
            <node index="1" text="Network" resource-id="com.android.settings:id/summary"
                  class="android.widget.TextView" package="com.android.settings"
                  content-desc="Network settings" clickable="true" enabled="true" focused="false"
                  bounds="[50,220][400,320]" />
        </hierarchy>"""

        elements = UIParser.parse_xml(sample_xml, filter_interactive=True)
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0].id, 1)
        self.assertEqual(elements[0].text, "Settings")
        self.assertEqual(elements[0].center, (225, 150))
        self.assertEqual(elements[1].id, 2)
        self.assertEqual(elements[1].content_desc, "Network settings")
        self.assertEqual(elements[1].center, (225, 270))

    def test_visualizer(self):
        """Tests drawing element badges on an image."""
        img = Image.new("RGB", (500, 500), color="white")
        elements = [
            {"id": 1, "bounds": [50, 100, 400, 200]},
            {"id": 2, "bounds": [50, 220, 400, 320]}
        ]
        annotated = draw_element_boxes(img, elements)
        self.assertEqual(annotated.size, (500, 500))

    def test_action_schema(self):
        """Tests Pydantic AgentAction schema instantiation."""
        action = AgentAction(
            thought="Tapping Settings item",
            action_type=ActionType.TAP_ELEMENT,
            element_id=1
        )
        self.assertEqual(action.action_type, ActionType.TAP_ELEMENT)
        self.assertEqual(action.element_id, 1)

    def test_adb_wrapper(self):
        """Tests ADBWrapper device discovery call."""
        adb = ADBWrapper()
        devices = adb.get_devices()
        self.assertIsInstance(devices, list)

    def test_emulator_manager(self):
        """Tests EmulatorManager AVD enumeration call."""
        emu = EmulatorManager()
        avds = emu.list_avds()
        self.assertIsInstance(avds, list)
        self.assertIn("Pixel_3a_API_34", avds)


if __name__ == "__main__":
    unittest.main()
