import wave
import struct
import argparse
import math

def calculate_rms(wav_file_path, offset=0):
    with wave.open(wav_file_path, 'rb') as wav_file:
        n_channels = wav_file.getnchannels()
        sampwidth = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()

        if n_channels != 1:
            print("Error: only mono WAV files are supported")
            return 0.0
        if sampwidth != 2:
            print("Error: only 16-bit WAV files are supported")
            return 0.0
        if framerate != 8000:
            print("Error: only 8000 Hz WAV files are supported")
            return 0.0

        frames = wav_file.readframes(n_frames)
        if len(frames) == 0:
            print("empty frames")
            return 0.0

        # for unpack: <h is little-endian 16-bit signed int
        fmt = f'{len(frames)//2}h'
        samples = list(struct.unpack("<" + fmt, frames))
        sum_sq = 0.0
        normalized_sum_sq = 0.0
 
        for i in range(int(offset/2), len(samples)):
            sum_sq += samples[i] * float(samples[i])
            normalized_sample = samples[i] / 32767
            normalized_sum_sq += normalized_sample * normalized_sample

    rms = math.sqrt(sum_sq / (len(samples) - offset))
    normalized_rms = math.sqrt(normalized_sum_sq / (len(samples) - offset))
    return rms, normalized_rms

def to_dbfs(rms):
    if rms <= 0:
        return float("-inf")
    return 20.0 * math.log10(rms)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate RMS of a WAV file.")
    parser.add_argument("input_file", help="Path to the input WAV file")

    args = parser.parse_args()

    input_path = args.input_file

    rms_value, normalized_rms_value = calculate_rms(input_path, offset=0)
    dbfs = to_dbfs(rms_value)
    dbfs = to_dbfs(normalized_rms_value)
    print(f'The RMS value of the audio file is: linear: {rms_value:.1f}, normalized: {normalized_rms_value:.3f}, dbfs: {dbfs:.3f}')
