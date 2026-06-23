# Shinku-Irodori-TTS

基于 [Irodori-TTS-500M-v3](https://github.com/Aratako/Irodori-TTS) 的二次元角色语音合成工具包，提供 LoRA 微调和 OpenAI 兼容 API 服务器。

> ⚠️ 本仓库仅包含增量文件，不包含原项目代码。使用前请先安装原项目。

## 目录

- [使用流程](#使用流程)
- [配置要求](#配置要求)
- [文件说明](#文件说明)
- [API 参考](#api-参考)
- [参数调优](#参数调优)
- [AstrBot 集成](#astrbot-集成)
- [训练新角色](#训练新角色)
- [常见问题](#常见问题)

## 使用流程

### 1. 安装原项目

```bash
git clone https://github.com/Aratako/Irodori-TTS.git
cd Irodori-TTS
uv sync --extra cu128
```

### 2. 添加本仓库文件

将本仓库所有文件复制到 `Irodori-TTS/` 目录下：

```
Irodori-TTS/
├── api_server.py                     ← 新增
├── generate_manifest.py              ← 新增
├── configs/train_500m_v3_lora_shinku.yaml  ← 新增
└── ... (原项目文件保持不变)
```

### 3. 下载基础模型

从 HuggingFace 下载 [Irodori-TTS-500M-v3](https://huggingface.co/Aratako/Irodori-TTS-500M-v3)（约 2GB）：

```bash
huggingface-cli download Aratako/Irodori-TTS-500M-v3 --local-dir models/Irodori-TTS-500M-v3
```

### 4. 获取 LoRA 权重（二选一）

**已有训练好的 LoRA**：放入 `outputs/shinku_lora/checkpoint_final/`

**自行训练**：参考下方[训练新角色](#训练新角色)

### 5. 启动 API 服务器

```bash
set IRODORI_LORA=outputs/shinku_lora/checkpoint_final
set IRODORI_DEFAULT_REF=outputs\shinku_lora\checkpoint_final\ref_audio.ogg
set IRODORI_PORT=8088
uv run python api_server.py
```

### 6. 测试

```bash
curl -o output.wav -X POST http://localhost:8088/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"irodori-tts","input":"こんにちは"}'
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IRODORI_LORA` | 空 | LoRA 适配器路径 |
| `IRODORI_DEFAULT_REF` | 空 | 参考音频路径 |
| `IRODORI_PORT` | `8088` | API 端口 |
| `IRODORI_DEVICE` | `cuda` | 运行设备 |
| `IRODORI_CHECKPOINT` | `models/Irodori-TTS-500M-v3/model.safetensors` | 基础模型路径 |

## 配置要求

### 硬件

| 项目 | 最低 | 推荐 |
|------|------|------|
| GPU | 8GB VRAM | 12GB+ VRAM |
| 内存 | 16GB | 32GB |
| 硬盘 | 10GB | 20GB+ |

### 软件

- Python 3.10 ~ 3.12
- CUDA 12.8（GPU 训练/推理）
- [uv](https://docs.astral.sh/uv/) 包管理器

## 文件说明

| 文件 | 作用 |
|------|------|
| `api_server.py` | OpenAI 兼容 TTS API 服务器 |
| `generate_manifest.py` | 音频清单生成脚本 |
| `configs/train_500m_v3_lora_shinku.yaml` | LoRA 训练配置 |

## API 参考

`POST /v1/audio/speech`，返回 WAV 音频。

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input` | string | — | 待合成文本（必填） |
| `speed` | float | `0.6` | 语速 |
| `steps` | int | `40` | 采样步数 |
| `text_scale` | float | `4.0` | 文本引导强度 |
| `speaker_scale` | float | `5.0` | 说话人特征强度 |

### 完整示例

```json
{
  "model": "irodori-tts",
  "input": "おやすみなさい、管理人様",
  "speed": 0.6,
  "steps": 50,
  "text_scale": 4.0,
  "speaker_scale": 5.0
}
```

## 参数调优

### 语速 (speed)

| 值 | 效果 |
|----|------|
| `0.5` | 较慢，沉稳 |
| `0.6` | 稍慢（默认） |
| `0.8` | 正常 |
| `1.0` | 偏快 |

### 语气 (text_scale / speaker_scale)

| 效果 | text_scale | speaker_scale |
|------|-----------|--------------|
| 平淡自然 | `4.0` | `4.0` |
| 温柔 | `5.0` | `5.0` |
| 活泼 | `3.0` | `6.0` |
| 沉稳 | `5.0` | `3.0` |
| 默认 | `4.0` | `5.0` |

### 音质 (steps)

- `30`: 快速，适合批量测试
- `40`: 均衡（默认）
- `50`: 高音质

## AstrBot 集成

插件配置：

```json
{
  "tts_provider": "openai_tts",
  "openai_api_base": "http://host.docker.internal:8088/v1",
  "openai_tts_model": "irodori-tts",
  "openai_api_key": "sk-placeholder"
}
```

## 训练新角色

### 准备数据

manifest JSONL 格式：

```jsonl
{"text": "...", "audio": "path/to/audio.ogg", "speaker_id": "shinku"}
```

### 生成清单

```bash
uv run python generate_manifest.py \
  --audio-dir path/to/audio_folder \
  --output data/manifest.jsonl \
  --speaker-id my_speaker
```

### 预计算 latents

```bash
uv run --no-sync python precompute_latents.py \
  --manifest data/manifest.jsonl \
  --output-dir data/latents
```

### 训练

```bash
uv run --no-sync python train.py \
  --config configs/train_500m_v3_lora_shinku.yaml \
  --manifest data/manifest_with_latents.jsonl \
  --init-checkpoint models/Irodori-TTS-500M-v3/model.safetensors \
  --output-dir outputs/my_lora
```

训练配置参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `train.max_steps` | `2000` | 总步数 |
| `train.learning_rate` | `0.0001` | 学习率 |
| `train.batch_size` | `8` | 批次大小 |
| `train.lora_r` | `16` | LoRA 秩 |
| `train.precision` | `bf16` | 训练精度 |

## 常见问题

**Q: CUDA 不可用？**
确认 CUDA 12.8 已安装，运行 `uv run python -c "import torch; print(torch.cuda.is_available())"` 检查。

**Q: Docker 无法连接 API？**
用 `host.docker.internal` 代替 `localhost`。

**Q: 音质差？**
增加 `steps` 到 50；确认 LoRA 路径和参考音频正确。

**Q: 语速不对？**
调整 `speed` 参数，以 ±0.1 微调。

## 版权说明

本仓库仅包含增量工具代码。基础模型和 LoRA 权重的版权归属各自权利人。使用时请遵守原项目 [MIT License](https://github.com/Aratako/Irodori-TTS/blob/main/LICENSE)。
