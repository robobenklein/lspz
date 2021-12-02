
from pathlib import Path
from collections import namedtuple
from random import shuffle

import tensorflow as tf

from .fma_data import data as fmadata

chroma_dimensions = (1025, 1025, 1)
TrackOnDisk = namedtuple("TrackOnDisk", ["id", "path"])


def track_label_array(track_id: int):
    """Return the numpy label_array for a given FMA track ID"""
    pass

def chromas_with_labels(infile: Path, random_order=False):
    """Generate (chroma, label_array) pairs for a file from the FMA dataset

    chroma: generated from generate_chromas_from_file
    label_array: track genres from the FMA metadata (same for every pair returned)
    """
    pass

def subset_tracks_with_genres(subset = "small"):
    """Generator: (track_id, path) pairs

    Only if track has genres specified and exists on the filesystem
    """
    for trackfile in fmadata.files_in(subset):
        trackid = int(trackfile.stem)
        if trackid in fmadata.track_genres_labels.index:
            yield TrackOnDisk(trackid, trackfile)
