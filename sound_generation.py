import numpy as np
import threading
import mido
from enum import Enum
# import pyaudio
# from scipy.signal import sawtooth, square
# import seaborn as sns
# import matplotlib.pyplot as plt
# from pynput import keyboard
# import os
# import collectionspy
# import time

class Instrument(Enum):
    PIANO = 0
    DRUM = 116
    DULCIMER = 15
    STRINGS =  45 
    BASS_DRUM = 939 
    SNARE = 938 
# see for example here: https://www.ccarh.org/courses/253/handout/gminstruments/

class Note():
    # length: duration of the tone (in seconds)
    # frequency: frequency (i.e. pitch) of the tone (in Hz)
    # instrument: the waveform of the tone (sine, pulse, sawtooth, or noise)
    # pulse: pulsewidth of the signal (only applies to pulse waves.)
    # sawwidth: width of the rising portion of the triangular wave form in proportion of one cycle. 0.0 produces a sawtooth wave, 0.5 produces a symmetrical triangle wave, 1.0 a sawtooth wave (but flipped). Only for sawtooth waves.
    
    def __init__(self, length:float, note:int, instrument:Instrument, volume:int):
        self.length = length
        self.note = note
        self.instrument = instrument
        self.volume = volume

SAMPLING_RATE = 11400
CHUNK_SIZE = 512
NUM_TRACKS = 10 # number of sounds that can be played in parallel
# py_audio = pyaudio.PyAudio()

class SoundGenerator():

    def __init__(self,sampling_rate):
        self.out_port = mido.open_output()

    def play_simultaneous_notes(self,notes:(list|np.ndarray)):
        if len(notes) <= 0:
            return
        
        for i, note in enumerate(notes):
            length = note.length
            note_height = note.note
            volume = note.volume
            instrument = note.instrument
            if instrument in [Instrument.PIANO, Instrument.DRUM, Instrument.DULCIMER, Instrument.STRINGS]:
                # Hammond and Sax doesn't turn a note off, when its two notes at the same time
                self.out_port.send(mido.Message('note_off', note=note_height, velocity=volume))
                inst = mido.Message('program_change', program=instrument.value)
                self.out_port.send(inst)
                print(length, i)
                msg = mido.Message('note_on', note=note_height, velocity=volume, time=length)
                self.out_port.send(msg)
                t = threading.Timer(length+ i *0.0001, lambda: self.end_note(note_height, volume))
                t.start()

            elif instrument in [Instrument.BASS_DRUM, Instrument.SNARE]:
                inst = mido.Message('program_change', program=instrument.value-900)
                self.out_port.send(inst)
                msg = mido.Message('note_on', note=note_height, time=length, channel=9)
                self.out_port.send(msg)
                
    
    def end_note (self, note_height, velocity):
        msg = mido.Message('note_off', note=note_height, velocity=0)
        self.out_port.send(msg)
        print(f"Message sent {msg}")
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
        self.tracks = np.pad(self.tracks, [(0,0),(0,3*sample_length)])
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


            
            

            


