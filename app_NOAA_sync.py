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
import scipy
from scipy.signal import butter, lfilter
import sys
from scipy.io.wavfile import read, write
import datetime
import PIL
import math
# configure device
recordFor = 10 # time in seconds
freqOffset = -30000
FMFreq = 137619408 # @ freq of FM station?
SDRSampleRate = 2.048e6 # 2MHz sampling rate
FMBandwidth = 60000 # BW of FM

# obtain IQ data either by capture or from file
samples = None # to store IQ samples
audFileName = "ress"
if not (len(sys.argv) == 2):
	print("Usage: python_NOAA.py <IQ.wav>")
	exit()

# read samples from file
print("Will read samples from file", sys.argv[1])


#numSamp, data = read(sys.argv[1], mmap=True) # any faster methods?
data = np.memmap(sys.argv[1], offset=44)

#if not len(data[0,:]) == 2:
#	print("The input file doesn't have 2 channels!")
#	exit()
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
i = 0
#samples = data[i*chunk_size:(i+1)*chunk_size,0] + 1j * data[i*chunk_size:(i+1)*chunk_size,1]

#for i in range(1+int(0*len(data[:,0])/chunk_size)):
for i in range(1+int(len(data)/(2*chunk_size))):
	#samples = data[i*chunk_size:(i+1)*chunk_size,0] + 1j * data[i*chunk_size:(i+1)*chunk_size,1] # any faster methods?
	samples = (data[2*i*chunk_size:2*(i+1)*chunk_size:2]) + 1j * (data[1+2*i*chunk_size:1+2*(i+1)*chunk_size:2])
	#print(samples[1:10])
	#print("processing chunk", i+1,"/",1+int(len(data[:,0])/chunk_size))
	print("processing chunk", i+1,"/",1+int(len(data)/(2*chunk_size)))
	#print(sum(samples)/len(samples))

	# convert to baseband: mult by e^(-j*2pi*freq_diff*time)
	sig_baseBand = np.array(samples).astype("complex64") - (129 + 1j*129)
	sig_baseBand *= np.exp(-1.0j*2.0*np.pi* freqOffset*np.arange(len(sig_baseBand))/SDRSampleRate)
	print("A", end = '', flush=True)

	#psd(sig_baseBand, NFFT=1024, Fs=SDRSampleRate)
	#xlabel('Frequency (MHz)')
	#ylabel('Relative power (dB)')
	#show()

	# gaussian filter
	window = signal.blackmanharris(151)
	sig_baseBand = signal.convolve(sig_baseBand, window, mode='same')
	print("B", end = '', flush=True)

	# IF filter
	#lpf = signal.remez(64, [0, FMBandwidth, FMBandwidth+(SDRSampleRate/2-FMBandwidth)/4, SDRSampleRate/2], [1,0], Hz=SDRSampleRate)  
	#sig_baseBand = signal.lfilter(lpf, 1.0, sig_baseBand)

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
	#b, a = butter(1, [1800 / (0.5 * Fs_bwlim), 3000 / (0.5 * Fs_bwlim)], btype='band')
	#sig_fm = lfilter(b, a, sig_fm)
	print("F", end = '', flush=True)

	# downsample to audio sampling rate of 44k  
	Fs_audlim = 20800
	sig_aud = signal.resample(sig_fm, int(20800 * len(sig_fm)/Fs_bwlim))
	print("G", end = '', flush=True)

	# resize so that max amp = 1
	#sig_aud *= 1.0 / np.max(np.abs(sig_aud))  
	print("H")

	fin_aud.extend(sig_aud)
	del(samples)
sig_aud = np.array(fin_aud)
print("Done FM demod")

# save .wav of audio
write(audFileName, Fs_audlim, sig_aud)


