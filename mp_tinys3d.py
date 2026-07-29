# TinyS3D Helper Library - micropython (vs circuitpython)

from machine import Pin, const # pyrefly: ignore [missing-import]
# APA102 Dotstar pins for production boards
DOTSTAR_CLK = const(12)
DOTSTAR_DATA = const(2)
DOTSTAR_PWR = const(13)

I2C_SDA = const(8)
I2C_SCL = const(9)

ANTENNA_SELECTION = const(38)

# Helper functions
def set_antenna_external():
    """Set the RF switch to the external uFL connector."""
    Pin(ANTENNA_SELECTION, Pin.OUT, value=1)  # Break the PULL_HOLD on the pin

# def set_pixel_power(state):
#     """Enable or Disable power to the onboard NeoPixel to either show colour, or to reduce power fro deep sleep."""
#     global pixel_power
#     pixel_power.value = state
    
def get_battery_voltage():
    return 3.3
