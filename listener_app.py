from support import write_rtc_memory, restore_from_rtc_memory, \
   read_config, my_deep_sleep, setup_station, mem_status, \
   get_bat_volt_int, ftp_bogus_login_msg
from machine import Pin, I2S # pyrefly: ignore [missing-import]
import math
import sys
import requests
from time import sleep

SAMPLE_SECONDS = 3
MIC_BUFFER_SIZE = (8000 * 2 * SAMPLE_SECONDS)

def get_rms(audio_in):
   mic_samples = bytearray(MIC_BUFFER_SIZE)
   num_read = audio_in.readinto(mic_samples)
   if num_read != MIC_BUFFER_SIZE:
      print(f"Error: samples read={num_read}; expected={MIC_BUFFER_SIZE}")
      rms = 0
   else:
      sum_squares = 0.0
      num_samples = len(mic_samples) // 2
      for i in range(0, len(mic_samples), 2):
         sample = int.from_bytes(mic_samples[i:i+2], 'little')
         # Signed 16-bit
         if sample >= 32768:
            sample -= 65536
         sum_squares += sample * float(sample)
      # print(f"{sum_squares=} {num_samples=}")
      rms = math.sqrt(sum_squares / num_samples)
   return rms

def main():
   if sys.implementation._machine.startswith("TinyPICO"):
      try:
         import tinypico # pyrefly: ignore [missing-import]
         # print("loaded: tinypico.py")
         tinypico.set_dotstar_power(False)
      except:
         print("missing: tinypico.py")
         pass

   if sys.implementation._machine.startswith("TinyS3"):
      try:
         from mp_tinys3d import set_antenna_external, set_pixel_power, init_fuel_guage  # pyrefly: ignore [missing-import]
         # print("loaded: mp_tinys3d.py")
         set_antenna_external()
         set_pixel_power(0)
         init_fuel_guage()
      except:
         print("missing: mp_tinys3d.py")
         pass

   report_string = None
   count_state = restore_from_rtc_memory()
   if count_state is None:
      count_state = {"wake_count": 0,
                     "thold_count": 0,
                     "rms_0_count": 0,
                     "rms_history": [],
                     "report_re_attempts": 0,
                     "wifi_history": [],
                     "periodic_report_minutes": 0,
                     "reported_low_battery": 0
                     }

   report_string = None # clear to prevent 2nd message on powerup
   count_state['wake_count'] +=1

   config = read_config()
   if config is None:
      print("No config; quitting")
      sys.exit(0)

   if 'periodic_reporting' not in config:
      print("Quitting: Missing 'periodic_reporting' in config json file")
      sys.exit(0)

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

   if count_state['report_re_attempts'] > 0:
      # last attempt to report didn't work; dont sample, and retry to send (will retry forever)
      print(f"Report reattempt # {count_state['report_re_attempts']}")
      # set report string as it would be by a threshold crossing
      report_string = f"RMS_history={count_state['rms_history']};threshold={config['sampling']['threshold']}"
      deep_sleep_seconds = 300 #retry in 5 minutes
   else:
      if 'i2s_pins' not in config:
         print("Quitting: Missing 'i2s_pins' in config json file")
         sys.exit(0)
      else:
         I2S_PORT_ID = 1
         # the pin direction is not specified; the I2S function probably does a Pin.reinit()
         audio_in = I2S(I2S_PORT_ID, mode=I2S.RX, format=I2S.MONO, bits=16, rate=8000, 
            ibuf=MIC_BUFFER_SIZE,
            sck=Pin(config['i2s_pins']['sck']),
            ws=Pin(config['i2s_pins']['wstrobe']),
            sd=Pin(config['i2s_pins']['sd']) \
            )
         # the Left/Right select pin must be low; maybe because of mono format
         select_pin = Pin(config['i2s_pins']['select'], Pin.OUT)
         select_pin.value(0)
         
         sleep(1)
         rms = get_rms(audio_in)
         print(f'RMS: {rms:.2f}')
         # throw out first sample
         if count_state['wake_count'] > 1:
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

      if count_state['thold_count'] > config['sampling']['thold_count_limit']:
         report_string = f"RMS_history={count_state['rms_history']};threshold={config['sampling']['threshold']}"
         print(report_string)
         tmp = config['sampling']['restart_sampling_hours']
         if isinstance(tmp, float) or isinstance(tmp, int):
            deep_sleep_seconds = int(tmp*3600)
         else:
            print(f"Warning: invalid restart_sampling_hours={tmp}; using 4 hours")
            deep_sleep_seconds = 14400

   # print debug info on first wake:
   if count_state["wake_count"] == 1:
      print(f"{config=}")
      mem_status()
      report_string = f"initialized: threshold={config['sampling']['threshold']};below_above={config['sampling']['below_above']}"

   if report_string is None:
      # check for sending periodic report (I'm alive message)
      battery_voltage = get_bat_volt_int()
      print(f'DEBUG: comparing {count_state['periodic_report_minutes']=} > {(config['periodic_reporting']['interval_days'] * 24*60)}')
      status_string = f"batt={battery_voltage}V; wake_count={count_state['wake_count']}; sample_interval={config['sampling']['sample_minutes']} minutes"
      if count_state['periodic_report_minutes'] > (config['periodic_reporting']['interval_days'] * 24*60):
         report_string = "Still checking noise levels: " + status_string
         
      if battery_voltage < config['periodic_reporting']['battery_voltage_threshold'] and count_state['reported_low_battery'] == 0:
         report_string = "Low battery warning: " + status_string
         count_state['reported_low_battery'] = 1

   if report_string:
      print(f'>>> reporting: {report_string}')
      if "wifi" in config:
         station, attempts = setup_station(config['wifi']['ssid'], config['wifi']['password'])
         if station is None:
            print("WiFi not connecting")
            count_state['report_re_attempts'] += 1
         if len(count_state['wifi_history']) > 2:
            count_state['wifi_history'].pop()
         count_state['wifi_history'].insert(0,attempts)
      else:
         station = None
         print("No wifi config")

      mem_status() #free up memory (the audio buffer) for urequest

      if station:
         rssi = station.status('rssi')
         battery_voltage = get_bat_volt_int()
         report_string = f"{report_string};report_reattempts={count_state['report_re_attempts']};connect_retries={count_state['wifi_history']};rssi={rssi};batt={battery_voltage}V"
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
            ftp_bogus_login_msg(config['ftp']['host'], report_string)
         else:
            print("no ftp config")

         #clear statistics after reporting
         count_state['thold_count'] = 0
         count_state['rms_history'] = []
         count_state['rms_0_count'] = 0
         count_state['report_re_attempts'] = 0
         count_state['periodic_report_minutes'] = 0
   else:
      deep_sleep_minutes = round(deep_sleep_seconds/60)
      if deep_sleep_minutes == 0:
         deep_sleep_minutes = 1 
      count_state['periodic_report_minutes'] += deep_sleep_minutes

   write_rtc_memory(count_state)
   audio_in.deinit()
   my_deep_sleep(deep_sleep_seconds)
