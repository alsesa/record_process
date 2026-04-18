import argparse
import os
import re
import subprocess
from pathlib import Path

from pydub import AudioSegment
from opencc import OpenCC

from logging_config import setup_logging
from transcribe_media import extract_or_convert_audio, transcribe_audio_funasr, transcribe_audio_funasr_batch

logger = setup_logging()
opencc_converter = OpenCC("t2s")

RECORD_DIR = Path(__file__).parent / "RECORD"
CONTENT_DIR = Path(__file__).parent / "content"
MENU_FILE = CONTENT_DIR / "menu.md"
FILENAME_PATTERN = re.compile(r"^R(\d{8})-(\d{6})\.WAV$", re.IGNORECASE)
SUPPORTED_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".aac"}


def parse_timestamp(filename: str) -> str | None:
    """Parse recording timestamp from filename like R20260417-000547.WAV."""
    m = FILENAME_PATTERN.match(filename)
    if not m:
        return None
    date_part = m.group(1)
    time_part = m.group(2)
    return f"{date_part[:4]}年{date_part[4:6]}月{date_part[6:]}日{time_part[:2]}时{time_part[2:4]}分{time_part[4:]}秒"


def parse_date(filename: str) -> str | None:
    """Parse date portion from filename like R20260417-000547.WAV -> 20260417."""
    m = FILENAME_PATTERN.match(filename)
    if not m:
        return None
    return m.group(1)


def update_menu(date_str: str, txt_name: str, timestamp: str | None):
    """Add an entry to content/menu.md if it doesn't already exist."""
    link_line = f"- [{timestamp}]({date_str}/{txt_name})\n" if timestamp else f"- [{txt_name}]({date_str}/{txt_name})\n"

    existing = MENU_FILE.read_text(encoding="utf-8") if MENU_FILE.exists() else ""
    if f"({date_str}/{txt_name})" in existing:
        return

    with open(MENU_FILE, "a", encoding="utf-8") as f:
        f.write(link_line)


def process_file(file_path: Path):
    """Process a single recording file through the full pipeline."""
    filename = file_path.name
    logger.info(f"Processing: {filename}")

    # Transcribe
    audio_file = None
    try:
        audio_file = extract_or_convert_audio(str(file_path))
        if audio_file is None:
            logger.warning(f"No audio track in {filename}, skipping")
            return

        # Check audio duration: <=30s use batch, >30s use full model with VAD
        audio_duration_ms = len(AudioSegment.from_file(audio_file))
        if audio_duration_ms <= 30_000:
            logger.info(f"Audio <= 30s, using batch transcription")
            transcript = transcribe_audio_funasr_batch(audio_file)
        else:
            logger.info(f"Audio > 30s ({audio_duration_ms / 1000:.1f}s), using VAD transcription")
            transcript = transcribe_audio_funasr(audio_file)
        logger.info(f"Transcription complete: {filename}")
    except Exception as e:
        logger.error(f"Failed to transcribe {filename}: {e}")
        return
    finally:
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)

    # Traditional -> Simplified Chinese
    transcript = opencc_converter.convert(transcript)

    # Prepend recording timestamp
    timestamp = parse_timestamp(filename)
    if timestamp:
        transcript = f"Record Time: {timestamp}\n{transcript}"

    # Save transcript to content/{date}/ folder
    date_str = parse_date(filename)
    if date_str:
        dest_folder = CONTENT_DIR / date_str
        dest_folder.mkdir(parents=True, exist_ok=True)
        txt_name = file_path.stem + ".txt"
        txt_path = dest_folder / txt_name
        txt_path.write_text(transcript, encoding="utf-8")
        logger.info(f"Transcript saved: {txt_path}")

        # Update menu.md
        timestamp = parse_timestamp(filename)
        update_menu(date_str, txt_name, timestamp)
    else:
        txt_path = file_path.with_suffix(".txt")
        txt_path.write_text(transcript, encoding="utf-8")
        logger.info(f"Transcript saved: {txt_path}")

    # macOS notification
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "record file {filename} process finished" '
             f'with title "record to text fast" subtitle "convert success" sound name "default"'],
            capture_output=True,
        )
    except FileNotFoundError:
        pass


def main():
    parser = argparse.ArgumentParser(description="Process voice recordings to text.")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Audio file(s) to process. Defaults to all WAV files in RECORD/.",
    )
    args = parser.parse_args()

    if args.files:
        files = [f for f in args.files if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS]
    else:
        files = sorted(RECORD_DIR.glob("*.WAV")) + sorted(RECORD_DIR.glob("*.wav"))

    if not files:
        logger.warning("No supported audio files found.")
        return

    logger.info(f"Found {len(files)} file(s) to process")

    for f in files:
        try:
            process_file(f)
        except Exception as e:
            logger.error(f"Unexpected error processing {f}: {e}")

    logger.info("All done!")


if __name__ == "__main__":
    main()
