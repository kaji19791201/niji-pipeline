import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image


def make_image(width=512, height=512):
    return Image.new("RGB", (width, height), color=(100, 150, 200))


def make_placements(font_size=20):
    return [
        {"text": "こんにちは", "role": "dialogue", "top": "10%", "left": "5%", "font_size": font_size, "rotation": 0},
        {"text": "ドキッ", "role": "sfx", "top": "70%", "left": "65%", "font_size": int(font_size * 1.3), "rotation": 15},
    ]


def test_render_dialogue_calls_playwright(tmp_path):
    image = make_image()
    out_path = tmp_path / "out.png"
    placements = make_placements()

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_pw = MagicMock()
    mock_pw.__enter__ = MagicMock(return_value=mock_pw)
    mock_pw.__exit__ = MagicMock(return_value=False)
    mock_pw.chromium.launch.return_value = mock_browser

    with patch("renderer.sync_playwright", return_value=mock_pw):
        from renderer import render_dialogue
        render_dialogue(image, placements, out_path)

    mock_page.goto.assert_called_once()
    url = mock_page.goto.call_args[0][0]
    assert url.startswith("file://")

    mock_page.screenshot.assert_called_once()
    kwargs = mock_page.screenshot.call_args[1]
    assert kwargs["path"] == str(out_path)
    assert kwargs["clip"] == {"x": 0, "y": 0, "width": 512, "height": 512}


def test_render_dialogue_html_contents(tmp_path):
    image = make_image(width=800, height=600)
    out_path = tmp_path / "out.png"
    font_size = 24
    placements = make_placements(font_size=font_size)

    html_files = []

    original_write_text = Path.write_text

    def capturing_write_text(self, text, encoding=None):
        if str(self).endswith(".html"):
            html_files.append(text)
        return original_write_text(self, text, encoding=encoding)

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_pw = MagicMock()
    mock_pw.__enter__ = MagicMock(return_value=mock_pw)
    mock_pw.__exit__ = MagicMock(return_value=False)
    mock_pw.chromium.launch.return_value = mock_browser

    with patch("renderer.sync_playwright", return_value=mock_pw):
        with patch.object(Path, "write_text", capturing_write_text):
            from renderer import render_dialogue
            render_dialogue(image, placements, out_path)

    assert html_files, "HTML file was not written"
    html = html_files[0]
    assert f"{font_size}px" in html
    assert "10%" in html
    assert "5%" in html
    assert "writing-mode: vertical-rl" in html
    assert "writing-mode: horizontal-tb" in html
    assert "こんにちは" in html
    assert "ドキッ" in html


def test_detect_placements_fallback_on_failure(tmp_path):
    image = make_image(width=512, height=512)
    texts = [
        {"text": "セリフA", "role": "dialogue"},
        {"text": "バキッ", "role": "sfx"},
    ]

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = RuntimeError("API error")

        from renderer import detect_placements
        placements = detect_placements(image, texts)

    assert len(placements) == 2
    dialogue = next(p for p in placements if p["role"] == "dialogue")
    sfx = next(p for p in placements if p["role"] == "sfx")
    assert dialogue["text"] == "セリフA"
    assert sfx["text"] == "バキッ"
    assert "top" in dialogue and "left" in dialogue
    assert dialogue["rotation"] == 0
    assert sfx["rotation"] != 0


def test_detect_placements_clamps_values():
    image = make_image(width=512, height=512)
    texts = [{"text": "テスト", "role": "dialogue"}]

    font_min = int(512 * 0.02)
    font_max = int(512 * 0.08)

    raw_response = {
        "placements": [
            {"text": "テスト", "role": "dialogue", "top": "200%", "left": "-10%", "font_size": 500, "rotation": 90}
        ]
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(raw_response)

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response

        from renderer import detect_placements
        placements = detect_placements(image, texts)

    assert len(placements) == 1
    p = placements[0]
    assert float(p["top"].rstrip("%")) <= 95
    assert float(p["left"].rstrip("%")) >= 0
    assert font_min <= p["font_size"] <= font_max
    assert -30 <= p["rotation"] <= 30
