"""
Visualizer utility for annotating UI screenshots with bounding boxes and numeric badges.
"""

from typing import List
from PIL import Image, ImageDraw, ImageFont


# pylint: disable=too-many-locals
def draw_element_boxes(
    image: Image.Image,
    elements: List[dict],
    highlight_color: str = "#FF5722",
    badge_color: str = "#2196F3",
    text_color: str = "#FFFFFF"
) -> Image.Image:
    """
    Draws bounding boxes and numeric ID badges on an image for a list of elements.
    Each element dictionary must contain:
    - 'id': int
    - 'bounds': Tuple[int, int, int, int] (xmin, ymin, xmax, ymax)
    """
    annotated = image.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)

    try:
        font = ImageFont.load_default()
    # pylint: disable=broad-exception-caught
    except Exception:
        font = None

    for elem in elements:
        elem_id = elem.get("id")
        bounds = elem.get("bounds")
        if not bounds or len(bounds) != 4:
            continue

        xmin, ymin, xmax, ymax = bounds

        # Draw bounding rectangle
        draw.rectangle([xmin, ymin, xmax, ymax], outline=highlight_color, width=3)

        # Draw ID badge at top-left of element
        badge_text = f" {elem_id} "
        badge_x = max(0, xmin)
        badge_y = max(0, ymin - 18)

        if font:
            bbox = font.getbbox(badge_text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(badge_text) * 8
            text_height = 14

        draw.rectangle(
            [badge_x, badge_y, badge_x + text_width + 4, badge_y + text_height + 4],
            fill=badge_color
        )
        draw.text((badge_x + 2, badge_y + 2), badge_text, fill=text_color, font=font)

    return annotated
