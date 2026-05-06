from pathlib import Path

import torch
import diffusers.loaders.peft as _diffusers_peft
import diffusers.utils.peft_utils as _peft_utils
from diffusers_anima import AnimaPipeline
from PIL import Image

# NOTE: diffusers-anima bug — lora_state_dict() passes raw safetensors metadata {'format':'pt'} as LoRA config.
# diffusers 0.37.1 _create_lora_config() treats any non-None metadata as LoRA config → KeyError:'rank_pattern'.
# Fix belongs in diffusers-anima lora_state_dict(): set metadata=None after non-diffusers conversion.
_orig_create_lora_config = _peft_utils._create_lora_config
_LORA_CONFIG_KEYS = {"r", "target_modules", "rank_pattern"}

def _patched_create_lora_config(state_dict, network_alphas, metadata, *args, **kwargs):
    if metadata is not None and not _LORA_CONFIG_KEYS.intersection(metadata):
        metadata = None
    return _orig_create_lora_config(state_dict, network_alphas, metadata, *args, **kwargs)

_diffusers_peft._create_lora_config = _patched_create_lora_config

_BASE = Path(__file__).parent.parent
MODEL_PATH = _BASE / "resources/models/animayume_v04.safetensors"
LORA_PATH = _BASE / "resources/loras/anima-turbo-lora-v0.1.safetensors"

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
