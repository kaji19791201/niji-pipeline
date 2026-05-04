from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image


def make_image(width=512, height=512):
    return Image.new("RGB", (width, height), color=(100, 150, 200))


def test_render_dialogue_calls_playwright(tmp_path):
    image = make_image()
    out_path = tmp_path / "out.png"

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_pw = MagicMock()
    mock_pw.__enter__ = MagicMock(return_value=mock_pw)
    mock_pw.__exit__ = MagicMock(return_value=False)
    mock_pw.chromium.launch.return_value = mock_browser

    with patch("renderer.sync_playwright", return_value=mock_pw):
        from renderer import render_dialogue
        render_dialogue(image, "こんにちは", {"top": "10%", "left": "5%"}, out_path)

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
            render_dialogue(image, "テスト", {"top": "20%", "left": "8%"}, out_path)

    assert html_files, "HTML file was not written"
    html = html_files[0]
    # font_size = int(600 * 0.04) = 24
    assert "24px" in html
    assert "20%" in html
    assert "8%" in html
