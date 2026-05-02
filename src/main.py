import argparse


def main():
    parser = argparse.ArgumentParser(description="niji-pipeline")
    parser.add_argument("--story", required=True)
    parser.add_argument("--char", required=True)
    parser.add_argument("--output", default="output")
    args = parser.parse_args()
    print(f"story={args.story}, char={args.char}, output={args.output}")


if __name__ == "__main__":
    main()
