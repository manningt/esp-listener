# Overview

This set of micropython modules:
* runs on a ESP device
* uses a i2s microphone to get noise levels
* wakes up from deep_sleep to get an audio sample, calculates the RMS and compares it to a threshold
* counts the number of times the sample is above or below the threshold
* if above/below the threshold for N times, it will send a message using a TBD method

# listener_simple:
Minimal code to take an audio sample and save it to flash in a binary format.  It is meant to be run manually using [rshell](https://github.com/dhylands/rshell/blob/master/README.rst):
```
% rshell
> cp listener_simple.py /pyboard
> repl
>>> import listener_simple
 after the code runs hit CTRL-X to get from repl back to rshell
> cp /pyboard/output.bin .
```
The script runs after typing import.  After it runs, the binary format output file can be copied back the host computer.  In the utils directory, the script *bin_to_wav.py* can be run to convert the output file format and then *calc_rms_wav.py* can be run.

# 