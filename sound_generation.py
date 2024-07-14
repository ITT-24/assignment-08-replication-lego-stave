import numpy as np
import pyaudio
from scipy.signal import sawtooth, square
from enum import Enum
import seaborn as sns
import matplotlib.pyplot as plt
from pynput import keyboard
import os
import collections
import time
import threading

class Instrument(Enum):
    SINE = 0
    PULSE = 1
    SAW = 2
    NOISE = 3

class Note():
    # length: duration of the tone (in seconds)
    # frequency: frequency (i.e. pitch) of the tone (in Hz)
    # instrument: the waveform of the tone (sine, pulse, sawtooth, or noise)
    # pulse: pulsewidth of the signal (only applies to pulse waves.)
    # sawwidth: width of the rising portion of the triangular wave form in proportion of one cycle. 0.0 produces a sawtooth wave, 0.5 produces a symmetrical triangle wave, 1.0 a sawtooth wave (but flipped). Only for sawtooth waves.
    
    def __init__(self, length:float, frequency:float, instrument:Instrument, volume:float,  pulse=0.5, sawwidth=0.5):
        self.length = length
        self.frequency = frequency
        self.instrument = instrument
        self.volume = volume
        self.pulse = pulse
        self.sawwidth = sawwidth


SAMPLING_RATE = 11400
CHUNK_SIZE = 4096
NUM_TRACKS = 10 # number of sounds that can be played in parallel
py_audio = pyaudio.PyAudio()

class SoundGenerator():

    def __init__(self,sampling_rate):

        self.sampling_rate = sampling_rate

        self.noise_rng = np.random.default_rng()
        self.stream: pyaudio.Stream|None = None
        
        self.tracks = np.ndarray((NUM_TRACKS, 1), dtype=np.float32)
        self.feed_stream_thread = threading.Thread(target=self.feed_stream)
        self.now = 0

    def start_stream(self):        
        self.stream = py_audio.open(rate=SAMPLING_RATE,format=pyaudio.paFloat32, channels=1, output=True, stream_callback=self.feed_stream)
        self.active = True
        #self.feed_stream_thread.start()

    def end_stream(self):
        self.active = False
        self.stream.stop_stream()
        self.stream.close()
        py_audio.terminate()

    """
    continuously reads samples from the multiple tracks, merges them, and writes them to the stream.
    """
    def feed_stream(self, in_data, frame_count, time_info, status):
        if self.tracks.shape[1] < self.now + frame_count:
            self.tracks = np.pad(self.tracks, [(0,0),(0,frame_count)])
        chunk = np.mean(self.tracks[:, self.now : self.now + frame_count], axis=0).tobytes()
        self.now += frame_count
        return chunk, pyaudio.paContinue


    # with the given parameters, creates a 32-bit float signal in byte form.
    def generate_tone(self, note):
        print(f"freq{note.frequency}")
        if not note.instrument in Instrument:
            print(f"No, Patrick, {note.instrument} is not an instrument!")
            return
        waveform = np.array([])
        t = np.arange(note.length * SAMPLING_RATE)
        if note.instrument == Instrument.SINE:
            waveform = np.sin(np.pi * 2 * (note.frequency/self.sampling_rate) * t)
            #NUM_QUANTISATION_STEPS = 512
            #quantisation_steps = np.linspace(-volume, volume, NUM_QUANTISATION_STEPS)
            #quant_inds = np.digitize(waveform, quantisation_steps)
            #waveform = quantisation_steps[quant_inds]

        elif note.instrument == Instrument.SAW:
            waveform = sawtooth(np.pi * 2 * (note.frequency/SAMPLING_RATE) * t, width=note.sawwidth)
        elif note.instrument == Instrument.PULSE:
            waveform = square(np.pi * 2 * (note.frequency/SAMPLING_RATE) * t, duty=note.pulse)
        elif note.instrument == Instrument.NOISE:
            waveform = np.random.normal(note.frequency, note.volume, note.length*SAMPLING_RATE)
            waveform = waveform / waveform.max()
        #waveform = waveform * volume

        return waveform.astype(np.float32)
    
    def play_simultaneous_notes(self,notes:(list|np.ndarray)):
        if len(notes) <= 0:
            return
        waves = []
        length_samples = []
        for note in notes:
            wave = self.generate_tone(note)
            waves.append(wave)
            length_samples.append(wave.shape[0])
        print(length_samples)
        sample_length = max(length_samples)
        print(sample_length)
        print(self.tracks.shape)
        now = self.now # save before padding to prevent race conditions
        self.tracks = np.pad(self.tracks, [(0,0),(0,sample_length)])
        print(self.tracks.shape)
        print(now)
        #waves = np.apply_along_axis(lambda arr:arr.resize(sample_length), 0, np.array(waves)) # extends length of all arrays to match length of the longest note
        #combined_wave = np.sum(waves, axis=0)
        #combined_wave = combined_wave / np.max(combined_wave)
        print("len waves",len(waves))
        for wave in waves:
            print("waveloop")
            for i in range(NUM_TRACKS):
                print("found one!")
                if self.tracks[i][now] == 0:
                    print(self.tracks[i].shape)
                    self.tracks[i][now:now + wave.shape[0]] = wave
                    break


            
            

            


