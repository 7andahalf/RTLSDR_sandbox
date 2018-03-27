'''
### Simple Python - RTLSDR script to capture raw data as well as demod FM
# Author: Vinay C K (github.com/7andahalf)
A small demo video: https://youtu.be/cCH-fBXAYAc

# prerequisits and Credits for libraries
- Install python wrapper for RTLSDR from https://github.com/roger-/pyrtlsdr
- math from: http://ultra.sdk.free.fr/docs/DxO/FM%20DEMODULATION%20USING%20A%20DIGITAL%20RADIO%20AND%20DIGITAL%20SIGNAL%20PROCESSING%20Digradio.pdf
- am from: https://github.com/zacstewart/apt-decoder
# How to use:
To demod FM + NOAA image from existing IQ.wav file:
	- record raw IQ from other softwares (@ 2.048MSPS if not edit below var) or use a prev IQ.wav generated by this tool
	- run 'python app.py IQ.wav', replace IQ.wav with input 
	- after demod the script will exit and show image and save it

	Output:
	- demodulated FM: a .wav file that has a name like 'IQ_FM.wav'
		format <input_file_name>_FM.wav
	- decoded image '<input_file_name>_FM.wav.png'

Thanks!
'''

from pylab import *
import numpy as np  
import scipy.signal as signal
from scipy.signal import butter, lfilter
import sys
from scipy.io.wavfile import read, write
import datetime
import PIL

# configure device
recordFor = 10 # time in seconds
freqOffset = 30000
FMFreq = 137619408 # @ freq of FM station?
SDRSampleRate = 2.048e6 # 2MHz sampling rate
FMBandwidth = 60000 # BW of FM

# obtain IQ data either by capture or from file
samples = None # to store IQ samples
audFileName = None
if not (len(sys.argv) == 2):
	print("Usage: python_NOAA.py <IQ.wav>")
	exit()

# read samples from file
print("Will read samples from file", sys.argv[1])
numSamp, data = read(sys.argv[1], mmap=True) # any faster methods?
if not len(data[0,:]) == 2:
	print("The input file doesn't have 2 channels!")
	exit()
print("File read complete")
print("Converting to complex IQ form")
#samples = data[:,0] + 1j * data[:,1] # any faster methods?
#samples *= 1.0 / np.max(np.abs(samples))
print("Conversion complete")
audFileName = sys.argv[1].split(".")[0] + "_FM.wav"

## FM Demoduation
# demodulate chunk by chunk
chunk_size = 20000000
fin_aud = []
for i in range(1+int(len(data[:,0])/chunk_size)):
	samples = data[i*chunk_size:(i+1)*chunk_size,0] + 1j * data[i*chunk_size:(i+1)*chunk_size,1] # any faster methods?
	print("processing chunk", i+1,"/",1+int(len(data[:,0])/chunk_size))
	# convert to baseband: mult by e^(-j*2pi*freq_diff*time)
	sig_baseBand = np.array(samples).astype("complex64")
	sig_baseBand *= np.exp(-1.0j*2.0*np.pi* freqOffset*np.arange(len(sig_baseBand))/SDRSampleRate)
	print("A", end = '', flush=True)

	# gaussian filter
	window = signal.blackmanharris(151)
	sig_baseBand = signal.convolve(sig_baseBand, window, mode='same')
	print("B", end = '', flush=True)

	# IF filter
	# add if necessary

	print("C", end = '', flush=True)

	# limit bandwidth of FM by downsampling
	targetFs = FMBandwidth  
	jumpIndex = int(SDRSampleRate / targetFs)  
	sig_baseBand_bwlim = sig_baseBand[0::jumpIndex]  # skip samples to downsample
	Fs_bwlim = SDRSampleRate/jumpIndex # Calculate the new sampling rate
	print("D", end = '', flush=True)

	# FM demod by polar discrimination
	sig_fmd = sig_baseBand_bwlim[1:] * np.conj(sig_baseBand_bwlim[:-1])  
	sig_fm = np.angle(sig_fmd)
	print("E", end = '', flush=True)

	# Filter audio
	# add later if needed
	print("F", end = '', flush=True)

	# downsample to audio sampling rate of 44k  
	Fs_audlim = 20800
	sig_aud = signal.resample(sig_fm, int(20800 * len(sig_fm)/Fs_bwlim))
	print("G", end = '', flush=True)

	# resize so that max amp = 1
	#sig_aud *= 1.0 / np.max(np.abs(sig_aud))  
	print("H")

	fin_aud.extend(sig_aud)

sig_aud = np.array(fin_aud)
print("Done FM demod")

# save .wav of audio
write(audFileName, Fs_audlim, sig_aud)

## decode image. source of am code mentioned above.
# limit size to multiple of 20800
sig_aud = sig_aud[:20800*int(len(sig_aud) // 20800)]

# get envelope by hilbert
hilb_aud = signal.hilbert(sig_aud)
filtered = signal.medfilt(np.abs(hilb_aud), 5)
reshaped = filtered.reshape(len(filtered) // 5, 5)

# get high low values to quantise
(low, high) = np.percentile(reshaped[:, 2], (0.5, 99.5))
delta = high - low

# quantize pixels
data = np.round(255 * (reshaped[:, 2] - low) / delta)
data[data < 0] = 0
data[data > 255] = 255
digitized = data.astype(np.uint8)

# Look for sync signal
pattern = [255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255]
lengthPattern = len(pattern)

firstMatch = None
for i in range(len(digitized) - lengthPattern):
	if sum(abs(digitized[i:i+lengthPattern] - pattern)) < 1000:
		firstMatch = i
		break

if firstMatch == None:
	print("No image in the data!")
	exit()

# adjust sync
digitized = digitized[firstMatch:]
digitized = digitized[:2080*int(len(digitized) // 2080)]
matrix = digitized.reshape((int(len(digitized) / 2080), 2080))

#create image and store
image = PIL.Image.fromarray(matrix)
image.save(audFileName+".png")
image.show()

''' EXPERIMENTAL
minVar = None
minInd = None
syncLocs = []
for i in range(len(digitized) - lengthPattern):
	if abs((i-firstMatch)-2080*int((i-firstMatch)/2080)) < 2:
		if minVar == None or (sum(abs(digitized[i:i+lengthPattern] - pattern)) < minVar):
			minVar = sum(abs(digitized[i:i+lengthPattern] - pattern))
			minInd = i
	else:
		minVar = None
		if not minInd == None:
			syncLocs.append(minInd)
			minInd = None

matrix = []
for i in syncLocs:
	if (i+2080)<len(digitized):
		matrix.append(digitized[i:i+2080])

image = PIL.Image.fromarray(np.array(matrix))
image.save(audFileName+".png")
image.show()
'''