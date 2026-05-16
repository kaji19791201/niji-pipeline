import json
import os
import subprocess

from pydantic import BaseModel

from schema import Character


class IdeatorOutput(BaseModel):
    name: str
    story: str
    character: Character


_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "story": {"type": "string"},
        "character": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "name_en": {"type": "string"},
                "series": {"type": "string"},
                "base_tags": {"type": "string"},
                "appearance_tags": {"type": "string"},
                "appearance": {
                    "type": "object",
                    "properties": {
                        "hair": {"type": "string"},
                        "eyes": {"type": "string"},
                        "build": {"type": "string"},
                        "age": {"type": "string"},
                    },
                    "required": ["hair", "eyes", "build", "age"],
                },
                "outfits": {"type": "array", "items": {"type": "string"}},
                "personality": {"type": "string"},
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "name", "name_en", "series", "base_tags", "appearance_tags",
                "appearance", "outfits", "personality",
            ],
        },
    },
    "required": ["name", "story", "character"],
}


def _build_prompt(idea: str) -> str:
    return f"""You are an anime character and story designer.

Given the following idea, generate a character definition and story for an illustrated manga scene.

## Idea
{idea}

## Instructions
- name: ASCII snake_case string used as the scenario filename (e.g. "ran_morning_training")
- story: 2-5 sentences in Japanese describing the scene
- character.base_tags: tags that identify the character for ComfyUI (e.g. "mouri ran, detective conan")
- character.appearance_tags: comma-separated appearance tags for ComfyUI (e.g. "brown hair, long hair, green eyes")
- character.appearance: natural language description with hair, eyes, build, age subfields
- character.outfits: list of outfits the character might wear in this scenario
- character.personality: one-line personality summary in Japanese
- character.notes: optional list of special rendering notes (can be empty list)

Output JSON only. No explanation, no markdown.
"""


def _call_claude(prompt: str) -> dict:
    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--json-schema", json.dumps(_SCHEMA),
        ],
        capture_output=True, text=True, check=True, timeout=120,
    )
    data = json.loads(result.stdout)
    return data["structured_output"]


def _call_gemini(prompt: str) -> dict:
    import google.genai as genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.environ["GEMINI_MODEL"],
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_SCHEMA,
        ),
    )
    return json.loads(response.text)


def generate_scenario(idea: str) -> IdeatorOutput:
    prompt = _build_prompt(idea)
    backend = os.environ.get("LLM_BACKEND", "gemini")

    last_exc = None
    for attempt in range(3):
        try:
            if backend == "gemini":
                data = _call_gemini(prompt)
            else:
                data = _call_claude(prompt)
            return IdeatorOutput.model_validate(data)
        except Exception as e:
            last_exc = e
            print(f"[ideator] attempt {attempt + 1} failed: {e}")

    raise RuntimeError(f"ideator failed after 3 attempts: {last_exc}") from last_exc
