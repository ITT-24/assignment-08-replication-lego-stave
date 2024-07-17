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
    BASS = 33
    HAMMOND = 16
    XYLO = 13
    VIOLIN = 40
    SQUARE = 80
    SAW = 81
    GOBLIN = 101
    BASS_DRUM = 939 
    SNARE = 938 
    SAX = 64
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
            if instrument in [Instrument.PIANO, Instrument.DRUM, Instrument.DULCIMER, Instrument.STRINGS, Instrument.SAX, Instrument.BASS, Instrument.HAMMOND, Instrument.SNARE, Instrument.SAW,Instrument.XYLO, Instrument.VIOLIN, Instrument.GOBLIN]:
                # Hammond and Sax doesn't turn a note off, when its two notes at the same time
                self.out_port.send(mido.Message('note_off', note=note_height, velocity=volume))
                inst = mido.Message('program_change', program=instrument.value)
                self.out_port.send(inst)
                msg = mido.Message('note_on', note=note_height, velocity=volume, time=length)
                self.out_port.send(msg)

                t = threading.Timer(length+ i *0.0001, lambda note_height=note_height: self.end_note(note_height, volume, instrument.value))
                t.start()

            elif instrument in [Instrument.BASS_DRUM, Instrument.SNARE]:
                inst = mido.Message('program_change', program=instrument.value-900)
                self.out_port.send(inst)
                msg = mido.Message('note_on', note=note_height, time=length, channel=9)
                self.out_port.send(msg)
                
    
    def end_note (self, note_height, velocity, program=None, timer=None):
        if not program is None:
            inst = mido.Message('program_change', program=program)
            self.out_port.send(inst)
            
        msg = mido.Message('note_off', note=note_height, velocity=0)
        self.out_port.send(msg)
        return



            
            

            


