
import functools
import random
from pathlib import Path
from collections import namedtuple

import tensorflow as tf

from .chroma import generate_chromas_from_file
from .fma_data import data as fmadata

random_number = 4
chroma_dimensions = (1025, 1025, 1)
TrackOnDisk = namedtuple("TrackOnDisk", ["id", "path"])


def subset_tracks_with_genres(subset = "small"):
    """Generator: (track_id, path) pairs

    Only if track has genres specified and exists on the filesystem
    """
    for trackfile in fmadata.files_in(subset):
        trackid = int(trackfile.stem)
        if trackid in fmadata.track_genres_labels.index:
            yield TrackOnDisk(trackid, trackfile)

def gen_chromas_with_labels(subset = "small"):
    """Generator: (input, labels) for tf.data.Dataset

    input: the chroma for the chunk
    labels: the numpy MultiHot array for genres of the track the chunk is from
    """
    target_tracks = list(subset_tracks_with_genres(subset))
    random.Random(random_number).shuffle(target_tracks)
    for trackid, trackfile in target_tracks:
        labels = fmadata.get_genres_for_track(trackid)
        for chroma in generate_chromas_from_file(trackfile):
            yield (chroma, labels)

dataset = tf.data.Dataset.from_generator(
    gen_chromas_with_labels,
    output_types=(tf.float32, tf.float32),
)

def is_test(x, y):
    return x % 4 == 0

def is_train(x, y):
    return not is_test(x, y)

def second(x, y):
    return y

test_dataset = dataset.enumerate() \
    .filter(is_test) \
    .map(second)

train_dataset = dataset.enumerate() \
    .filter(is_train) \
    .map(second)
