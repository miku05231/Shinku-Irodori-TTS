# Shinku-Irodori-TTS

基于 [Irodori-TTS-500M-v3](https://github.com/Aratako/Irodori-TTS) 的二阶堂真红（Shinku）语音合成模型，提供 OpenAI 兼容 API 服务器。

## 🎯 这是什么

这是一个**预训练好的** Shinku 声音模型，你可以直接下载使用，无需训练。

- 🎤 基于 71 条 Shinku 语音样本训练
- 🔌 OpenAI TTS API 兼容，可直接替换
- 🤖 支持 AstrBot 等聊天机器人集成
- 🖥️ 提供 Web UI 和命令行工具

## 📦 快速开始

### 1. 安装原项目

```bash
git clone https://github.com/Aratako/Irodori-TTS.git
cd Irodori-TTS
uv sync --extra cu128
```

### 2. 下载基础模型

```bash
huggingface-cli download Aratako/Irodori-TTS-500M-v3 --local-dir models/Irodori-TTS-500M-v3
```

### 3. 下载 Shinku LoRA 权重

从 [Releases](https://github.com/miku05231/Shinku-Irodori-TTS/releases) 下载 `shinku_lora.zip`，解压到 `outputs/shinku_lora/`：

```
outputs/shinku_lora/checkpoint_final/
├── adapter_model.safetensors  (81MB)
├── adapter_config.json
├── config.json
└── irodori_lora_metadata.json
```

### 4. 启动 API 服务器

**方式一：一键启动（Windows）**
```bash
start_server.bat
```

**方式二：手动启动**
```bash
set IRODORI_LORA=outputs/shinku_lora/checkpoint_final
set IRODORI_PORT=8088
uv run python api_server.py
```

### 5. 测试

```bash
curl -o output.wav -X POST http://localhost:8088/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"irodori-tts","input":"こんにちは"}'
```

播放 `output.wav` 即可听到 Shinku 的声音。

## 📋 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IRODORI_LORA` | 空 | LoRA 适配器路径（必填） |
| `IRODORI_DEFAULT_REF` | 空 | 参考音频路径（可选，不设则用 no_ref 模式） |
| `IRODORI_HOST` | `127.0.0.1` | 监听地址（`0.0.0.0` 允许外部访问） |
| `IRODORI_PORT` | `8088` | API 端口 |
| `IRODORI_DEVICE` | `cuda` | 运行设备 |
| `IRODORI_CHECKPOINT` | `models/Irodori-TTS-500M-v3/model.safetensors` | 基础模型路径 |

> ⚠️ **安全提示**：API 默认绑定 `127.0.0.1` 仅本机可访问。如需外部访问（如 Docker 或局域网），设置 `IRODORI_HOST=0.0.0.0`，但请注意**API 无认证机制**，暴露在网络上可能导致滥用。

## 🔧 API 参考

`POST /v1/audio/speech`，返回 WAV 音频。

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input` | string | — | 待合成文本（必填） |
| `voice` | string | `null` | 参考音频路径（可选，不传则用 IRODORI_DEFAULT_REF 或 no_ref 模式） |
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

### 健康检查

```bash
curl http://localhost:8088/health
```

返回：
```json
{"status": "ready", "model_loaded": true}
```

## 🎨 参数调优

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

## 🤖 AstrBot 集成

插件配置：

```json
{
  "tts_provider": "openai_tts",
  "openai_api_base": "http://host.docker.internal:8088/v1",
  "openai_tts_model": "irodori-tts",
  "openai_api_key": "***"
}
```

## 🖥️ Web UI（可选）

原项目提供 Gradio Web UI，适合可视化调试：

```bash
# 标准版 UI
uv run python gradio_app.py

# VoiceDesign 版 UI（支持语音设计功能）
uv run python gradio_app_voicedesign.py
```

启动后访问 `http://localhost:7860` 即可使用 Web 界面。

## 📁 文件说明

| 文件 | 作用 |
|------|------|
| `api_server.py` | OpenAI 兼容 TTS API 服务器 |
| `generate_manifest.py` | 音频清单生成脚本（训练用） |
| `configs/train_500m_v3_lora_shinku.yaml` | LoRA 训练配置（训练用） |
| `start_server.bat` | Windows 一键启动脚本 |

## ❓ 常见问题

**Q: CUDA 不可用？**
确认 CUDA 12.8 已安装，运行 `uv run python -c "import torch; print(torch.cuda.is_available())"` 检查。

**Q: Docker 无法连接 API？**
用 `host.docker.internal` 代替 `localhost`。

**Q: 音质差？**
增加 `steps` 到 50；确认 LoRA 路径正确。

**Q: 语速不对？**
调整 `speed` 参数，以 ±0.1 微调。

**Q: 如何训练自己的声音模型？**
参考下方[训练新角色](#训练新角色)章节。

---

## 🚀 训练新角色（可选）

如果你想训练自己的声音模型，可以参考以下流程。

### 配置要求

| 项目 | 最低 | 推荐 |
|------|------|------|
| GPU | 8GB VRAM | 12GB+ VRAM |
| 内存 | 16GB | 32GB |
| 硬盘 | 10GB | 20GB+ |

### 训练流程

```
本地音频 (*.wav/*.mp3/*.ogg/*.flac/*.m4a)
    │
    ▼
generate_manifest.py         ← 第1步：扫描音频目录，生成 manifest（含 audio 路径）
    │
    ▼  data/train_manifest.jsonl
    │
prepare_manifest.py          ← 第2步：加载 manifest，计算 DACVAE latents，输出最终 manifest
    │
    ▼  data/train_manifest_with_latents.jsonl
    │
train.py                     ← 第3步：LoRA 训练
```

### 第1步：生成初始 manifest

```bash
uv run python generate_manifest.py \
  --audio-dir path/to/audio/folder \
  --output data/train_manifest.jsonl \
  --speaker-id my_speaker
```

输出示例：
```jsonl
{"text": "...", "audio": "/path/to/voice_00001.ogg", "speaker_id": "my_speaker"}
```

> ⚠️ **关于占位文本**：默认情况下，`generate_manifest.py` 使用占位文本（`このテキストは話者埋め込み学習用です。`）。这对于 speaker embedding 训练没问题，但如果要做带真实台词的训练，需要替换为实际文本。可以使用 `--text` 参数指定自定义文本，或在生成后用脚本批量替换 JSONL 文件中的 `text` 字段。

### 第2步：计算 DACVAE latents

使用原项目的 `prepare_manifest.py`，从 JSONL 加载音频并计算 latents：

```bash
uv run --no-sync python prepare_manifest.py \
  --dataset json \
  --data-files data/train_manifest.jsonl \
  --audio-column audio \
  --text-column text \
  --speaker-column speaker_id \
  --speaker-id-prefix shinku \
  --output-manifest data/train_manifest_with_latents.jsonl \
  --latent-dir data/latents \
  --device cuda
```

输出：`data/train_manifest_with_latents.jsonl`（含 `latent_path` 和 `num_frames` 字段）。

> `--dataset json` 是必需的，表示使用 HuggingFace `datasets` 内置的 JSON loader 加载本地 JSONL 文件。`--speaker-id-prefix shinku` 用于在输出 manifest 中生成干净的 speaker_id（如 `shinku::my_speaker`），不加则默认以 `json` 作为前缀。

### 第3步：LoRA 训练

```bash
uv run --no-sync python train.py \
  --config configs/train_500m_v3_lora_shinku.yaml \
  --manifest data/train_manifest_with_latents.jsonl \
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

训练完成后，LoRA 权重位于 `outputs/my_lora/checkpoint_final/`。

## 📄 版权说明

本仓库仅包含增量工具代码。基础模型和 LoRA 权重的版权归属各自权利人。使用时请遵守原项目 [MIT License](https://github.com/Aratako/Irodori-TTS/blob/main/LICENSE)。
