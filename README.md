# A simple NOAA APT decoder
A small demo video: https://youtu.be/cCH-fBXAYAc

## Goal
- to create a simple FM demod tool
- capture raw data at 2MHz and store in a file OR read from a IQ.wav file
- demod FM and store audio in a .wav file
- use the demod FM to decode the NOAA APT image

## Preliminary results
### FM demodulation of NOAA to get audio
Audio was extracted from the raw IQ files by the script. The audio is fairly a good estimate but has noise. This needs to be worked on. However we can see that the waveform closely relates to a standard NOAAAPT line. The frequency domain also shows that the sound is 2.4kHz as expected.

![Alt text](readmeImgs/audio_comp.jpg?raw=true "Current decoded pulse vs. ideal pulse")

![Alt text](readmeImgs/fft_aud.jpg?raw=true "FFT of decoded audio")

### using demodulated audio to construct image
The audio was used to contruct image. Since there was noise, the image looks very bad. But we can make out atleast the sync signals and rough dark and light areas of image.

![Alt text](readmeImgs/gen.png?raw=true "A few lines of generated image")

![Alt text](readmeImgs/original.png?raw=true "Ideal image")

We can observe that the generated image is a subset of ideal one, there is only an offset and less size. So we can confirm this proof of concept of NOAA APT decoding. We need to improve the FM demodulation to get better looking image.

## Further steps:
- add filters to remove noise from FM, currently not many filters
- modularize code
- optimize operations to make code faster (chunk processing, memory mapping etc.)

Video (of just FM demod example): https://www.youtube.com/watch?v=RuZPJMp2Nt0