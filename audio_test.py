import os
import math
import random
import time
from pydub import AudioSegment
import simpleaudio as sa
from SoundPlayer import SoundPlayer

# Create sample list
SAMPLE_FOLDER = "samples"
samples = {}

# Locate the sample and check the files
for file in sorted(os.listdir(SAMPLE_FOLDER)):
    if file.endswith(".mp3"):
        key = int(file.split("_")[0])
        samples[key] = os.path.join(SAMPLE_FOLDER, file)

# Print the samples to verify
print("Samples found:", samples)

# Change pitch
def change_pitch(file_path, pitch_shift):
    sound = AudioSegment.from_file(file_path)
    new_frame_rate = int(sound.frame_rate * (2 ** (pitch_shift / 12)))  # Pitch shift in semitones
    return sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate}).set_frame_rate(44100)

# Play sound
def play_sound(sound):
    playback = sa.play_buffer(sound.raw_data, num_channels=sound.channels, bytes_per_sample=sound.sample_width, sample_rate=sound.frame_rate)
    # playback.wait_done()

def get_pitch_times(g, base_freq=261.63):
    g_to_semitone = {
        1: 0,   # C
        2: 2,   # D
        3: 4,   # E
        4: 5,   # F
        5: 7,   # G
        6: 9,   # A
        7: 11   # B
    }

    if g not in g_to_semitone:
        raise ValueError("G must be between 1 and 7.")

    n = g_to_semitone[g]
    pitch_times = math.pow(2, n / 12)
    return pitch_times

def main():
    # Ensure a sample exists for key 1

    # soundPlayers = []
    # for i, sample in enumerate(samples):
    #     soundPlayers[i] = SoundPlayer(samples)
    
    if 2 in samples:
        selected_sample = samples[2]  
        print(f"Playing: {selected_sample}")
        for i in range(20):
            start_time = time.time()
            pitch_index = math.floor(random.randint(1, 7))
            pitch_times = get_pitch_times(pitch_index)
            pitch_shift = math.log2(pitch_times) * 12
            modified_sound = change_pitch(selected_sample, math.log2(pitch_times) * 12)  
            play_sound(modified_sound)

            sleep_time = random.uniform(0, 3)
            time.sleep(sleep_time)
            end_time = time.time()
            print(end_time - start_time)
    else:
        print("Sample 3 not found in the samples folder.")

if __name__ == "__main__":
    main()