from dataclasses import dataclass


@dataclass
class Scene:
    tags: str
    description: str
    dialogue: str
    position: dict  # {"top": "20%", "left": "8%"}


def plan_scenes(story: str, character: dict) -> list[Scene]:
    ...
