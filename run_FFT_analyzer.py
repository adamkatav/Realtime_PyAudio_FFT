import argparse
from src.stream_analyzer import Stream_Analyzer
import time
import numpy as np
from collections import deque

def detect_beat_in_interval(fftx: np.ndarray, fft: np.ndarray) -> bool:
    raise NotImplementedError()

def calc_energy(fftx: np.ndarray, fft: np.ndarray, bass_max_hz:int=400) -> float:
    bass_freqs = fftx<bass_max_hz
    return sum(fft[bass_freqs])/sum(bass_freqs)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default=None, dest='device',
                        help='pyaudio (portaudio) device index')
    parser.add_argument('--height', type=int, default=450, dest='height',
                        help='height, in pixels, of the visualizer window')
    parser.add_argument('--n_frequency_bins', type=int, default=400, dest='frequency_bins',
                        help='The FFT features are grouped in bins')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--window_ratio', default='24/9', dest='window_ratio',
                        help='float ratio of the visualizer window. e.g. 24/9')
    parser.add_argument('--sleep_between_frames', dest='sleep_between_frames', action='store_true',
                        help='when true process sleeps between frames to reduce CPU usage (recommended for low update rates)')
    parser.add_argument('--visualize', type=int, default=1, dest='visualize',
                        help='Visualize fft 1 or 0')
    return parser.parse_args()

def convert_window_ratio(window_ratio):
    if '/' in window_ratio:
        dividend, divisor = window_ratio.split('/')
        try:
            float_ratio = float(dividend) / float(divisor)
        except:
            raise ValueError('window_ratio should be in the format: float/float')
        return float_ratio
    raise ValueError('window_ratio should be in the format: float/float')

def run_FFT_analyzer():
    args = parse_args()
    window_ratio = convert_window_ratio(args.window_ratio)

    ear = Stream_Analyzer(
                    device = args.device,        # Pyaudio (portaudio) device index, defaults to first mic input
                    rate   = None,               # Audio samplerate, None uses the default source settings
                    FFT_window_size_ms  = 60,    # Window size used for the FFT transform
                    updates_per_second  = 1000,  # How often to read the audio stream for new data
                    smoothing_length_ms = 50,    # Apply some temporal smoothing to reduce noisy features
                    n_frequency_bins = args.frequency_bins, # The FFT features are grouped in bins
                    visualize = args.visualize,               # Visualize the FFT features with PyGame
                    verbose   = args.verbose,    # Print running statistics (latency, fps, ...)
                    height    = args.height,     # Height, in pixels, of the visualizer window,
                    window_ratio = window_ratio  # Float ratio of the visualizer window. e.g. 24/9
                    )

    fps = 60  #How often to update the FFT features + display
    last_update = time.time()
    NUMBER_OF_FRAMES = 20 # One second (?) for best detection try maybe 6
    BEAT_COEFF = 1.5
    history = deque([], maxlen=NUMBER_OF_FRAMES)
    while True:
        if (time.time() - last_update) > (1./fps):
            last_update = time.time()
            raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()
            energy = calc_energy(fftx=binned_fftx, fft=binned_fft, bass_max_hz=300)
            history.appendleft(energy)
            if len(history) == NUMBER_OF_FRAMES:
                hist_as_array = np.array(history)
                mean_energy = hist_as_array.mean()
                is_beat = energy > BEAT_COEFF*mean_energy
                if is_beat:
                    # print(f'Beat detected!\t{energy=}\t{mean_energy=}')
                    print("BEAT")
                else:
                    print("NO")
        elif args.sleep_between_frames:
            time.sleep(((1./fps)-(time.time()-last_update)) * 0.99)
        

if __name__ == '__main__':
    run_FFT_analyzer()
