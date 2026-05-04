import argparse
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

        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        scene_prompt = "1girl, solo, long hair, school uniform, looking at viewer, smile"
        out_path = out_dir / "dry_run.png"
        print(f"[dry-run] generating: {scene_prompt}")
        image = generate_image(scene_prompt, out_path)
        print(f"[dry-run] saved: {out_path} ({image.size})")
    else:
        import yaml
        from planner import plan_scenes
        from generator import generate_image

        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)

        story = Path(args.story).read_text()
        character = yaml.safe_load(Path(args.char).read_text())

        print("[planner] generating scenes...")
        scenes = plan_scenes(story, character)
        print(f"[planner] {len(scenes)} scenes")

        for i, scene in enumerate(scenes):
            print(f"\n--- scene {i+1} ---")
            print(f"  tags: {scene.tags}")
            print(f"  description: {scene.description}")
            print(f"  dialogue: {scene.dialogue}")
            scene_prompt = f"{scene.tags}\n{scene.description}"
            out_path = out_dir / f"scene_{i+1:02d}.png"
            print(f"[generator] generating {out_path}...")
            image = generate_image(scene_prompt, out_path)
            print(f"[generator] saved: {out_path} ({image.size})")


if __name__ == "__main__":
    main()
