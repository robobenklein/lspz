
import sys
from pathlib import Path
import math
import warnings
import argparse
import concurrent
import traceback
from concurrent.futures import TimeoutError

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
from pebble import ProcessPool, ProcessExpired

# from .tf_data import subset_tracks_with_genres, TrackOnDisk
from .fma_data import FMAData
from .chroma import generate_chromas_from_file


class Skeet(Exception):
    pass

def write_chromas_for_file(trackfile: Path, chroma_dir: Path, skip_if_exists=True):
    chromas = []
    sub_dir = chroma_dir / f"{trackfile.name[:3]}"
    sub_dir.mkdir(parents=True, exist_ok=True)
    # first_img_file = sub_dir / f"{trackfile.name}.chroma.0.png"
    npz_outfile = sub_dir / f"{trackfile.name}.chroma.npz"
    if skip_if_exists and npz_outfile.exists():
        return int(trackfile.stem), None
    try:
        chromas = list(generate_chromas_from_file(trackfile))
    except audioread.exceptions.NoBackendError as e:
        print(f"failed loading track {trackfile}, will not be included in output data")
        print(traceback.format_exc())
        raise e
    # for idx, chroma in enumerate(generate_chromas_from_file(trackfile)):
    #     written_chromas.append(npz_outfile)
        # img_outfile = sub_dir / f"{trackfile.name}.chroma.{idx}.png"
        # imageio.imwrite(img_outfile, chroma)
        # npz_outfile = sub_dir / f"{trackfile.name}.chroma.{idx}.npz"
        # np.save(npy_outfile, chroma, allow_pickle=False)
    if not len(chromas):
        raise Skeet(f"file had no chromas, boi: {trackfile}")
    np.savez_compressed(npz_outfile, *chromas)

    return int(trackfile.stem), len(chromas)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'subset',
        type=str,
        help="Which subset of the FMA data to process",
        default="small",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing chroma images if they already exist",
    )
    parser.add_argument(
        "-d", "--data-dir",
        type=Path,
        help="Path to the FMA data dir",
        default=Path("data"),
    )

    args = parser.parse_args()

    data = FMAData(args.data_dir)
    chroma_dir = args.data_dir / f"lspz_chromas_{args.subset}"

    # for idx, trackfile in enumerate(data.files_in(args.subset)):
    #     trackid, chromafiles = write_chromas_for_file(trackfile, chroma_dir, skip_if_exists=not args.overwrite)
    #     print(f"wrote chromas for {trackid}: {len(chromafiles)} chromas")

    with ProcessPool() as pool:
        futures = []
        for idx, trackfile in enumerate(data.files_in(args.subset)):
            futures.append(
                pool.schedule(
                    write_chromas_for_file,
                    args=(trackfile, chroma_dir),
                    kwargs={"skip_if_exists": not args.overwrite},
                )
            )

        for idx, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                res = future.result()
                trackid, chromacount = res
                print(f"wrote chromas for {trackid}: {chromacount} chromas")
            except audioread.exceptions.NoBackendError as e:
                continue
            except Skeet as e:
                print(f"Skeet bro: (file probably has too much silence) {e}")
                continue
            except Exception as e:
                pool.stop()
                pool.join()
                raise e
