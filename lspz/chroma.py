
import sys
from pathlib import Path
import math
import warnings

import matplotlib.pyplot as plt
import audioread
import librosa.display
import numpy as np
import scipy.misc
import imageio
import librosa
from librosa.core import audio as lr_audio
from scipy import signal
from scipy.io import wavfile

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

    if chunk.shape[0] != chunk_sample_count:
        raise RuntimeWarning(f"input chunk does not match target chunk size: {chunk.shape} vs expected {chunk_sample_count}")

    stft = librosa.stft(chunk, n_fft=window_fft_length)
    S_db = librosa.amplitude_to_db(np.abs(stft), ref=np.max)

    return S_db

def generate_chromas_from_file(infile: Path, exclude_partial=True):
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', 'PySoundFile failed. Trying audioread instead.')
        # samples, sample_rate = librosa.load(infile, sr=default_sr)
        y, sr_native = lr_audio.__audioread_load(
            str(infile), 0.0, None, np.float32)
        y = lr_audio.to_mono(y)
        y = lr_audio.resample(y, sr_native, default_sr)
        samples = y
        sample_rate = default_sr

    samples = np.trim_zeros(samples)

    nchunks = samples.shape[0] / chunk_sample_count

    for chunkidx, chunk in enumerate(chunk_iter(samples, chunk_sample_count)):
        if len(chunk) != chunk_sample_count:
            # ignore incomplete last chunk
            if exclude_partial:
                continue
        spectrogram = generate_chroma_from_chunk(chunk, sample_rate)
        yield spectrogram

if __name__ == '__main__':
    infile = Path(sys.argv[1])

    # # sample_rate, samples = wavfile.read(infile)
    # samples, sample_rate = librosa.load(infile, sr=default_sr)
    #
    # print(f"chunk_time_seconds: {chunk_time_seconds}")
    # print(f"file samples: {samples.shape}")
    # print(f"sample_rate: {sample_rate}")
    #
    # nchunks = samples.shape[0] / chunk_sample_count
    #
    # print(f"number of chunks in input file: {nchunks}")

    chroma_dir = Path("data/chroma_imgs")
    chroma_dir.mkdir(parents=True, exist_ok=True)

    chromas = list(generate_chromas_from_file(infile))
    fig, ax = plt.subplots(len(chromas))
    print(f"full chromas from file: {len(chromas)}")

    for idx, chroma in enumerate(chromas):
        imageio.imwrite(chroma_dir / f"{infile.name}.chroma.{idx}.png", chroma)
        img = librosa.display.specshow(chroma, ax=ax[idx])
        fig.colorbar(img, ax=ax[idx])

    plt.show()
