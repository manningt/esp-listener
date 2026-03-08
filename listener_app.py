import math

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
   tinypico.set_dotstar_power(False)
   rtc = machine.RTC()
   I2S_PORT_ID = 1
   MIC_BUFFER_SIZE = (8000 * 2 * 3) + OFFSET

   config = read_config()
   if config is None:
      print("No config; calling deep sleep")
      my_deep_sleep(15)

   if 'sleep' not in config:
      config['sleep'] = 30

   if 'i2s' in config:
      audio_in = machine.I2S(I2S_PORT_ID, mode=I2S.RX, sck=config['i2s']['sck'], sd=config['i2s']['sd'], \
         ws=config['i2s']['wstrobe'], bits=16, format=I2S.MONO, rate=8000, ibuf=MIC_BUFFER_SIZE)
      mic_samples = bytearray(MIC_BUFFER_SIZE)
      select_pin = machine.Pin(config['i2s']['select'], Pin.OUT)
      select_pin.value(0)    
      num_read = audio_in.readinto(mic_samples)
      if num_read != MIC_BUFFER_SIZE:
         print(f"Error: samples read={num_read}; expected={MIC_BUFFER_SIZE}")
      else:
         rms = calculate_rms(mic_samples, 0)
         print(f'RMS: {rms:.2f}')
   else:
      print("No i2s config")

   if "wifi" in config:
      station = setup_station(config[wifi]['ssid'], config['wifi']['password'])
      if station is None:
         print("WiFi not connecting")
         # my_deep_sleep(config['sleep'])
   else:
      print("No wifi config")

   if "ftp" in config:
      host = config['ftp']['host']
      ftp = setup_ftp(host, config['ftp']['user'], config['ftp']['password'])
      if ftp is None:
         print(f"FTP setup to {host} failed")
         # my_deep_sleep(config['sleep'])
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

   my_deep_sleep(config['sleep'])
