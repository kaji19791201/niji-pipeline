import csv
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
import yaml

TAGS_CSV = Path(__file__).parent.parent / "resources" / "anima_general_tags.csv"

_POSE_KEYWORDS = {
    "standing", "sitting", "lying", "pose", "crouch", "kneel", "walking",
    "running", "jump", "squat", "lean", "all fours", "close-up", "upper body",
    "full body", "from above", "from below", "from behind", "side view",
    "front view", "portrait", "action pose", "flying", "on back", "spreading",
    "spread eagle", "step pose", "begging pose",
}


def _load_pose_tags() -> list[str]:
    tags = []
    with open(TAGS_CSV, newline="") as f:
        for row in csv.DictReader(f):
            name = row["name"].strip()
            if any(kw in name for kw in _POSE_KEYWORDS):
                tags.append(name)
    return tags


_SCHEMA = {
    "type": "object",
    "properties": {
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tags":        {"type": "string"},
                    "description": {"type": "string"},
                    "dialogue":    {"type": "string"},
                    "position": {
                        "type": "object",
                        "properties": {
                            "top":  {"type": "string"},
                            "left": {"type": "string"},
                        },
                        "required": ["top", "left"],
                    },
                },
                "required": ["tags", "description", "dialogue", "position"],
            },
        }
    },
    "required": ["scenes"],
}


def _build_prompt(story: str, character: dict) -> str:
    char_yaml = yaml.dump(character, allow_unicode=True, default_flow_style=False)
    pose_tags = _load_pose_tags()
    pose_tags_str = ", ".join(pose_tags)

    return f"""You are a manga scene planner. Generate scenes for an illustrated manga page.

## Prompt Generation Rules (Gem Rules)

### tags field
- Comma-separated English tags (e621/danbooru style)
- Include character appearance tags from the character sheet (species, fur color, hair, eyes, clothing, etc.)
- Include composition/pose tags from the pose tag dictionary
- Add attribute tags relevant to the scene
- Do NOT include quality tags (masterpiece, best quality, etc.)
- Remove tags for body parts outside the frame (e.g. if close-up, omit feet/legs)
- Use tags from the provided pose tag dictionary when applicable

### description field
- Natural English sentence(s) describing the scene
- Cover: spatial composition, lighting, pose, expression, atmosphere
- Be specific and detailed

### dialogue field
- Japanese dialogue for the character in this scene
- Should match the mood and context
- Keep it concise (1-3 sentences)

### position field
- Where to place the dialogue box on the image
- top: percentage from top (e.g. "10%", "70%")
- left: percentage from left (e.g. "5%", "60%")
- Choose a position that avoids covering the character's face and key parts of the scene

## Character Sheet
```yaml
{char_yaml}
```

## Pose Tag Dictionary (use these for composition/pose tags)
{pose_tags_str}

## Story
{story}

## Instructions
- Split the story into scenes. Number of scenes: 5 to 20 depending on story density.
- Each scene should be a distinct moment or beat in the story.
- Output JSON only. No explanation, no markdown.
"""


@dataclass
class Scene:
    tags: str
    description: str
    dialogue: str
    position: dict  # {"top": "20%", "left": "8%"}


def plan_scenes(story: str, character: dict) -> list[Scene]:
    prompt = _build_prompt(story, character)

    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--json-schema", json.dumps(_SCHEMA),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )

    data = json.loads(result.stdout)
    scenes_data = data["structured_output"]["scenes"]

    return [
        Scene(
            tags=s["tags"],
            description=s["description"],
            dialogue=s["dialogue"],
            position=s["position"],
        )
        for s in scenes_data
    ]
