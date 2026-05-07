import json
import os
from unittest.mock import MagicMock, patch

from ideator import IdeatorOutput, _build_prompt, generate_scenario
from schema import Character, CharacterAppearance


_MOCK_DATA = {
    "name": "ran_morning_training",
    "story": "蘭は朝の道場で空手の稽古に励んでいる。",
    "character": {
        "name": "毛利蘭",
        "name_en": "Mouri Ran",
        "series": "名探偵コナン",
        "base_tags": "mouri ran, detective conan",
        "appearance_tags": "brown hair, long hair, green eyes",
        "appearance": {
            "hair": "茶色の長髪",
            "eyes": "緑色",
            "build": "スリム",
            "age": "17歳",
        },
        "outfits": ["空手着", "制服"],
        "personality": "明るく活発、空手の達人",
        "notes": [],
    },
}


def test_build_prompt_contains_idea():
    idea = "名探偵コナンの毛利蘭の朝の空手稽古のシーン"
    prompt = _build_prompt(idea)
    assert idea in prompt
    assert "name" in prompt
    assert "story" in prompt
    assert "character" in prompt
    assert "JSON" in prompt


def test_generate_scenario_claude_backend():
    mock_stdout = json.dumps({"structured_output": _MOCK_DATA})
    mock_result = MagicMock()
    mock_result.stdout = mock_stdout

    with patch("ideator.subprocess.run", return_value=mock_result), \
         patch.dict(os.environ, {"LLM_BACKEND": "claude"}):
        result = generate_scenario("名探偵コナンの毛利蘭の朝の空手稽古のシーン")

    assert isinstance(result, IdeatorOutput)
    assert result.name == "ran_morning_training"
    assert "蘭" in result.story
    assert isinstance(result.character, Character)
    assert result.character.name == "毛利蘭"
    assert result.character.name_en == "Mouri Ran"


def test_generate_scenario_gemini_backend():
    mock_response = MagicMock()
    mock_response.text = json.dumps(_MOCK_DATA)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("ideator._call_gemini", return_value=_MOCK_DATA), \
         patch.dict(os.environ, {"LLM_BACKEND": "gemini"}):
        result = generate_scenario("テストアイデア")

    assert result.name == "ran_morning_training"
    assert isinstance(result.character, Character)


def test_generate_scenario_retries_on_failure():
    call_count = 0

    def failing_then_ok(prompt: str) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("simulated failure")
        return _MOCK_DATA

    with patch("ideator._call_gemini", side_effect=failing_then_ok), \
         patch.dict(os.environ, {"LLM_BACKEND": "gemini"}):
        result = generate_scenario("テスト")

    assert call_count == 2
    assert result.name == "ran_morning_training"


def test_generate_scenario_raises_after_3_failures():
    with patch("ideator._call_gemini", side_effect=ValueError("always fails")), \
         patch.dict(os.environ, {"LLM_BACKEND": "gemini"}):
        try:
            generate_scenario("テスト")
            assert False, "RuntimeError expected"
        except RuntimeError as e:
            assert "3 attempts" in str(e)