#Fs_audlim, sig_aud = read(sys.argv[1])
## decode image. source of am code mentioned above.
# limit size to multiple of 20800
sig_aud = sig_aud[:20800*int(len(sig_aud) // 20800)]
hilb_aud = signal.hilbert(sig_aud)
filtered = signal.medfilt(np.abs(hilb_aud), 5)
reshaped = filtered.reshape(len(filtered) // 5, 5)
# get high low values to quantise
(low, high) = np.percentile(reshaped[:, 2], (0.5, 99.5))
delta = high - low

# quantize pixels
dataI = np.round(255 * (reshaped[:, 2] - low) / delta)
dataI[dataI < 0] = 0
dataI[dataI > 255] = 255
digitized = dataI.astype(np.uint8)

# Look for sync signal
pattern2 = [255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255]

pattern2 = scipy.ndimage.filters.gaussian_filter(pattern2, 0.5)
lengthPattern2 = len(pattern2)
filDig = scipy.ndimage.filters.gaussian_filter(digitized, 0.5)


linesize = 2080
expectedError = 100
matrix = []
# Sync Video A & time A
pattern = [255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255 ,0 ,0 ,255 ,255]
pattern = scipy.ndimage.filters.gaussian_filter(pattern, 0.5)
SyncVideoA = []
SyncTimeA = []
currentIndex = 0
for i in range(int(len(digitized)/linesize) - 2):
	minVar = None
	minI = 0
	rangeSearch = (currentIndex - expectedError, currentIndex + expectedError)
	if currentIndex == 0: rangeSearch = (0, linesize + len(pattern) - 1)

	for j in range(rangeSearch[0], rangeSearch[1]):
		diff = sum(abs(filDig[j:j+len(pattern)] - pattern))
		if minVar == None or  diff < minVar:
			minI = j
			minVar = diff
	if(filDig[minI+len(pattern)+len(pattern)-1] > 127 and filDig[minI+len(pattern)+len(pattern)] > 127 and filDig[minI+len(pattern)+len(pattern)+1] > 127):
		tPos = minI+len(pattern)+len(pattern)
		while(digitized[tPos] > 127 or digitized[tPos-1] > 127): tPos -= 1
		SyncTimeA.append(tPos)
	SyncVideoA.append(minI)
	currentIndex = minI + linesize
	matrix.append(digitized[minI:minI+linesize])


# Sync Video B & time B
pattern = [255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255 ,0 ,0 ,255 ,255 ,255]
pattern = scipy.ndimage.filters.gaussian_filter(pattern, 0.5)
SyncVideoB = []
SyncTimeB = []
currentIndex = 0
for i in range(int(len(digitized)/linesize) - 2):
	minVar = None
	minI = 0
	rangeSearch = (currentIndex - expectedError, currentIndex + expectedError)
	if currentIndex == 0: rangeSearch = (0, linesize + len(pattern) - 1)

	for j in range(rangeSearch[0], rangeSearch[1]):
		diff = sum(abs(filDig[j:j+len(pattern)] - pattern))
		if minVar == None or  diff < minVar:
			minI = j
			minVar = diff
	if(filDig[minI+len(pattern)+len(pattern)-1] < 127 and filDig[minI+len(pattern)+len(pattern)] < 127 and filDig[minI+len(pattern)+len(pattern)+1] < 127):
		tPos = minI+len(pattern)+len(pattern)
		while(digitized[tPos] < 127 or digitized[tPos-1] < 127): tPos -= 1
		SyncTimeB.append(tPos)
	SyncVideoB.append(minI)
	currentIndex = minI + linesize

# sample num to time
#print(SyncVideoA)
#print(SyncTimeA)

# border issues
'''
delThresh = 20
maxLen = int(len(data)/2)
if len(SyncVideoA) > 0 and SyncVideoA[0] < delThresh: SyncVideoA.pop(0)
if len(SyncVideoA) > 0 and maxLen - SyncVideoA[-1] < delThresh: SyncVideoA.pop(-1)
if len(SyncVideoB) > 0 and SyncVideoB[0] < delThresh: SyncVideoB.pop(0)
if len(SyncVideoB) > 0 and maxLen - SyncVideoB[-1] < delThresh: SyncVideoB.pop(-1)
if len(SyncTimeA) > 0 and SyncTimeA[0] < delThresh: SyncTimeA.pop(0)
if len(SyncTimeA) > 0 and maxLen - SyncTimeA[-1] < delThresh: SyncTimeA.pop(-1)
if len(SyncTimeB) > 0 and SyncTimeB[0] < delThresh: SyncTimeB.pop(0)
if len(SyncTimeB) > 0 and maxLen - SyncTimeB[-1] < delThresh: SyncTimeB.pop(-1)'''



pixPerSec = 2*2080
tSyncVideoA = [(i*1.0)/pixPerSec for i in SyncVideoA]
tSyncVideoB = [(i*1.0)/pixPerSec for i in SyncVideoB]
tSyncTimeA = [(i*1.0)/pixPerSec for i in SyncTimeA]
tSyncTimeB = [(i*1.0)/pixPerSec for i in SyncTimeB]

# time to sample
SyncVideoA = [math.floor(i*SDRSampleRate) for i in tSyncVideoA]
SyncVideoB = [math.floor(i*SDRSampleRate) for i in tSyncVideoB]
SyncTimeA = [math.floor(i*SDRSampleRate) for i in tSyncTimeA]
SyncTimeB = [math.floor(i*SDRSampleRate) for i in tSyncTimeB]

#print(SyncVideoA)
#print(SyncVideoB)
#print([x - y for x, y in zip(SyncVideoA, SyncVideoB)])
#print(SyncTimeA)
#print(SyncTimeB)

# identify in the high sampling
numPixelsAft = 10
numPixelsBef = 2
pixPerSec = 2*2080
fSyncVideoA = []
for i in SyncVideoA:
	numSamplesHigh = math.ceil(((numPixelsAft*1.0)/pixPerSec)*SDRSampleRate)
	numSamplesLow = math.ceil(((numPixelsBef*1.0)/pixPerSec)*SDRSampleRate)
	searchRange = (2*(i - numSamplesLow), 2*(i + numSamplesHigh))
	samples = (data[searchRange[0]:searchRange[1]:2]) + 1j * (data[searchRange[0]+1:searchRange[1]+1:2])
	sig_baseBand = np.array(samples).astype("complex64") - (129 + 1j*129)
	#print(startSamp,startSamp+numSamplesHigh,numSamplesHigh)
	sig_baseBand *= np.exp(-1.0j*2.0*np.pi* freqOffset*np.arange(len(sig_baseBand))/SDRSampleRate)
	window = signal.blackmanharris(151)
	sig_baseBand = signal.convolve(sig_baseBand, window, mode='same')
	sig_fmd = sig_baseBand[1:] * np.conj(sig_baseBand[:-1])
	sig_fm = np.angle(sig_fmd)
	hilb_aud = signal.hilbert(sig_fm)
	filtered = signal.medfilt(np.abs(hilb_aud), 5)
	xax = [-1.0*numPixelsBef + ((numPixelsBef+numPixelsAft)*i*1.0/len(filtered)) for i in range(len(filtered))]
	(minP, maxP) = np.percentile(filtered, (0.5, 80))
	j = numSamplesLow-math.ceil(((0.5*1.0)/pixPerSec)*SDRSampleRate)
	while filtered[j] < maxP: j+=1
	fSyncVideoA.append(i - numSamplesLow + j)
	#print(i, i - numSamplesLow + j)
	#plot(xax,filtered)
	#plot(xax[j], filtered[j], 'ro')
	#show()

fSyncVideoB = []
for i in SyncVideoB:
	numSamplesHigh = math.ceil(((numPixelsAft*1.0)/pixPerSec)*SDRSampleRate)
	numSamplesLow = math.ceil(((numPixelsBef*1.0)/pixPerSec)*SDRSampleRate)
	searchRange = (2*(i - numSamplesLow), 2*(i + numSamplesHigh))
	samples = (data[searchRange[0]:searchRange[1]:2]) + 1j * (data[searchRange[0]+1:searchRange[1]+1:2])
	sig_baseBand = np.array(samples).astype("complex64") - (129 + 1j*129)
	#print(startSamp,startSamp+numSamplesHigh,numSamplesHigh)
	sig_baseBand *= np.exp(-1.0j*2.0*np.pi* freqOffset*np.arange(len(sig_baseBand))/SDRSampleRate)
	window = signal.blackmanharris(151)
	sig_baseBand = signal.convolve(sig_baseBand, window, mode='same')
	sig_fmd = sig_baseBand[1:] * np.conj(sig_baseBand[:-1])
	sig_fm = np.angle(sig_fmd)
	hilb_aud = signal.hilbert(sig_fm)
	filtered = signal.medfilt(np.abs(hilb_aud), 5)
	xax = [-1.0*numPixelsBef + ((numPixelsBef+numPixelsAft)*i*1.0/len(filtered)) for i in range(len(filtered))]
	(minP, maxP) = np.percentile(filtered, (0.5, 80))
	j = numSamplesLow-math.ceil(((0.5*1.0)/pixPerSec)*SDRSampleRate)
	while filtered[j] < maxP: j+=1
	fSyncVideoB.append(i - numSamplesLow + j)
	#print(i, i - numSamplesLow + j)
	#plot(xax,filtered)
	#plot(xax[j], filtered[j], 'ro')
	#show()
'''
numPixelsAft = 100
numPixelsBef = 1
fSyncTimeA = []
for i in SyncTimeA:
	numSamplesHigh = math.ceil(((numPixelsAft*1.0)/pixPerSec)*SDRSampleRate)
	numSamplesLow = math.ceil(((numPixelsBef*1.0)/pixPerSec)*SDRSampleRate)
	searchRange = (2*(i - numSamplesLow), 2*(i + numSamplesHigh))
	#print(searchRange)
	samples = (data[searchRange[0]:searchRange[1]:2]) + 1j * (data[searchRange[0]+1:searchRange[1]+1:2])
	sig_baseBand = np.array(samples).astype("complex64") - (129 + 1j*129)
	#print(startSamp,startSamp+numSamplesHigh,numSamplesHigh)
	sig_baseBand *= np.exp(-1.0j*2.0*np.pi* freqOffset*np.arange(len(sig_baseBand))/SDRSampleRate)
	window = signal.blackmanharris(151)
	sig_baseBand = signal.convolve(sig_baseBand, window, mode='same')
	sig_fmd = sig_baseBand[1:] * np.conj(sig_baseBand[:-1])
	sig_fm = np.angle(sig_fmd)
	hilb_aud = signal.hilbert(sig_fm)
	filtered = signal.medfilt(np.abs(hilb_aud), 5)
	xax = [-1.0*numPixelsBef + ((numPixelsBef+numPixelsAft)*i*1.0/len(filtered)) for i in range(len(filtered))]
	(minP, maxP) = np.percentile(filtered, (0.5, 95))
	j = numSamplesLow + math.ceil(((65*1.0)/pixPerSec)*SDRSampleRate)
	while j < len(filtered) and filtered[j] < maxP: j+=1
	fSyncTimeA.append(i - numSamplesLow + j)
	print(i, i - numSamplesLow + j)
	plot(xax,filtered)
	plot(xax[j], filtered[j], 'ro')
	show()
'''
numPixelsAft = 100
numPixelsBef = 1
fSyncTimeB = []
for i in SyncTimeB:
	numSamplesHigh = math.ceil(((numPixelsAft*1.0)/pixPerSec)*SDRSampleRate)
	numSamplesLow = math.ceil(((numPixelsBef*1.0)/pixPerSec)*SDRSampleRate)
	searchRange = (2*(i - numSamplesLow), 2*(i + numSamplesHigh))
	#print(searchRange)
	samples = (data[searchRange[0]:searchRange[1]:2]) + 1j * (data[searchRange[0]+1:searchRange[1]+1:2])
	sig_baseBand = np.array(samples).astype("complex64") - (129 + 1j*129)
	#print(startSamp,startSamp+numSamplesHigh,numSamplesHigh)
	sig_baseBand *= np.exp(-1.0j*2.0*np.pi* freqOffset*np.arange(len(sig_baseBand))/SDRSampleRate)
	window = signal.blackmanharris(151)
	sig_baseBand = signal.convolve(sig_baseBand, window, mode='same')
	sig_fmd = sig_baseBand[1:] * np.conj(sig_baseBand[:-1])
	sig_fm = np.angle(sig_fmd)
	hilb_aud = signal.hilbert(sig_fm)
	filtered = signal.medfilt(np.abs(hilb_aud), 5)
	xax = [-1.0*numPixelsBef + ((numPixelsBef+numPixelsAft)*i*1.0/len(filtered)) for i in range(len(filtered))]
	(minP, maxP) = np.percentile(filtered, (0.5, 95))
	j = numSamplesLow + math.ceil(((75*1.0)/pixPerSec)*SDRSampleRate)
	while j >= 0 and filtered[j] < maxP: j-=1
	fSyncTimeB.append(i - numSamplesLow + j)
	#print(i, i - numSamplesLow + j)
	#plot(xax,filtered)
	#plot(xax[j], filtered[j], 'ro')
	#show()

print("Format: <sample Num from method1> <sample Num from method2> <time from method1> <time from method2>")

print("SYNCA")
for i in range(len(SyncVideoA)):print(SyncVideoA[i], fSyncVideoA[i], (SyncVideoA[i]*1.0)/SDRSampleRate, (fSyncVideoA[i]*1.0)/SDRSampleRate)
print("SYNCB")
for i in range(len(SyncVideoB)):print(SyncVideoB[i], fSyncVideoB[i], (SyncVideoB[i]*1.0)/SDRSampleRate, (fSyncVideoB[i]*1.0)/SDRSampleRate)
#print("TIMEA")
#for i in range(len(SyncTimeA)):print(SyncTimeA[i], fSyncTimeA[i], (SyncTimeA[i]*1.0)/SDRSampleRate, (fSyncTimeA[i]*1.0)/SDRSampleRate)
print("TIMEB")
for i in range(len(SyncTimeB)):print(SyncTimeB[i], fSyncTimeB[i], (SyncTimeB[i]*1.0)/SDRSampleRate, (fSyncTimeB[i]*1.0)/SDRSampleRate)


image = PIL.Image.fromarray(np.array(matrix))
image.save(audFileName+".png")
image.show()