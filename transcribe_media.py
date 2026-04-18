import os
import argparse
import uuid

from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment

from logging_config import setup_logging

logger = setup_logging()


def extract_or_convert_audio(file_path, output_audio_path="processed_audio"):
    ext = os.path.splitext(file_path)[1].lower()
    random_uuid = str(uuid.uuid4())
    output_audio_path = output_audio_path + "_" + random_uuid + ".wav"

    if ext in [".mp4", ".mov", ".avi", ".mkv"]:
        logger.info("🎬 Extracting audio from video...")
        video = VideoFileClip(file_path)
        if video.audio is None:
            print("⚠️ 警告：该视频没有音频轨道。")
            return None
        video.audio.write_audiofile(output_audio_path)
    elif ext in [".mp3", ".wav", ".flac", ".m4a", ".aac"]:
        logger.info("🎧 Converting audio format...")
        sound = AudioSegment.from_file(file_path)
        sound.export(output_audio_path, format="wav")
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    logger.info(f"Converted Audio saved to: {output_audio_path}")

    return output_audio_path


def transcribe_audio_funasr(audio_path, device="cpu"):
    logger.info("🧠 Loading FunASR model...")
    model = AutoModel(
        model="iic/SenseVoiceSmall",
        trust_remote_code=True,
        remote_code="./SenseVoice/model.py",  # Make sure this file is accessible
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        device=device,
        disable_update=True
    )

    logger.info("📤 Transcribing with FunASR...")
    res = model.generate(
        input=audio_path,
        cache={},
        language="auto",
        use_itn=True,
        batch_size_s=60,
        merge_vad=True,
        merge_length_s=15,
    )

    text = rich_transcription_postprocess(res[0]["text"])
    return split_into_sentences(text)


# 加载模型并作为全局变量
default_model = AutoModel(model="iic/SenseVoiceSmall", trust_remote_code=True, device="cpu", disable_update=True)

def transcribe_audio_funasr_batch(audio_path):
    try:
        res = default_model.generate(
            input=audio_path,
            cache={},
            language="auto",
            use_itn=True,
            batch_size=64,
        )

        text = rich_transcription_postprocess(res[0]["text"])
        transcribe_content =  split_into_sentences(text)
    except:
        logger.info("transcribe audio batch fail, using no batch method")
        transcribe_content = transcribe_audio_funasr(audio_path)

    return transcribe_content



# 新增：用于句子分割的符号列表
SENTENCE_ENDINGS = ["。", "！", "？", ".", "!", "?", "\n"]


def split_into_sentences(text, max_length=100):
    """
    将文本按句子结束符分割，并确保每行不超过指定长度

    参数:
    text (str): 待分割的文本
    max_length (int): 每行最大长度

    返回:
    str: 处理后的文本，句子间用换行符分隔
    """
    if not text:
        return ""

    # 首先按句子结束符进行分割
    sentences = []
    current_sentence = ""

    for char in text:
        current_sentence += char
        # 如果遇到句子结束符，则将当前积累的字符添加到句子列表中
        if char in SENTENCE_ENDINGS:
            sentences.append(current_sentence.strip())
            current_sentence = ""

    # 添加最后一个可能不完整的句子
    if current_sentence.strip():
        sentences.append(current_sentence.strip())

    # 然后处理过长的句子，确保每行不超过max_length
    processed_lines = []
    for sentence in sentences:
        if len(sentence) <= max_length:
            processed_lines.append(sentence)
        else:
            # 对于过长的句子，按最大长度分割，但尽量在标点符号处分割
            current_line = ""
            for i, char in enumerate(sentence):
                current_line += char
                # 如果达到最大长度，并且下一个字符是标点符号，或者当前字符是空格，则分割
                if len(current_line) >= max_length:
                    if (i + 1 < len(sentence) and sentence[i + 1] in SENTENCE_ENDINGS) or char == ' ':
                        processed_lines.append(current_line.strip())
                        current_line = ""
            # 添加最后一个片段
            if current_line.strip():
                processed_lines.append(current_line.strip())

    # 用换行符连接所有处理后的行
    return "\n".join(processed_lines)


def convert_media(file_path, is_batch=False, save_to_disk=True):
    audio_file = None
    try:
        audio_file = extract_or_convert_audio(file_path)
        if audio_file is None:
            return None

        if is_batch:
            transcript = transcribe_audio_funasr_batch(audio_file)
        else:
            transcript = transcribe_audio_funasr(audio_file)

        logger.info("\n📜 Transcript:")
        logger.info(transcript)

        # ✅ Save transcript to disk as .txt file
        if save_to_disk:
            output_path = os.path.splitext(file_path)[0] + ".txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            logger.info(f"✅ Transcript saved to: {output_path}")
        return transcript
    finally:
        if audio_file and os.path.exists(audio_file):
            try:
                # 确保文件已关闭再尝试删除
                import gc
                gc.collect()  # 强制垃圾回收，释放可能占用文件的引用
                os.remove(audio_file)
                logger.info(f"Temporary audio file removed: {audio_file}")
            except OSError as e:
                logger.error(f"Failed to remove temporary audio file {audio_file}: {e}")


def process_input(path, recursive=False):
    if not os.path.exists(path):
        logger.error(f"❌ Path does not exist: {path}")
        return

    supported_exts = {".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".flac", ".m4a", ".aac"}

    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in supported_exts:
            convert_media(path)
        else:
            logger.warning(f"🚫 Unsupported file skipped: {path}")
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_exts:
                    try:
                        convert_media(file_path, False)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                else:
                    logger.debug(f"Skipping non-media file: {file_path}")
            if not recursive:
                break


def main():
    parser = argparse.ArgumentParser(description="Convert audio/video to text using FunASR.")
    parser.add_argument("input_path", nargs='?', default="./media", help="Path to a file or folder containing media files. Defaults to './media'.")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process subdirectories recursively.")
    args = parser.parse_args()

    input_path = args.input_path
    process_input(input_path, recursive=args.recursive)


if __name__ == '__main__':
    main()