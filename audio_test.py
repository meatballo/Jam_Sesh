import os
import math
import time
import json
import threading
from pydub import AudioSegment
import simpleaudio as sa

# 设置样本文件夹
SAMPLE_FOLDER = "samples"
samples = {}

# 读取samples
for file in sorted(os.listdir(SAMPLE_FOLDER)):
    if file.endswith(".mp3"):
        key = int(file.split("_")[0])
        samples[str(key)] = os.path.join(SAMPLE_FOLDER, file)

# 音高变换
def change_pitch(file_path, pitch_shift):
    sound = AudioSegment.from_file(file_path)
    new_frame_rate = int(sound.frame_rate * (2 ** (pitch_shift / 12)))
    return sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate}).set_frame_rate(44100)

# 播放音频（开新线程，允许重叠）
def play_sound(sound):
    threading.Thread(target=lambda: sa.play_buffer(
        sound.raw_data,
        num_channels=sound.channels,
        bytes_per_sample=sound.sample_width,
        sample_rate=sound.frame_rate
    ).wait_done()).start()

# 根据g值计算频率倍率
def get_pitch_times(g, base_freq=261.63):
    g_to_semitone = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
    if g not in g_to_semitone:
        raise ValueError("G must be between 1 and 7.")
    return math.pow(2, g_to_semitone[g] / 12)

# 输入文件路径
INPUT_FILE = "realtime_input.txt"

# 监听输入
def monitor_input():
    last_processed_line = ""
    while True:
        try:
            with open(INPUT_FILE, "r") as f:
                lines = f.readlines()
                if not lines:
                    time.sleep(0.05)
                    continue

                # 只处理最后一行
                line = lines[-1].strip()
                if line == last_processed_line or not line:
                    time.sleep(0.05)
                    continue
                last_processed_line = line

                try:
                    # 去掉空格，转小写，解析json
                    clean_line = line.strip().lower()
                    data = json.loads(clean_line)
                    
                    if not isinstance(data, list) or len(data) != 3:
                        print(f"Invalid data format: {line}")
                        continue
                    
                    is_active, sample_key, g = data

                    if is_active and str(sample_key) in samples:
                        pitch_shift = math.log2(get_pitch_times(int(g))) * 12
                        sound = change_pitch(samples[str(sample_key)], pitch_shift)
                        play_sound(sound)

                except json.JSONDecodeError as e:
                    print("JSON decode error:", e)
                    print("Problematic line:", repr(line))
                    time.sleep(0.1)
                except Exception as e:
                    print("Error processing line:", e)
                    time.sleep(0.1)

            time.sleep(0.01)
        except FileNotFoundError:
            print(f"Input file '{INPUT_FILE}' not found. Waiting...")
            time.sleep(1)
        except Exception as e:
            print("File read error:", e)
            time.sleep(0.5)

if __name__ == "__main__":
    monitor_input()
