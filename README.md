# Overview

This set of micropython modules:
* runs on a ESP device
* uses a i2s microphone to get noise levels
* wakes up from deep_sleep to get an audio sample, calculates the RMS and compares it to a threshold
* counts the number of times the sample is above or below the threshold
* if below the threshold for N times, 