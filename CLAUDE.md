# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A voice recording-to-text pipeline for macOS. Takes `.WAV` recordings (filenames like `R20260417-000547.WAV` encoding timestamps), transcribes them to Chinese text using Alibaba's SenseVoiceSmall model via FunASR, converts traditional to simplified Chinese, and organizes output into date-based folders.

## Commands

```bash
# Install/sync dependencies
uv sync

# Add a dependency
uv add <package>

# Process all WAV files in RECORD/
python main.py

# Process specific files
python main.py RECORD/R20260417-000547.WAV

# Standalone transcription (supports video + audio formats)
python transcribe_media.py [input_path] [--recursive]
```

No tests, linter, or CI/CD are configured.

## Architecture

**Two entry points:**

- **`main.py`** — Primary CLI. Processes `RECORD/*.WAV` files, organizes output to `content/{YYYYMMDD}/`, maintains `content/menu.md` index, sends macOS notifications. Imports core functions from `transcribe_media.py`.
- **`transcribe_media.py`** — Core transcription library + standalone CLI. Supports video (MP4, MOV, AVI, MKV) and audio (MP3, WAV, FLAC, M4A, AAC). `main.py` imports `extract_or_convert_audio()` and `transcribe_audio_funasr()` from here.

**`convert.sh`** is a legacy shell pipeline that predates `main.py`.

**`SenseVoice/`** — Vendored model code from [FunASR/SenseVoice](https://github.com/FunAudioLLM/SenseVoice). Loaded at runtime by FunASR's `AutoModel` via `remote_code="./SenseVoice/model.py"`. Do not modify unless you understand the CTC-based encoder architecture (SANM attention layers, fbank feature extraction, CTC forced alignment).

**Pipeline flow:** WAV file → `extract_or_convert_audio()` (moviepy/pydub conversion to 16kHz) → `transcribe_audio_funasr()` (FunASR AutoModel with SenseVoiceSmall + fsmn-vad) → opencc traditional→simplified → save to `content/{date}/{filename}.txt`

## Key Dependencies

- **funasr** — Speech recognition framework; provides AutoModel, VAD, and model loading
- **torch/torchaudio** — CPU-only PyTorch (no CUDA), installed from `https://download.pytorch.org/whl/cpu`
- **moviepy** — Audio extraction from video files
- **pydub** — Audio format conversion
- **opencc-python-reimplemented** — Traditional-to-simplified Chinese conversion

## Conventions

- Python 3.12 (pinned in `.python-version`)
- Package manager: `uv` (not pip)
- Raw recordings in `RECORD/` are git-ignored; transcripts in `content/` are tracked
- Recording filenames follow pattern `R{YYYYMMDD}-{HHMMSS}.WAV` — the timestamp is parsed for output organization
- Output format: timestamp header line, then transcribed text with sentence-level line breaks (max ~100 chars)