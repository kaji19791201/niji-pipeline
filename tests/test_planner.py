import json
from unittest.mock import MagicMock, patch

import pytest

from planner import Scene, _build_prompt, plan_scenes


def test_build_prompt_contains_story():
    story = "A fox girl wanders through the autumn forest."
    character = {"name": "Kitsune", "species": "fox", "fur_color": "orange"}
    prompt = _build_prompt(story, character)
    assert story in prompt
    assert "Kitsune" in prompt
    assert "description" in prompt
    assert "tags" in prompt


def test_build_prompt_no_pose_dict():
    story = "Test story."
    character = {"name": "Test"}
    prompt = _build_prompt(story, character)
    assert "Pose Tag Dictionary" not in prompt


def test_plan_scenes_parses_claude_output():
    mock_scenes = [
        {
            "tags": "solo, fox_girl, standing, autumn_forest",
            "description": "A fox girl stands among golden leaves.",
            "dialogue": "きれいな景色……",
            "position": {"top": "10%", "left": "5%"},
        }
    ]
    mock_stdout = json.dumps({"structured_output": {"scenes": mock_scenes}})

    mock_result = MagicMock()
    mock_result.stdout = mock_stdout

    with patch("planner.subprocess.run", return_value=mock_result) as mock_run:
        scenes = plan_scenes("A fox girl walks in autumn.", {"name": "Kitsune"})

    assert len(scenes) == 1
    s = scenes[0]
    assert isinstance(s, Scene)
    assert s.tags == "solo, fox girl, standing, autumn forest"
    assert s.dialogue == "きれいな景色……"
    assert s.position == {"top": "10%", "left": "5%"}

    call_args = mock_run.call_args
    cmd = call_args[0][0]
    assert cmd[0] == "claude"
    assert "-p" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd
    assert "--json-schema" in cmd
