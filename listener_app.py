from support import write_rtc_memory, restore_from_rtc_memory, \
   read_config, my_deep_sleep, setup_station, setup_ftp, mem_status
from machine import Pin, I2S
import math
import sys

def calculate_rms(data, offset):
    sum_squares = 0.0
    num_samples = len(data) // 2
    for i in range(offset, len(data), 2):
        sample = int.from_bytes(data[i:i+2], 'little')
        # Signed 16-bit
        if sample >= 32768:
            sample -= 65536
        sum_squares += sample * float(sample)
            
    # print(f'offset: {offset}, len(data): {len(data)}, sum_sq: {sum_squares}')
    if num_samples == 0:
        return 0
    return math.sqrt(sum_squares / num_samples)

def main():
   try:
      import tinypico
      tinypico.set_dotstar_power(False)
   except:
      pass
   I2S_PORT_ID = 1
   # MIC_BUFFER_SIZE = (8000 * 2 * 3)
   MIC_BUFFER_SIZE = (8000 * 2)

   count_state = restore_from_rtc_memory()
   if count_state is None:
      count_state = {"wake_count": 0, "thold_count": 0}
      write_rtc_memory(count_state)

   config = read_config()
   if config is None:
      print("No config; calling deep sleep")
      my_deep_sleep(15)

   # print debug info on first wake:
   if count_state["wake_count"] == 0:
      print(f"{config=}")
      mem_status()

   if 'sampling' in config:
      tmp = config['sampling']['sample_minutes']
      if isinstance(tmp, float) or isinstance(tmp, int):
         deep_sleep_seconds = int(60*tmp)
      else:
         print(f"Quitting: invalid sample_minutes={tmp}")
         sys.exit(0)
   else:
      print("Quitting: Missing 'sampling' in config json file")
      sys.exit(0)


   if 'i2s_pins' in config:
      audio_in = I2S(I2S_PORT_ID, mode=I2S.RX, \
         sck=config['i2s_pins']['sck'], sd=config['i2s_pins']['sd'], ws=config['i2s_pins']['wstrobe'], \
         bits=16, format=I2S.MONO, rate=8000, ibuf=MIC_BUFFER_SIZE)
      mic_samples = bytearray(MIC_BUFFER_SIZE)
      select_pin = Pin(config['i2s_pins']['select'], Pin.OUT)
      select_pin.value(0)    
      num_read = audio_in.readinto(mic_samples)
      if num_read != MIC_BUFFER_SIZE:
         print(f"Error: samples read={num_read}; expected={MIC_BUFFER_SIZE}")
      else:
         rms = calculate_rms(mic_samples, 0)
         print(f'RMS: {rms:.2f}')

         increment_thold_count = False
         if config['sampling']['below_above'] == 1:
            if rms > config['sampling']['threshold']:
               increment_thold_count = True
         elif rms < config['sampling']['threshold']:
            increment_thold_count = True

         if increment_thold_count:
            count_state['thold_count'] +=1
         elif count_state['thold_count'] > 0:
            count_state['thold_count'] -=1
            
         count_state['wake_count'] +=1
         write_rtc_memory(count_state)
   else:
      print("No i2s config")

   if count_state['thold_count'] > config['sampling']['thold_count_limit']:
      # report threshold exceeded, reset thold_count and set deep_sleep to report interval
      print(f"thold_count={count_state['thold_count']} > thold_limit={config['sampling']['thold_count_limit']}")
      count_state['thold_count'] = 0
      tmp = config['sampling']['report_hours']
      if isinstance(tmp, float) or isinstance(tmp, int):
         deep_sleep_seconds = int(tmp*3600)
      else:
         print(f"Warning: invalid report_hours={tmp}; using 4 hours")
         deep_sleep_seconds = 14400

      if "wifi" in config:
         station = setup_station(config['wifi']['ssid'], config['wifi']['password'])
         if station is None:
            print("WiFi not connecting")
      else:
         print("No wifi config")

      if "ftp" in config:
         host = config['ftp']['host']
         ftp = setup_ftp(host, config['ftp']['user'], config['ftp']['password'])
         if ftp is None:
            print(f"FTP setup to {host} failed")
         else:
            battery_voltage = get_bat_volt_int()
            send_battery_voltage(host,battery_voltage)
            ftp.quit()
         # try:
         #    ftp.cwd('epaper')
         # except Exception as e:
         #    print(f"{e} on cwd to epaper")
         #    my_deep_sleep(config['sleep'])
      else:
         print("no ftp config")

   my_deep_sleep(deep_sleep_seconds)
