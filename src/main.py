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
        print(f"story={args.story}, char={args.char}, output={args.output}")


if __name__ == "__main__":
    main()
