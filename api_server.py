#!/usr/bin/env python3
"""Irodori-TTS OpenAI-compatible API server with LoRA support."""
import io
import os
from pathlib import Path

import soundfile as sf
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from irodori_tts.inference_runtime import InferenceRuntime, RuntimeKey, SamplingRequest

app = FastAPI(title="Irodori-TTS Server")

# Config
BASE_CHECKPOINT = os.environ.get(
    "IRODORI_CHECKPOINT",
    str(Path(__file__).parent / "models/Irodori-TTS-500M-v3/model.safetensors"),
)
LORA_ADAPTER = os.environ.get("IRODORI_LORA", "")
DEFAULT_REF_WAV = os.environ.get("IRODORI_DEFAULT_REF", "")
DEVICE = os.environ.get("IRODORI_DEVICE", "cuda")
PORT = int(os.environ.get("IRODORI_PORT", "8088"))

runtime: InferenceRuntime | None = None


class SpeechRequest(BaseModel):
    model: str = "irodori-tts"
    input: str
    voice: str | None = None
    response_format: str = "wav"
    speed: float = 0.6
    steps: int = 40
    text_scale: float = 4.0
    speaker_scale: float | None = None


def get_runtime() -> InferenceRuntime:
    global runtime
    if runtime is None:
        key = RuntimeKey(
            checkpoint=BASE_CHECKPOINT,
            model_device=DEVICE,
            codec_device=DEVICE,
        )
        runtime = InferenceRuntime.from_key(key)
    return runtime


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{"id": "irodori-tts", "object": "model", "owned_by": "local"}],
    }


@app.post("/v1/audio/speech")
async def create_speech(req: SpeechRequest):
    if not req.input.strip():
        raise HTTPException(400, "input is required")

    rt = get_runtime()

    ref_wav = req.voice or DEFAULT_REF_WAV or None
    use_no_ref = LORA_ADAPTER is not None and LORA_ADAPTER != ""

    duration_scale = 1.0 / req.speed if req.speed > 0 else 1.0

    try:
        request = SamplingRequest(
            text=req.input,
            ref_wav=ref_wav,
            no_ref=(ref_wav is None),
            duration_scale=duration_scale,
            num_steps=req.steps,
            cfg_scale_text=req.text_scale,
            cfg_scale_speaker=req.speaker_scale if req.speaker_scale is not None else 5.0,
            lora_adapter=LORA_ADAPTER if LORA_ADAPTER else None,
        )
        result = rt.synthesize(request)

        audio_tensor = result.audio
        sample_rate = result.sample_rate

        if isinstance(audio_tensor, torch.Tensor):
            audio_np = audio_tensor.cpu().numpy()
        else:
            import numpy as np
            audio_np = np.array(audio_tensor)

        if audio_np.ndim > 1:
            audio_np = audio_np.squeeze()

        buf = io.BytesIO()
        sf.write(buf, audio_np, sample_rate, format="WAV")
        content = buf.getvalue()

        return Response(content=content, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(500, f"Synthesis failed: {e}")


if __name__ == "__main__":
    print(f"Preloading model from {BASE_CHECKPOINT}...")
    if LORA_ADAPTER:
        print(f"LoRA adapter: {LORA_ADAPTER}")
    get_runtime()
    print(f"Model loaded. Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
