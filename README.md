# Overview

This set of micropython modules:
* runs on a ESP device
* uses an [i2s microphone](https://invensense.tdk.com/wp-content/uploads/2015/02/INMP441.pdf) to get noise levels
* wakes up from deep_sleep to get an audio sample, calculates the RMS and compares it to a threshold
* counts the number of times the sample is above or below the threshold
* if above/below the threshold for N times:
    * it will send a message using a TBD method (twilio SMS if wifi is available)
    * the message is currently: Noise RMS history = [640, 614, 587, 534]; threshold=500
    * resets the number of threshold crossings and RMS history
    * sets the next deep_sleep duration equal to the configured 'report_hours'
* goes back to deep_sleep for the configured time: either sample_minutes or report_hours

# set up and run code on an ESP
Connect to your ESP using [rshell](https://github.com/dhylands/rshell/blob/master/README.rst) and a USB cable.  Before the code is run, a config file should be written, the contents of the file are described in the next section.

At the rshell prompt:
```
cp main.py /pyboard
cp your-config.json /pyboard/config.json
cp support.py /pyboard
cp listener_app.py /pyboard
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
    * "report_hours": once the threshold limit count is exceeded, sampling will _not_ continue for this duration.

# twilio
[twilio](twilio.com/en-us/blog/developers/tutorials/integrations/sms-doorbell-micropython-twilio) provides a large set of services; one of them is an API to send a text message.  The link to twilio provided the example code somewhat followed by the code in listener_app. 

# ftp
An FTP server, running on linux computer, maintains a log file which contains client login attempts.  A program can run on the FTP server to watch the log and perform some action based on the client's attempt.  For example a user ID that contains data on an upweller crossing used to trigger sending a message.  The FTP code in listener_app.py was used in a different project and could be used for this purpose.

# background information
Old ESP development boards will most likely not have enough RAM to run micropython with a 3 second audio buffer plus do the http request.  For example, ```>>> gc.mem_free()``` yielded 164784 bytes.  I used an 6 year old version of [TinyPICO](tinypico.com) which had 4182848 bytes free.  The TinyPICO has the feature of being LiPO battery operated (charger, regulator and connector) as well as an ADC pin to read the battery voltage.  A TinyPICO version of micropython is available which includes a module [tinypico.py](github.com/tinypico/tinypico-micropython/tree/master/tinypico-helper) containing defines and functions to read the battery and turn off the LED.  On the [micropython download](micropython.org/download/) page, search for tinypico (there are other tiny ESP32 products).

I2S reference materials:
* [class I2S](docs.micropython.org/en/latest/library/machine.I2S.html)
* [I2S example](github.com/miketeachman/micropython-i2s-examples/blob/master/examples/record_mic_to_sdcard_uasyncio.py)


# listener_simple:
Minimal code to take an audio sample and save it to flash in a binary format.  It is meant to be run manually using [rshell](github.com/dhylands/rshell/blob/master/README.rst):
```
% rshell
> cp listener_simple.py /pyboard
> repl
>>> import listener_simple
 after the code runs hit CTRL-X to get from repl back to rshell
> cp /pyboard/output.bin .
```
The script runs after typing import.  After it runs, the binary format output file can be copied back the host computer.  In the utils directory, the script *bin_to_wav.py* can be run to convert the output file format and then *calc_rms_wav.py* can be run.
