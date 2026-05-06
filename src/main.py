import argparse
import json
from dataclasses import asdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="niji-pipeline")
    parser.add_argument("--story", required=True)
    parser.add_argument("--char", required=True)
    parser.add_argument("--output", default="output")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        from generator import generate_image
        from renderer import detect_placements, render_dialogue

        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        raw_dir = out_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        scene_prompt = "1girl, solo, long hair, school uniform, looking at viewer, smile"
        raw_path = raw_dir / "dry_run.png"
        out_path = out_dir / "dry_run.png"
        print(f"[dry-run] generating: {scene_prompt}")
        image = generate_image(scene_prompt, raw_path)
        print(f"[dry-run] saved: {raw_path} ({image.size})")
        texts = [
            {"text": "テストセリフです。\nここに文字が入ります。", "role": "dialogue"},
            {"text": "ドキッ", "role": "sfx"},
        ]
        placements = detect_placements(image, texts)
        render_dialogue(image, placements, out_path)
        print(f"[dry-run] rendered: {out_path}")
    else:
        import yaml
        from planner import plan_scenes
        from generator import generate_image
        from renderer import detect_placements, render_dialogue

        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        raw_dir = out_dir / "raw"
        raw_dir.mkdir(exist_ok=True)

        story = Path(args.story).read_text()
        character = yaml.safe_load(Path(args.char).read_text())

        print("[planner] generating scenes...")
        scenes = plan_scenes(story, character)
        print(f"[planner] {len(scenes)} scenes")

        scenes_path = out_dir / "scenes.json"
        scenes_path.write_text(
            json.dumps([asdict(s) for s in scenes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[planner] saved: {scenes_path}")

        for i, scene in enumerate(scenes):
            print(f"\n--- scene {i+1} ---")
            print(f"  tags: {scene.tags}")
            print(f"  description: {scene.description}")
            print(f"  texts: {scene.texts}")
            scene_prompt = f"{scene.tags}\n{scene.description}"
            raw_path = raw_dir / f"scene_{i+1:02d}.png"
            out_path = out_dir / f"scene_{i+1:02d}.png"
            print(f"[generator] generating {raw_path}...")
            image = generate_image(scene_prompt, raw_path)
            print(f"[generator] saved: {raw_path} ({image.size})")
            placements = detect_placements(image, scene.texts)
            render_dialogue(image, placements, out_path)
            print(f"[renderer] rendered: {out_path}")


if __name__ == "__main__":
    main()
