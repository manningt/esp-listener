from support import write_rtc_memory, restore_from_rtc_memory, \
   read_config, my_deep_sleep, setup_station, setup_ftp, mem_status
from machine import Pin, I2S
import math
import sys
import requests

# MIC_BUFFER_SIZE = (8000 * 2 * 3)
MIC_BUFFER_SIZE = (8000 * 2)

def get_rms(audio_in):
   mic_samples = bytearray(MIC_BUFFER_SIZE)
   num_read = audio_in.readinto(mic_samples)
   if num_read != MIC_BUFFER_SIZE:
      print(f"Error: samples read={num_read}; expected={MIC_BUFFER_SIZE}")
      rms = 0
   else:
      sum_squares = 0.0
      num_samples = MIC_BUFFER_SIZE // 2
      for i in range(0, MIC_BUFFER_SIZE, 2):
         sample = int.from_bytes(mic_samples[i:i+2], 'little')
         # Signed 16-bit
         if sample >= 32768:
            sample -= 65536
         sum_squares += sample * float(sample)
      rms = math.sqrt(sum_squares / num_samples)
   return rms

def main():
   if sys.implementation._machine.startswith("TinyPICO"):
      try:
         import tinypico
         print("loaded: tinypico.py")
         tinypico.set_dotstar_power(False)
      except:
         print("missing: tinypico.py")
         pass

   report_string = None
   count_state = restore_from_rtc_memory()
   if count_state is None:
      count_state = {"wake_count": 0,
                     "thold_count": 0,
                     "rms_0_count": 0,
                     "rms_history": []
                     }
      write_rtc_memory(count_state)

   config = read_config()
   if config is None:
      print("No config; calling deep sleep")
      my_deep_sleep(15)

   # print debug info on first wake:
   if count_state["wake_count"] == 0:
      print(f"{config=}")
      mem_status()

   count_state['wake_count'] +=1

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
      I2S_PORT_ID = 1
      audio_in = I2S(I2S_PORT_ID, mode=I2S.RX, \
         sck=config['i2s_pins']['sck'], sd=config['i2s_pins']['sd'], ws=config['i2s_pins']['wstrobe'], \
         bits=16, format=I2S.MONO, rate=8000, ibuf=MIC_BUFFER_SIZE)
      select_pin = Pin(config['i2s_pins']['select'], Pin.OUT)
      select_pin.value(0)
      rms = get_rms(audio_in)
      print(f'RMS: {rms:.2f}')
      if rms > 0:
         increment_thold_count = False
         if config['sampling']['below_above'] == 1:
            if rms > config['sampling']['threshold']:
               increment_thold_count = True
         elif rms < config['sampling']['threshold']:
            increment_thold_count = True

         if increment_thold_count:
            count_state['thold_count'] +=1
            count_state['rms_history'].append(int(rms))
         elif count_state['thold_count'] > 0:
            count_state['thold_count'] -=1   
      else:
         count_state['rms_0_count'] +=1
         if count_state['rms_0_count'] > 3:
            report_string = f"Error: RMS was zero for 3 samples."
            count_state['rms_0_count'] = 0
            print(report_string)
   else:
      print("Quitting: Missing 'i2s_pins' in config json file")
      sys.exit(0)

   if count_state['thold_count'] > config['sampling']['thold_count_limit']:
      print(f"thold_count={count_state['thold_count']} > thold_limit={config['sampling']['thold_count_limit']}")
      report_string = f"Noise RMS history = {count_state['rms_history']}; threshold={config['sampling']['threshold']}"
      count_state['thold_count'] = 0
      count_state['rms_history'] = []
      count_state['rms_0_count'] = 0

   write_rtc_memory(count_state)

   if report_string:
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

      mem_status() #free up memory (the audio buffer) for urequest

      if "twilio" in config:
         url = config['twilio']['api'].replace('_sid_',config['twilio']['sid'])
         response = requests.post(
            url, 
            data=f"To={config['twilio']['to']}&From={config['twilio']['from']}&Body={report_string}",
            auth=(config['twilio']['sid'], config['twilio']['token']),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
         )
         print(f"sms response: code={response.status_code}; text={response.text}")
         response.close()
      else:
         print("no twilio config when trying to report")

      if "ftp" in config:
         host = config['ftp']['host']
         ftp = setup_ftp(host, config['ftp']['user'], config['ftp']['password'])
         if ftp is None:
            print(f"FTP setup to {host} failed")
         else:
            battery_voltage = get_bat_volt_int()
            send_battery_voltage(host,battery_voltage)
            ftp.quit()
      else:
         print("no ftp config")

   my_deep_sleep(deep_sleep_seconds)
