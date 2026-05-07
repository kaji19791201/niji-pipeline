import argparse
import json
from dataclasses import asdict
from pathlib import Path

from schema import Scenario


def main():
    parser = argparse.ArgumentParser(description="niji-pipeline")
    parser.add_argument("--scenario", default=None, help="Path to scenario JSON (scenarios/*.json)")
    parser.add_argument("--idea", default=None, help="One-line idea to auto-generate scenario")
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-lora", action="store_true")
    args = parser.parse_args()
    use_lora = not args.no_lora

    if args.idea is None and args.scenario is None:
        parser.error("either --idea or --scenario is required")

    if args.idea:
        from ideator import generate_scenario
        print(f"[ideator] generating scenario from idea: {args.idea}")
        result = generate_scenario(args.idea)
        scenarios_dir = Path("scenarios")
        scenarios_dir.mkdir(parents=True, exist_ok=True)
        scenario_path = scenarios_dir / f"{result.name}.json"
        scenario = Scenario(
            idea=args.idea,
            character=result.character,
            story=result.story,
        )
        scenario_path.write_text(
            scenario.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )
        print(f"[ideator] saved: {scenario_path}")
    else:
        scenario_path = Path(args.scenario)
        scenario = Scenario.model_validate_json(scenario_path.read_text(encoding="utf-8"))

    out_dir = Path(args.output) if args.output else Path("output") / scenario_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        from generator import generate_image
        from renderer import detect_placements, render_dialogue

        raw_dir = out_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        scene_prompt = "1girl, solo, long hair, school uniform, looking at viewer, smile"
        raw_path = raw_dir / "dry_run.png"
        out_path = out_dir / "dry_run.png"
        print(f"[dry-run] generating: {scene_prompt}")
        image = generate_image(scene_prompt, raw_path, use_lora=use_lora)
        print(f"[dry-run] saved: {raw_path} ({image.size})")
        texts = [
            {"text": "テストセリフです。\nここに文字が入ります。", "role": "dialogue"},
            {"text": "ドキッ", "role": "sfx"},
        ]
        placements = detect_placements(image, texts)
        render_dialogue(image, placements, out_path)
        print(f"[dry-run] rendered: {out_path}")
    else:
        from planner import plan_scenes
        from generator import generate_image
        from renderer import detect_placements, render_dialogue

        raw_dir = out_dir / "raw"
        raw_dir.mkdir(exist_ok=True)

        print("[planner] generating scenes...")
        scenes = plan_scenes(scenario.story, scenario.character.model_dump())
        print(f"[planner] {len(scenes)} scenes")

        scenes_path = out_dir / "scenes.json"
        scenes_path.write_text(
            json.dumps([asdict(s) for s in scenes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[planner] saved: {scenes_path}")

        scenario.scenes = [asdict(s) for s in scenes]
        scenario_path.write_text(
            scenario.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )

        for i, scene in enumerate(scenes):
            print(f"\n--- scene {i+1} ---")
            print(f"  tags: {scene.tags}")
            print(f"  description: {scene.description}")
            print(f"  texts: {scene.texts}")
            scene_prompt = f"{scene.tags}\n{scene.description}"
            raw_path = raw_dir / f"scene_{i+1:02d}.png"
            out_path = out_dir / f"scene_{i+1:02d}.png"
            print(f"[generator] generating {raw_path}...")
            image = generate_image(scene_prompt, raw_path, use_lora=use_lora)
            print(f"[generator] saved: {raw_path} ({image.size})")
            placements = detect_placements(image, scene.texts)
            render_dialogue(image, placements, out_path)
            print(f"[renderer] rendered: {out_path}")


if __name__ == "__main__":
    main()
