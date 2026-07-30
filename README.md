# Overview

This set of micropython modules:
* runs on a ESP device
* uses an [i2s microphone](https://invensense.tdk.com/wp-content/uploads/2015/02/INMP441.pdf) to get noise levels
* wakes up from deep_sleep to get an audio sample, calculates the RMS and compares it to a threshold
* counts the number of times the sample is above or below the threshold
* if above/below the threshold for N times:
    * it will send a message using a TBD method:
        * the twilio.com service can be used to send an SMS if internet via Wifi is available
            * this has been tested
        * Using FTP (kind of kludgy, but it works)
            * the ESP client does an FTP login with the userID being the message content
            * a process on the FTP server watches for login attempts and extras the information
            * this method was used on another project, but hasn't been tested here
    * the message is currently: Noise RMS history = [640, 614, 587, 534]; threshold=500
    * resets the number of threshold crossings and RMS history
    * sets the next deep_sleep duration equal to the configured 'restart_sampling_hours'
* goes back to deep_sleep for the configured time: either sample_minutes or restart_sampling_hours

# set up and run code on an ESP
Connect to your ESP using [rshell](https://github.com/dhylands/rshell/blob/master/README.rst) and a USB cable.  Before the code is run, a config file should be written, the contents of the file are described in the next section.

At the rshell prompt:
```
cp main.py /pyboard
cp your-config.json /pyboard/config.json
cp support.py /pyboard
cp listener_app.py /pyboard
cp mp_tinys3d.py /pyboard (or whatever device routines you may add)
repl
>>> CTRL-D to reset the ESP, which will then run boot, then main.py, which imports and runs listener_app
```

# configuration file
The listener_app reads a config file; refer to the example-config.json file included in this repository.  The wifi, twilio and ftp parameters are self-explanatory.  The other parameters are:
* [i2s](https://en.wikipedia.org/wiki/I2S):
    * the pins for sck, ws and sd need to be configured
    * the select pin can either be tied to ground or a pin to drive it low needs to be configured
* sampling:
    * all the settings are numbers.  No validation is performed by the code (ranges or strings)
    * "below_above": if 1 the threshold has to be exceeded, otherwise the RMS has to below the threshold to be counted as a threshold crossing.
    * "threshold": an RMS value to use for a threshold. An integer from 0 to any large value.
    * "thold_count_limit": the number of samples the RMS has to be above/below the threshold before sending a message.
    * "sample_minutes": determines the interval between samples.  Can be floating point in order to specify seconds, but would normally be set to 5 or 10 minutes.  For faster detection times, set to a lower number. 
    * "restart_sampling_hours": once the threshold limit count is exceeded, sampling will _not_ continue for this duration.

# twilio
[twilio](twilio.com/en-us/blog/developers/tutorials/integrations/sms-doorbell-micropython-twilio) provides a large set of services; one of them is an API to send a text message.  The link to twilio provided the example code somewhat followed by the code in listener_app. 

# ftp
An FTP server, running on linux computer, maintains a log file which contains client login attempts.  A program can run on the FTP server to watch the log and perform some action based on the client's attempt.  For example a user ID that contains data on an upweller crossing used to trigger sending a message.  The FTP code in listener_app.py was used in a different project and could be used for this purpose.  **You'll need to install micropython [ftplib.py](https://github.com/SpotlightKid/micropython-ftplib) onto the ESP board to use FTP.**

# notes on the python code and the ESP
* main.py just calls listener_app.main.  That way if an exception happens in the listener_app, then it goes to the repl prompt after printing out the exception.  Also, renaming main.py to something else is a way of not entering the continous deep_sleep loop when debugging.
* the ESP and 8K of RAM (rtc_memory) that is preserved when in deep_sleep.  It is used to store state information from one wake session to the next.  If what is read from the memory is not JSON, a default state is stored in rtc_memory.

# features to possibly add:
* reporting low battery levels
* storing a wav file for the samples that are above/below the threshold.  The issue is how to send them.  twilio does offer MMS in addition to SMS.

# background information
Old ESP development boards will most likely not have enough RAM to run micropython with a 3 second audio buffer plus do the http request.  For example, ```>>> gc.mem_free()``` yielded 164784 bytes.  I used an 6 year old version of [TinyPICO](tinypico.com) which had 4182848 bytes free.  The TinyPICO has the feature of being LiPO battery operated (charger, regulator and connector) as well as an ADC pin to read the battery voltage.  A TinyPICO version of micropython is available which includes a module [tinypico.py](github.com/tinypico/tinypico-micropython/tree/master/tinypico-helper) containing defines and functions to read the battery and turn off the LED.  On the [micropython download](micropython.org/download/) page, search for tinypico (there are other tiny ESP32 products).
## Update (2026-July): migrated from TinyPico to [TinyS3d](https://esp32s3.com/tinys3d.html) in order to have an external antenna.  This also changed how to read the battery voltage from using the ADC to using a [I2C based fuel guage](https://www.analog.com/en/products/max17048.html).

I2S reference materials:
* [class I2S](docs.micropython.org/en/latest/library/machine.I2S.html)
* [class I2S for ESP32s3](https://docs.espressif.com/projects/esp-idf/en/v4.4/esp32s3/api-reference/peripherals/i2s.html)
* [I2S example](github.com/miketeachman/micropython-i2s-examples/blob/master/examples/record_mic_to_sdcard_uasyncio.py)


# listener_simple:
Minimal code to take an audio sample and save it to flash in a binary format.  It is meant to be run manually using [rshell](github.com/dhylands/rshell/blob/master/README.rst):
```
% cd <path>/esp-listener
% rshell
> cp listener_simple.py /pyboard
> repl
>>> import listener_simple
>>> listener_simple.sample()
 after the code runs hit CTRL-X to get from repl back to rshell
> cp /pyboard/output.bin samples/lastest_output.bin
```
The script runs after typing import.  After it runs, the binary format output file can be copied back the host computer.  In the utils directory, the script *bin_to_wav.py* can be run to convert the output file format and then *calc_rms_wav.py* can be run.
