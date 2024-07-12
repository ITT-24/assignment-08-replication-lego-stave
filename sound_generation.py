import numpy as np
import pyaudio
from scipy.signal import sawtooth, square
from enum import Enum
import seaborn as sns
import matplotlib.pyplot as plt
from pynput import keyboard
import os

class Instrument(Enum):
    SINE = 0
    PULSE = 1
    SAW = 2
    NOISE = 3

SAMPLING_RATE = 11400
py_audio = pyaudio.PyAudio()

noise_rng = np.random.default_rng()
stream: pyaudio.Stream|None = None

# with the given parameters, creates a 32-bit float signal in byte form.
# length: duration of the tone (in seconds)
# frequency: frequency (i.e. pitch) of the tone (in Hz)
# instrument: the waveform of the tone (sine, pulse, sawtooth, or noise)
# pulse: pulsewidth of the signal (only applies to pulse waves.)
# sawwidth: width of the rising portion of the triangular wave form in proportion of one cycle. 0.0 produces a sawtooth wave, 0.5 produces a symmetrical triangle wave, 1.0 a sawtooth wave (but flipped). Only for sawtooth waves.
def generate_tone(length:float, frequency:float, instrument:Instrument, volume:float,  pulse=0.5, sawwidth=0.5):
    if not instrument in Instrument:
        print(f"No, Patrick, {instrument} is not an instrument!")
        return
    waveform = np.array([])
    t = np.arange(length * SAMPLING_RATE)
    if instrument == Instrument.SINE:
        waveform = np.sin(np.pi * 2 * (frequency/SAMPLING_RATE) * t)
        #NUM_QUANTISATION_STEPS = 512
        #quantisation_steps = np.linspace(-volume, volume, NUM_QUANTISATION_STEPS)
        #quant_inds = np.digitize(waveform, quantisation_steps)
        #waveform = quantisation_steps[quant_inds]

    elif instrument == Instrument.SAW:
        waveform = sawtooth(np.pi * 2 * (frequency/SAMPLING_RATE) * t, width=sawwidth)
    elif instrument == Instrument.PULSE:
        waveform = square(np.pi * 2 * (frequency/SAMPLING_RATE) * t, duty=pulse)
    elif instrument == Instrument.NOISE:
        waveform = noise_rng.normal(0, 0.5,size=int(length*SAMPLING_RATE))
        waveform = waveform / waveform.max()
    #waveform = waveform * volume
    print(waveform)

    return waveform.astype(np.float32).tobytes()

def on_press(key):
    if key == keyboard.KeyCode.from_char('a'):
        length = 0.5
        frequency = 220
        tone = generate_tone(length, frequency, Instrument.SINE, 10)
        stream.write(tone)
    elif key == keyboard.KeyCode.from_char('s'):
        length = 0.5
        frequency = 220
        tone = generate_tone(length, frequency, Instrument.SAW, 10, sawwidth=0.0)
        stream.write(tone)
    elif key == keyboard.KeyCode.from_char('d'):
        length = 0.5
        frequency = 220
        tone = generate_tone(length, frequency, Instrument.PULSE, 8, pulse=0.5)
        stream.write(tone)
    elif key == keyboard.KeyCode.from_char('f'):
        length = 0.1
        frequency = 220
        tone = generate_tone(length, frequency, Instrument.NOISE, 10)
        stream.write(tone)
    elif key == keyboard.KeyCode.from_char('q'):
        stream.stop_stream()
        stream.close()
        py_audio.terminate()
        os._exit(0)
        


if __name__ == "__main__":
    stream = py_audio.open(rate=SAMPLING_RATE,format=pyaudio.paFloat32, channels=1, output=True)
    with keyboard.Listener(
        on_press=on_press) as listener:
        listener.join()

