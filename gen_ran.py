"""毛利蘭ピンナップ生成テスト"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from generator import generate_image

prompt = (
    "1girl, solo, mouri ran, detective conan, long brown hair, ponytail, blue eyes, "
    "karate uniform, white gi, black belt, athletic build, "
    "standing pose, confident smile, looking at viewer, "
    "pinup, full body, dynamic pose, "
    "school setting background, sunlight, detailed face"
)

out_path = Path(__file__).parent / "output" / "ran_pinup.png"
out_path.parent.mkdir(parents=True, exist_ok=True)

print(f"生成開始: {out_path}")
img = generate_image(prompt, out_path, rating="safe")
print(f"完了: {out_path} size={img.size}")
