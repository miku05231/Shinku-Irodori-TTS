#!/usr/bin/env python3
"""Irodori-TTS OpenAI-compatible API server with LoRA support."""
import io
import os
import threading
from pathlib import Path

import soundfile as sf
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from irodori_tts.inference_runtime import InferenceRuntime, RuntimeKey, SamplingRequest

app = FastAPI(title="Irodori-TTS Server")

@app.get("/health")
async def health_check():
    """健康检查端点，用于探测服务是否就绪。"""
    if runtime is not None:
        return {"status": "ready", "model_loaded": True}
    return {"status": "loading", "model_loaded": False}

# Config
BASE_CHECKPOINT = os.environ.get(
    "IRODORI_CHECKPOINT",
    str(Path(__file__).parent / "models/Irodori-TTS-500M-v3/model.safetensors"),
)
LORA_ADAPTER = os.environ.get("IRODORI_LORA", "")
DEFAULT_REF_WAV = os.environ.get("IRODORI_DEFAULT_REF", "")
DEVICE = os.environ.get("IRODORI_DEVICE", "cuda")
HOST = os.environ.get("IRODORI_HOST", "127.0.0.1")
PORT = int(os.environ.get("IRODORI_PORT", "8088"))

runtime: InferenceRuntime | None = None
runtime_lock = threading.Lock()


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
        with runtime_lock:
            if runtime is None:  # 双重检查锁定
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
    
    # 验证参考音频路径，防止路径遍历攻击
    if ref_wav:
        ref_path = Path(ref_wav).resolve()
        # 检查文件是否存在且是音频文件
        if not ref_path.is_file():
            raise HTTPException(400, f"Reference audio not found: {ref_wav}")
        allowed_ext = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}
        if ref_path.suffix.lower() not in allowed_ext:
            raise HTTPException(400, f"Unsupported audio format. Allowed: {allowed_ext}")
        ref_wav = str(ref_path)
    
    # no_ref 模式：有 LoRA 且没有参考音频时启用
    no_ref = ref_wav is None and LORA_ADAPTER

    duration_scale = 1.0 / req.speed if req.speed > 0 else 1.0

    try:
        request = SamplingRequest(
            text=req.input,
            ref_wav=ref_wav,
            no_ref=bool(no_ref),
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
        # 不向客户端返回原始异常，避免泄露内部路径
        print(f"[ERROR] Synthesis failed: {e}")
        raise HTTPException(500, "Synthesis failed. Check server logs for details.")


if __name__ == "__main__":
    print(f"Preloading model from {BASE_CHECKPOINT}...")
    if LORA_ADAPTER:
        print(f"LoRA adapter: {LORA_ADAPTER}")
    get_runtime()
    print(f"Model loaded. Starting server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
