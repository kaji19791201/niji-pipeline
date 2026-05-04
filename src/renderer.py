import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


def render_dialogue(image: Image.Image, dialogue: str, position: dict, output_path: Path) -> None:
    width, height = image.size
    font_size = int(height * 0.04)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_tmp:
        img_path = Path(img_tmp.name)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as html_tmp:
        html_path = Path(html_tmp.name)

    try:
        image.save(img_path)

        escaped = dialogue.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        top = position.get("top", "10%")
        left = position.get("left", "5%")

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ width: {width}px; height: {height}px; overflow: hidden; position: relative; }}
  img {{ position: absolute; top: 0; left: 0; width: {width}px; height: {height}px; }}
  .text {{
    position: absolute;
    top: {top};
    left: {left};
    writing-mode: vertical-rl;
    text-orientation: upright;
    font-family: 'Hiragino Mincho ProN', 'Yu Mincho', serif;
    font-size: {font_size}px;
    color: white;
    line-height: 1.4;
    text-shadow:
      -2px -2px 0 black,  2px -2px 0 black,
      -2px  2px 0 black,  2px  2px 0 black,
      -3px  0   0 black,  3px  0   0 black,
       0   -3px 0 black,  0    3px 0 black,
       0    0   12px rgba(100, 160, 255, 0.9);
  }}
</style>
</head><body>
<img src="file://{img_path}">
<div class="text">{escaped}</div>
</body></html>"""

        html_path.write_text(html, encoding="utf-8")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"file://{html_path}")
            page.screenshot(
                path=str(output_path),
                clip={"x": 0, "y": 0, "width": width, "height": height},
            )
            browser.close()
    finally:
        img_path.unlink(missing_ok=True)
        html_path.unlink(missing_ok=True)
