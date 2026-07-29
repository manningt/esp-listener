'''
captures a 3 second 8Khz sample from an i2s microphone and stores it in flash as a .bin file
'''
from machine import Pin, I2S # pyrefly: ignore [missing-import]
import math
from time import sleep

# 2 bytes per sample, 8000 samples per second, 3 seconds
MIC_BUFFER_SIZE = (8000 * 2 * 3)
'''
#TinyPico
sck_pin = Pin(25) #           green in pair with yellow
ws_pin = Pin(26)  # Word strobe  purple
sd_pin = Pin(27)  # yellow
'''
#TinyS3; defaults https://docs.espressif.com/projects/esp-idf/en/v4.4/esp32s3/api-reference/peripherals/i2s.html
# default sd pin is 18 (not 3)
sck_pin = Pin(4) #  orange
ws_pin = Pin(5)  # yellow
sd_pin = Pin(3)  # brown 

# the Left/Right select pin must be low; maybe because of mono format
sel_pin = Pin(14, Pin.OUT) # Select green
sel_pin.value(0)

I2S_PORT_ID = 1
audio_in = I2S(I2S_PORT_ID, mode=I2S.RX, sck=sck_pin, ws=ws_pin, sd=sd_pin, \
    bits=16, format=I2S.MONO, rate=8000, ibuf=MIC_BUFFER_SIZE)

mic_samples = bytearray(MIC_BUFFER_SIZE)

def calculate_rms(data, offset):
    sum_squares = 0.0
    num_samples = len(data) // 2
    for i in range(offset, len(data), 2):
        sample = int.from_bytes(data[i:i+2], 'little')
        # Signed 16-bit
        if sample >= 32768:
            sample -= 65536
        sum_squares += sample * float(sample)
    if num_samples == 0:
        return 0
    print(f"{sum_squares=} {num_samples=}")
    return math.sqrt(sum_squares / num_samples)

def sample(iterations = 3):
    OFFSET = 0
    for i in range(iterations):
        num_read = audio_in.readinto(mic_samples)
        if i == 0:
            print(f"sample buffer={num_read} bytes")
        rms = calculate_rms(mic_samples, OFFSET)
        print(f"RMS={rms:.2f}")
        sleep(1)

    filename = "output.bin"
    with open(filename, 'wb') as f:
        f.write(mic_samples)
        print(f"wrote {filename}")
