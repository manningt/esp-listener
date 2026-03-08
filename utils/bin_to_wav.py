

import wave
import argparse
import sys
import os

def convert_bin_to_wav(input_file, output_file, sample_rate, channels, sample_width):
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    try:
        with open(input_file, 'rb') as bin_file:
            pcm_data = bin_file.read()

        with wave.open(output_file, 'wb') as wav_file:
            # Set parameters
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            
            # Write frames
            wav_file.writeframes(pcm_data)
        
        print(f"Successfully converted '{input_file}' to '{output_file}'")
        print(f"  Settings: {sample_rate} Hz, {channels} Channel(s), {sample_width} Byte(s) per sample")

    except Exception as e:
        print(f"An error occurred during conversion: {e}")
        sys.exit(1)

def main():

    parser = argparse.ArgumentParser(description="Convert raw binary audio file to WAV.")
    parser.add_argument("input_file", help="Path to the input binary file")
    parser.add_argument("output_file", nargs='?', help="Path to the output WAV file (optional, defaults to input filename with .wav)")
    parser.add_argument("--rate", type=int, default=8000, help="Sample rate in Hz (default: 8000)")
    parser.add_argument("--channels", type=int, default=1, help="Number of channels (default: 1)")
    parser.add_argument("--width", type=int, default=2, help="Sample width in bytes (default: 2 for 16-bit)")

    args = parser.parse_args()

    input_path = args.input_file
    output_path = args.output_file

    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}.wav"

    convert_bin_to_wav(input_path, output_path, args.rate, args.channels, args.width)

if __name__ == "__main__":
    main()
