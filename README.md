# AGS10 sensor
Micropython library for the AGS10 TVOC sensor

## I2C

### Pin layout

|  Pin  |   Name  | Description  |
|:-----:|:--------|:-------------|
|   1   |   SCL   | Serial clock |
|   2   |   SDA   | Serial data  |
|   3   |   GND   | Ground       |
|   4   |   VCC   | Power supply |

> ## Warning!
>
> - The sensor uses I2C at low speed. It should be LESS than 15kHz. 
>
> - The datasheet advices against frequent measurements. Specially whne TVOC measurements cannot be performed frequently. Doing so will deteriorate the sensor quickly.
>
> - There should be at least 1.5s delay between two successive measurements

## Example
```py
from ags10 import AGS10
from machine import I2C
from time import sleep_ms

# Init
sensor = AGS10(I2C(0, freq=10000))

# Enable to perform CRC check for measurements
sensor.check_crc = True

# Measure TVOC in parts per billion
tvoc = sensor.total_volatile_organic_compounds_ppb

# wait before the next command to the sensor
sleep_ms(2000)

# Measure resistance in kohms
resistance = sensor.resistance_kohm

# Re-calibrate zero point.
# Set the resistance in kohms in virtual memory.
# Needs at least 15 min exposure in fresh air before calibration.
sensor.zero_point_calibrate(resistance)
sleep_ms(30)

# Reset zero point to factory defaults
sensor.zero_point_factory_reset()
sleep_ms(30)

# Update I2C address
sensor.update_address(126)
```

## Support

You can always improve the quality of the libraries by providing issues and Pull Requests.
