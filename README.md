# A simple NOAA APT decoder
https://www.youtube.com/watch?v=Tu6vo0PwN74

## Goal
- to create a simple FM demod tool
- capture raw data at 2MHz and store in a file OR read from a IQ.wav file
- demod FM and store audio in a .wav file
- use the demod FM to decode the NOAA APT image

## Preliminary results
### FM demodulation of NOAA to get audio
Raw IQ was used to FM demodulate it and get audio then image was constructed. Following is the result, which is fairly good result.

![Alt text](readmeImgs/nice.png?raw=true "Decoded")

input file cortesy (Andreas Hornig (https://github.com/aerospaceresearch)): https://drive.google.com/open?id=18E-h3DWMbzC5W6pS5mHzA-4Yt02WxxzX

We can observe that the generated image is a subset of ideal one, there is only an offset and less size. So we can confirm this proof of concept of NOAA APT decoding. We need to improve the FM demodulation to get better looking image.

## Further steps:
- modularize code
- optimize operations to make code faster (chunk processing, memory mapping etc.)

Video (old): https://www.youtube.com/watch?v=RuZPJMp2Nt0
Video (of just FM demod example): https://www.youtube.com/watch?v=RuZPJMp2Nt0