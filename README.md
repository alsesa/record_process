# record_process

Voice recording-to-text pipeline for macOS. Transcribes `.WAV` recordings to Chinese text using Alibaba's SenseVoiceSmall model via FunASR, converts traditional to simplified Chinese, and organizes output into date-based folders.

## Prerequisites

- Python 3.12+
- FFmpeg

## Installation

```bash
uv sync

# Install PyTorch CPU-only build
uv pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cpu
```

## Usage

```bash
# Process all WAV files in RECORD/
python main.py

# Process specific files
python main.py RECORD/R20260417-000547.WAV

# Standalone transcription (supports video + audio: MP4, MOV, WAV, MP3, FLAC, M4A, AAC)
python transcribe_media.py [input_path] [--recursive]
```

Transcripts are saved to `content/{YYYYMMDD}/{filename}.txt`. An index is maintained at `content/menu.md`.

Recording filenames follow the pattern `R{YYYYMMDD}-{HHMMSS}.WAV` — the timestamp is used to organize output into date-based directories.

## How It Works

1. Audio is extracted/converted to 16kHz WAV (via moviepy for video, pydub for audio)
2. Transcribed using SenseVoiceSmall with VAD (`fsmn-vad`) for speech segmentation
3. Traditional Chinese characters are converted to simplified Chinese (opencc)
4. Output is saved with a timestamp header and sentence-level line breaks
5. A macOS notification is sent on completion