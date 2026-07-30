# TinyS3D Helper Library - micropython (vs circuitpython)
'''
references:
https://github.com/UnexpectedMaker/esp32s3/blob/main/series_d/pinout_cards/tinys3d_pinout.jpg
https://github.com/UnexpectedMaker/esp32s3/blob/main/schematics/schematic-tinys3.pdf
https://github.com/UnexpectedMaker/esp32s3/blob/main/code/circuitpython/shipping%20files/tinys3/tinys3.py

https://github.com/adafruit/Adafruit_CircuitPython_MAX1704x/blob/main/adafruit_max1704x.py


'''
from machine import Pin, const, I2C # pyrefly: ignore [missing-import]

ANTENNA_SELECTION = const(38)
RGB_PWR = const(17)

MAX1704X_I2CADDR_DEFAULT = const(0x36)
MAX1704X_VCELL_REG = const(0x02)
MAX1704X_MODE_REG = const(0x06)
MAX1704X_VERSION_REG = const(0x08)
MAX1704X_HIBRT_REG = const(0x0A) #hibernate
MAX1704X_CONFIG_REG = const(0x0C)
MAX1704X_CONFIG_DEFAULT = const(0x971C)
MAX1704X_POR_REG = const(0xFE) #power on reset register
MAX1704X_POR_VALUE = bytearray([0x54,0x00])

i2c = None

# Helper functions
def set_antenna_external():
    #Set the RF switch to the external uFL connector.
    Pin(ANTENNA_SELECTION, Pin.OUT, value=1)  # Break the PULL_HOLD on the pin

def set_pixel_power(state):
    #reduce power for deep sleep.
    Pin(RGB_PWR, Pin.OUT, value=state)

def init_fuel_guage():
    global i2c
    try:
        i2c = I2C(0) #defaults to sda=io8, scl=io9
        max17048_version = i2c.readfrom_mem(MAX1704X_I2CADDR_DEFAULT, MAX1704X_VERSION_REG, 2)
        # print(f'{max17048_version[0]=} {max17048_version[1]=}')
        if int.from_bytes(max17048_version) & 0xFFF0 != 0x0010:
            print(f'MAX17048G incorrect version = {max17048_version}; expected 0x001_')
            return False

        # The following is commented because it intermittently returns 0xFF 0xFF - not sure why.
        #     checking hibernate mode should be good enough to verify the device
        # check config register is returns default value
        # max17048_config = i2c.readfrom_mem(MAX1704X_I2CADDR_DEFAULT, MAX1704X_CONFIG_REG, 2)
        # print(f'TEMPORARY: MAX17048G power-on config = {max17048_config}; expected 0x971C')
        # if int.from_bytes(max17048_config) != MAX1704X_CONFIG_DEFAULT:
        #     print(f'MAX17048G incorrect power-on config = {max17048_config}; expected 0x971C')
        #     return False

        #enable hibernate operation: battery sampled every 45 seconds
        i2c.writeto_mem(MAX1704X_I2CADDR_DEFAULT, MAX1704X_HIBRT_REG, bytearray([0xFF,0xFF,0xFF,0xFF,]))
        # max17048_hibernate = i2c.readfrom_mem(MAX1704X_I2CADDR_DEFAULT, MAX1704X_HIBRT_REG, 2)
        # print(f'Hibernate after write/read = {max17048_hibernate}')

        #check hiberate mode bit:
        max17048_mode = i2c.readfrom_mem(MAX1704X_I2CADDR_DEFAULT, MAX1704X_MODE_REG, 2)
        # print(f'read back of max17048_mode: {max17048_mode[0]=} {max17048_mode[1]=}')
        if max17048_mode[0] & 0x10 != 0x10:
            print(f'MAX17048G not in hibernate mode = {max17048_mode[0]}; expected bit 4 set')
            return False
        # print('max17048 OK')
    except Exception as e:
        print(f'i2c failed: exception: {e}')
 
def get_battery_voltage():
    global i2c
    try:
        max17048_vcell = i2c.readfrom_mem(MAX1704X_I2CADDR_DEFAULT, MAX1704X_VCELL_REG, 2)
        max17048_vcell_int = int.from_bytes(max17048_vcell)
        # print(f'max17048 OK; VCELL={max17048_vcell_int} times 78.125µV per cell')
        return (max17048_vcell_int * .000078125)
    except Exception as e:
        print(f'i2c failed: exception: {e}')
        return 0

def read_fuel_cell(register=MAX1704X_VCELL_REG, num_bytes=2):
    global i2c
    if not i2c:
        i2c = I2C(0)
    try:
        read_value = i2c.readfrom_mem(MAX1704X_I2CADDR_DEFAULT, register, num_bytes)
        read_value_int = int.from_bytes(read_value)
        print(f'register addr={register} returned {read_value}')
        return read_value_int
    except Exception as e:
        print(f'i2c failed: exception: {e}')
        return 0

def write_fuel_cell(register=MAX1704X_HIBRT_REG, value=bytearray([0xFF,0xFF,0xFF,0xFF,])):
    if not isinstance(value, bytearray):
        print(f'value={value} is not a bytearray')
        return
    global i2c
    if not i2c:
        i2c = I2C(0)
    try:
        i2c.writeto_mem(MAX1704X_I2CADDR_DEFAULT, register, value)
        print(f'wrote register addr={register} with {value}')
    except Exception as e:
        print(f'i2c failed: exception: {e}')
