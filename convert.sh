PATH=$PATH:/opt/homebrew/bin/:/bin/;
# source ~/Documents/songyi/.venv/bin/activate
for f in "$@"
do
	base="${f%.*}"  # 去掉文件的后缀
	# ffmpeg -i "$f" -ar 16000 -ac 1 -c:a pcm_s16le "${base}-c.wav"
	# whisper-cpp "${base}-c.wav" -l auto --model ~/Documents/whisper.cpp/models/ggml-small-q8_0.bin -otxt
	# rm "${base}-c.wav"
	# mv "${base}-c.wav.txt" "${base}.txt"
	~/Documents/songyi/.venv/bin/python ~/Documents/songyi/transcribe_media.py "$f"
	# 繁体转换简体
	opencc -c t2s -i "${base}.txt" -o "${base}.txt"
	# 发送转换成功通知
	# osascript -e "display notification \"file $f convert finished\" with title \"voice to text fast\" subtitle \"convert success\" sound name \"default\""
	# 提取录音文件的录制时间
	RECORD_TIME=$(echo "$f" | grep -oE 'R[0-9]{8}-[0-9]{6}' | sed 's/R//')
	TIME=$(echo "$RECORD_TIME" | sed -E 's/^([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})([0-9]{2})$/\1年\2月\3日\4时\5分\6秒/')
	# 在文本文件的第一行添加录制时间
	sed -i '' "1s/^/Record Time: $TIME\n/" "${base}.txt"
	# 提取日期部分
	RECORD_DATE=$(echo "$f" | grep -oE 'R[0-9]{8}' | sed 's/R//')
	# 创建日期文件夹
	DEST_FOLDER="/Users/yuanhui/Music/RECORD/$RECORD_DATE"
	mkdir -p "$DEST_FOLDER"
	# 移动文件到日期文件夹
	mv "$f" "$DEST_FOLDER"
	mv "${base}.txt" "$DEST_FOLDER"
	# 发送处理成功通知
	osascript -e "display notification \"record file $f process finished\" with title \"record to text fast\" subtitle \"convert success\" sound name \"default\""
done