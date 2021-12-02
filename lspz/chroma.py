
import sys
from pathlib import Path
import math

import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
import librosa
import librosa.display
import numpy as np

from .utils import chunk_iter

default_sr = 22050
window_fft_length = 2048
window_count = 256

chunk_sample_count = (window_fft_length * window_count)
chunk_time_seconds = chunk_sample_count / 22050


def generate_chroma_from_chunk(chunk, sample_rate=default_sr):
    """Generates a spectrogram from audio data

    chunk: 1-d array of samples
    sample_rate: samples/sec
    """
    # frequencies, times, spectrogram = signal.spectrogram(chunk, sample_rate)

    stft = librosa.stft(chunk, n_fft=window_fft_length, dtype=np.float32)
    S_db = librosa.amplitude_to_db(np.abs(stft), ref=np.max)

    return S_db

if __name__ == '__main__':
    infile = Path(sys.argv[1])

    # sample_rate, samples = wavfile.read(infile)
    samples, sample_rate = librosa.load(infile, sr=default_sr)

    print(f"chunk_time_seconds: {chunk_time_seconds}")
    print(f"file samples: {samples.shape}")
    print(f"sample_rate: {sample_rate}")

    nchunks = samples.shape[0] / chunk_sample_count

    print(f"number of chunks in input file: {nchunks}")

    fig, ax = plt.subplots(math.floor(nchunks))

    for chunkidx, chunk in enumerate(chunk_iter(samples, chunk_sample_count)):
        if len(chunk) != chunk_sample_count:
            # ignore incomplete last chunk
            continue
        spectrogram = generate_chroma_from_chunk(chunk, sample_rate)

        print(f"spectrogram shape: {spectrogram.shape}")

        img = librosa.display.specshow(spectrogram, ax=ax[chunkidx])
        fig.colorbar(img, ax=ax[chunkidx])

        # plt.figure()
        # librosa.display.specshow(S_db)
        # plt.colorbar()

    plt.show()

    # plt.pcolormesh(times, frequencies, np.log(spectrogram))
    # # plt.imshow(spectrogram)
    # plt.ylabel('Frequency [Hz]')
    # plt.xlabel('Time [sec]')
