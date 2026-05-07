import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_generator():
    # Remove cached module to reset module-level state
    for key in list(sys.modules.keys()):
        if "generator" in key and "niji" not in key:
            del sys.modules[key]
    src = Path(__file__).parent.parent / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    # Patch heavy imports before load
    mocks = {
        "torch": MagicMock(),
        "diffusers": MagicMock(),
        "diffusers.loaders": MagicMock(),
        "diffusers.loaders.peft": MagicMock(),
        "diffusers.utils": MagicMock(),
        "diffusers.utils.peft_utils": MagicMock(_create_lora_config=MagicMock()),
        "diffusers_anima": MagicMock(),
        "PIL": MagicMock(),
        "PIL.Image": MagicMock(),
    }
    with patch.dict("sys.modules", mocks):
        import generator as gen
    return gen


def _make_mock_pipe():
    mock_image = MagicMock()
    mock_pipe = MagicMock()
    mock_pipe.return_value.images = [mock_image]
    return mock_pipe, mock_image


def test_get_pipe_loads_lora_when_use_lora_true():
    gen = _load_generator()
    gen._pipe = None
    gen._pipe_has_lora = None

    mock_pipe, _ = _make_mock_pipe()
    gen.AnimaPipeline = MagicMock()
    gen.AnimaPipeline.from_single_file.return_value = mock_pipe

    gen._get_pipe(use_lora=True)

    mock_pipe.load_lora_weights.assert_called_once()
    assert gen._pipe_has_lora is True


def test_get_pipe_skips_lora_when_use_lora_false():
    gen = _load_generator()
    gen._pipe = None
    gen._pipe_has_lora = None

    mock_pipe, _ = _make_mock_pipe()
    gen.AnimaPipeline = MagicMock()
    gen.AnimaPipeline.from_single_file.return_value = mock_pipe

    gen._get_pipe(use_lora=False)

    mock_pipe.load_lora_weights.assert_not_called()
    assert gen._pipe_has_lora is False


def test_get_pipe_reloads_when_lora_state_changes():
    gen = _load_generator()
    gen._pipe_has_lora = True
    existing_pipe = MagicMock()
    gen._pipe = existing_pipe

    new_pipe = MagicMock()
    new_pipe.return_value.images = [MagicMock()]
    gen.AnimaPipeline = MagicMock()
    gen.AnimaPipeline.from_single_file.return_value = new_pipe

    result = gen._get_pipe(use_lora=False)

    assert result is new_pipe
    assert gen._pipe_has_lora is False


def test_generate_image_lora_on_uses_turbo_params(tmp_path):
    gen = _load_generator()
    mock_pipe, mock_image = _make_mock_pipe()
    gen._pipe = mock_pipe
    gen._pipe_has_lora = True

    out = tmp_path / "out.png"
    gen.generate_image("test prompt", out, use_lora=True)

    call_kwargs = mock_pipe.call_args.kwargs
    assert call_kwargs["num_inference_steps"] == 10
    assert call_kwargs["guidance_scale"] == 1.0


def test_generate_image_lora_off_uses_quality_params(tmp_path):
    gen = _load_generator()
    mock_pipe, mock_image = _make_mock_pipe()
    gen._pipe = mock_pipe
    gen._pipe_has_lora = False

    out = tmp_path / "out.png"
    gen.generate_image("test prompt", out, use_lora=False)

    call_kwargs = mock_pipe.call_args.kwargs
    assert call_kwargs["num_inference_steps"] == 30
    assert call_kwargs["guidance_scale"] == 4.5
