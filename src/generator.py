from pathlib import Path

import torch
from diffusers_anima import AnimaPipeline
from PIL import Image

MODEL_PATH = Path(
    "/Users/shingo/Documents/devel/kaji/_regacy/ComfyUI/models"
    "/diffusion_models/animayume_v04.safetensors"
)

LORA_PATH = Path(
    "/Users/shingo/Documents/devel/kaji/_resource/loras/anima"
    "/anima-turbo-lora-v0.1.safetensors"
)

_POSITIVE_PREFIX = (
    "masterpiece,best quality,highres,absurdrres,"
    "score_7,score_8,score_9,{rating},"
    "official art,digital anime illustration,anime style,vibrant colors,newest,"
)

_NEGATIVE = (
    "score_1,score_2,score_3,blurry,worst quality,low quality,jpeg artifacts,"
    "signature,watermark,username,error,deformed hands,bad anatomy,extra limbs,"
    "poorly drawn hands,poorly drawn face,mutation,deformed,extra eyes,extra arms,"
    "extra legs,malformed limbs,fused fingers,too many fingers,long neck,cross-eyed,"
    "bad proportions,missing arms,missing legs,extra digit,fewer digits,cropped,normal quality"
)

_pipe: AnimaPipeline | None = None


def _get_pipe() -> AnimaPipeline:
    global _pipe
    if _pipe is None:
        _pipe = AnimaPipeline.from_single_file(
            str(MODEL_PATH),
            device="mps" if torch.backends.mps.is_available() else "cpu",
            dtype="bfloat16",
        )
        _pipe.scheduler.set_sampling_config(sampler="euler_a_rf", sigma_schedule="simple")
        _pipe.load_lora_weights(str(LORA_PATH))
    return _pipe


def generate_image(
    scene_prompt: str,
    output_path: Path,
    rating: str = "safe",
) -> Image.Image:
    pipe = _get_pipe()
    positive = _POSITIVE_PREFIX.format(rating=rating) + scene_prompt
    result = pipe(
        prompt=positive,
        negative_prompt=_NEGATIVE,
        height=1152,
        width=896,
        num_inference_steps=10,
        guidance_scale=1.0,
    )
    image = result.images[0]
    image.save(output_path)
    return image
