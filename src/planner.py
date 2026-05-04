import json
import subprocess
from dataclasses import dataclass
import yaml


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

    return f"""You are a manga scene planner. Generate scenes for an illustrated manga page.

## Prompt Generation Rules

### tags field
- Comma-separated English tags (e621/danbooru style, space-separated words within each tag)
- Keep tags minimal — only what cannot be expressed in description
- Always include: species tag (anthro/human/etc.), gender, count (1girl/1boy/duo/etc.)
- For known fictional characters: use `character name, series name` tags
  - Do NOT add body type tags (tall, slender, etc.) for known characters
- For original/unnamed characters: add body type tags as needed
- Include pose/framing tag if it is a fixed constraint (e.g. close-up, from above, full body)
- Do NOT include: emotions, colors, backgrounds, lighting, atmosphere — put these in description instead
- Do NOT include quality tags (masterpiece, best quality, etc.)

### description field
- Natural English prose (2-4 sentences). This is the primary driver of image quality.
- Cover ALL of the following:
  - Framing & composition: camera angle, distance, what is in/out of frame
  - Lighting: direction, quality, color temperature (e.g. "soft afternoon sunlight from the left")
  - Pose & gesture: body position, hand placement, weight distribution
  - Expression & gaze: emotion, eye direction
  - Atmosphere & mood: time of day, weather, emotional tone
  - Background: setting, depth, what surrounds the character
- Be specific. "She leans against a window" beats "she is by a window"

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
            tags=s["tags"].replace("_", " "),
            description=s["description"],
            dialogue=s["dialogue"],
            position=s["position"],
        )
        for s in scenes_data
    ]
