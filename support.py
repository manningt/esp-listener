import sys
import network, machine # pyrefly: ignore [missing-import]
import ujson as json # pyrefly: ignore [missing-import]
from time import sleep
import gc

def setup_station(ssid, password):
   sta_if = network.WLAN(network.STA_IF)
   sta_if.active(True)

   MAX_RETRIES = 11
   attempt = 1
   try:
      while attempt <= MAX_RETRIES:
         if sta_if.isconnected():
            break
         sta_if.connect(ssid, password)
         print(f"  {attempt}: ", end='')
         for _ in range(10):
            sleep(1)
            if sta_if.isconnected():
               break
            else:
               print(".  ", end='')
         attempt += 1
   except:
      return None, attempt

   if sta_if.isconnected():
      rssi = sta_if.status('rssi')
      print(f"  my IP={sta_if.ifconfig()[0]} after {attempt} attempts; rssi={rssi}")
   else:
      print("Failed to connect to WiFi")
      sta_if.active(False)
      sta_if = None
   return sta_if, attempt

def setup_ftp(host, user, password):
   try:
      from ftplib import FTP
   except:
      return None
   try:
      ftp = FTP(host)
   except Exception as e:
      print(f"FTP connection error: {e}")
      return None
   try:
      ftp.login(user,password)
   except Exception as e:
      print(f"FTP login error: {e}")
      return None
   ftp.set_pasv(False)
   return ftp

def my_deep_sleep(seconds):
   # check for an input character to jump out of deep_sleep loop
   # doesn't work because the UART is used by REPL
   '''
   uart = machine.UART(0, 115200)
   for _ in range(5):
      sleep(1)
      if uart.any():  # Non-blocking check
         data = uart.read()
         if data:
            sys.exit()
   '''
   print(f"deep sleep for {seconds} seconds")
   sleep(1)
   machine.deepsleep(seconds * 1000)

def read_config(filename="config.json"):
   config = None
   try:
      with open(filename, 'r') as f:
         config = json.load(f)
   except Exception as e:
      print(f"Error loading {filename}: {e}")
   return config

def write_rtc_memory(state_dict):
   machine.RTC().memory(bytearray(json.dumps(state_dict).encode()))

def restore_from_rtc_memory():
   tmp = None
   try:
      tmp = json.loads(machine.RTC().memory().decode())
      print(f"RTC.memory={tmp}")
      if type(tmp) is not dict:
            print(f"Warning (restore_state): RTC.memory={tmp} is not a dictionary")
            tmp = None
   except:
      print(f"Warning (restore_state): RTC.memory={tmp} was not JSON")
   return tmp

def get_bat_volt_int():
   bat_volt_int = 0
   if sys.implementation._machine.startswith("TinyPICO"):
      from tinypico import get_battery_voltage
      
      # old code to be deleted, if ever re-tested with TinyPICO
      # from machine import Pin  # pyrefly: ignore [missing-import]
      # from micropython import const # pyrefly: ignore [missing-import]
      # BAT_VOLTAGE_PIN = const(35) # refer to tinypico.py definitions
      # VOLTAGE_DIVIDER = 11 # 4096 max value divided by 370 reference voltage
      # adc = machine.ADC(machine.Pin(BAT_VOLTAGE_PIN))
      # raw_adc_value = adc.read()
      # bat_volt_int = int(raw_adc_value / VOLTAGE_DIVIDER)

   if sys.implementation._machine.startswith("TinyS3"):
      from mp_tinys3d import get_battery_voltage
      
   try:
      bat_volts = get_battery_voltage()
   except:
      print("get_battery_voltage failed")
      bat_volts = 0
   bat_volt_int = int(bat_volts  *100)
   return bat_volt_int

def mem_status():
   gc.collect()
   mem_stats = gc.mem_alloc()
   mem_free = gc.mem_free()
   print(f"Mem bytes Free={mem_free} + Alloc={mem_stats} >> Total={mem_stats + mem_free}")

def ftp_bogus_login_msg(host, message):
   # does a login attempt with a username equal to the message
   # which is recorded in /etc/log/vsftpd.log as a failed login attempt
   try:
      from ftplib import FTP
      ftp = FTP(host)
      ftp.login(message, "bogus_pw")
      ftp.quit()
   except Exception as e:
      print(f"ftp_bogus_login_msg: {e}")
