import json
from unittest.mock import MagicMock, patch

import pytest

from planner import Scene, _build_prompt, _load_pose_tags, plan_scenes


def test_load_pose_tags_returns_list():
    tags = _load_pose_tags()
    assert isinstance(tags, list)
    assert len(tags) > 0
    assert "standing" in tags
    assert "sitting" in tags


def test_build_prompt_contains_story():
    story = "A fox girl wanders through the autumn forest."
    character = {"name": "Kitsune", "species": "fox", "fur_color": "orange"}
    prompt = _build_prompt(story, character)
    assert story in prompt
    assert "Kitsune" in prompt
    assert "standing" in prompt


def test_plan_scenes_parses_claude_output():
    mock_scenes = [
        {
            "tags": "solo, fox girl, standing, autumn forest",
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
