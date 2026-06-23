#!/usr/bin/env python3
"""Generate manifest JSONL for speaker embedding training."""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_TEXT = "このテキストは話者埋め込み学習用です。"

def main():
    parser = argparse.ArgumentParser(description="Generate training manifest")
    parser.add_argument("--audio-dir", type=str, required=True,
                        help="Audio directory")
    parser.add_argument("--output", type=str, required=True,
                        help="Output JSONL path")
    parser.add_argument("--speaker-id", type=str, default="shinku",
                        help="Speaker ID (default: shinku)")
    parser.add_argument("--text", type=str, default=DEFAULT_TEXT,
                        help="Placeholder text")
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir)
    if not audio_dir.is_dir():
        print(f"Error: Audio directory not found: {audio_dir}")
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 直接按扩展名搜索，避免先搜索所有文件再过滤
    exts = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}
    audio_files = []
    for ext in exts:
        audio_files.extend(audio_dir.rglob(f"*{ext}"))
    audio_files = sorted(audio_files)

    print(f"Found {len(audio_files)} audio files in {audio_dir}")

    with open(output_path, "w", encoding="utf-8") as f:
        for audio_path in audio_files:
            entry = {
                "text": args.text,
                "audio": audio_path.as_posix(),
                "speaker_id": args.speaker_id,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Manifest written to {output_path}")

if __name__ == "__main__":
    main()
