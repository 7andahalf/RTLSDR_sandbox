'''
### Simple Python - RTLSDR script to capture raw data as well as demod FM
# Author: Vinay C K (github.com/7andahalf)

# prerequisits and Credits for libraries
- Install python wrapper for RTLSDR from https://github.com/roger-/pyrtlsdr

Thanks!
'''

from pylab import *
from rtlsdr import *

sdr = RtlSdr(serial_number='00000001') # Change serial_number to select different device, it was 1 for me

# configure device
sdr.sample_rate = 2e6 # 2MHz sampling rate
sdr.center_freq = 102.9e6 # @ what freq?
sdr.gain = 4 # for now

# app settings
recordFor = 1 # time in seconds

# read samples
numSamples = (int(sdr.sample_rate * recordFor) / 1024) * 1024 # div and mult bcz can only read a multiple of 1024 samples. why?
print "Will collect", numSamples, "samples over the duration of", recordFor, "seconds"
samples = sdr.read_samples(numSamples)
print "Collection complete"
print samples[0]

# use matplotlib to estimate and plot the PSD
psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
xlabel('Frequency (MHz)')
ylabel('Relative power (dB)')

show()