"""
Parser module for Android uiautomator layout XML files.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any


@dataclass
# pylint: disable=too-many-instance-attributes
class UIElement:
    """Represents a single parsed UI element from Android uiautomator XML."""

    id: int
    text: str
    content_desc: str
    resource_id: str
    class_name: str
    package: str
    bounds: tuple[int, int, int, int]  # (xmin, ymin, xmax, ymax)
    center: tuple[int, int]  # (cx, cy)
    clickable: bool
    editable: bool
    scrollable: bool
    enabled: bool
    focused: bool

    def to_dict(self) -> dict[str, Any]:
        """Converts element properties to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "content_desc": self.content_desc,
            "resource_id": self.resource_id,
            "class_name": self.class_name,
            "bounds": list(self.bounds),
            "center": list(self.center),
            "clickable": self.clickable,
            "editable": self.editable,
            "scrollable": self.scrollable,
        }


class UIParser:
    """Parses Android uiautomator dump XML hierarchies."""

    @staticmethod
    def parse_bounds(bounds_str: str) -> tuple[int, int, int, int] | None:
        """
        Parses bounds string of format '[xmin,ymin][xmax,ymax]'
        Returns (xmin, ymin, xmax, ymax) or None if invalid.
        """
        match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
        if match:
            xmin, ymin, xmax, ymax = map(int, match.groups())
            return (xmin, ymin, xmax, ymax)
        return None

    @classmethod
    # pylint: disable=too-many-locals
    def parse_xml(cls, xml_content: str, filter_interactive: bool = True) -> list[UIElement]:
        """
        Parses XML string into list of UIElement objects.
        If filter_interactive is True, filters out non-interactive or empty elements.
        """
        if not xml_content or not xml_content.strip():
            return []

        try:
            root = ET.fromstring(xml_content.strip())
        except ET.ParseError:
            return []

        elements: list[UIElement] = []
        element_counter = 1

        for node in root.iter():
            if node.tag != "node":
                continue

            attr = node.attrib
            bounds_str = attr.get("bounds", "")
            bounds = cls.parse_bounds(bounds_str)
            if not bounds:
                continue

            xmin, ymin, xmax, ymax = bounds
            width = xmax - xmin
            height = ymax - ymin

            if width <= 0 or height <= 0:
                continue

            center = (xmin + width // 2, ymin + height // 2)

            text = attr.get("text", "").strip()
            content_desc = attr.get("content-desc", "").strip()
            resource_id = attr.get("resource-id", "").strip()
            class_name = attr.get("class", "").strip()
            package = attr.get("package", "").strip()

            clickable = attr.get("clickable", "false").lower() == "true"
            editable = (
                attr.get("focused", "false").lower() == "true" or "edittext" in class_name.lower()
            )
            scrollable = attr.get("scrollable", "false").lower() == "true"
            enabled = attr.get("enabled", "true").lower() == "true"
            focused = attr.get("focused", "false").lower() == "true"

            if filter_interactive:
                is_meaningful = (
                    clickable or editable or scrollable or bool(text) or bool(content_desc)
                )
                if not is_meaningful:
                    continue

            element = UIElement(
                id=element_counter,
                text=text,
                content_desc=content_desc,
                resource_id=resource_id,
                class_name=class_name,
                package=package,
                bounds=bounds,
                center=center,
                clickable=clickable,
                editable=editable,
                scrollable=scrollable,
                enabled=enabled,
                focused=focused,
            )
            elements.append(element)
            element_counter += 1

        return elements
