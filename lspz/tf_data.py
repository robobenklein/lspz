
import functools
import random
import sys
from pathlib import Path
from collections import namedtuple

import numpy as np
import tensorflow as tf

from .chroma import generate_chromas_from_file
from .fma_data import data as fmadata

random_number = 4
chroma_dimensions = (1025, 1025)
TrackOnDisk = namedtuple("TrackOnDisk", ["id", "path"])


def subset_tracks_with_genres(subset = "small"):
    """Generator: (track_id, path) pairs

    Only if track has genres specified and exists on the filesystem
    """
    for trackfile in fmadata.files_in(subset):
        trackid = int(trackfile.stem)
        if trackid in fmadata.track_genres_labels.index:
            yield TrackOnDisk(trackid, trackfile)

# def track_first_chroma_labels_pair(tod):
#     if isinstance(tod, TrackOnDisk):
#         trackid, trackfile = tod
#     else:
#         tod = tod.numpy()
#         trackid = tod[0].item()
#         trackfile = Path(tod[1].item())
#     labels = fmadata.get_genres_for_track(trackid)
#     for chroma in generate_chromas_from_file(trackfile):
#         return (chroma, labels)

# def gen_chromas_with_labels(subset = "small"):
#     """Generator: (input, labels) for tf.data.Dataset
#
#     input: the chroma for the chunk
#     labels: the numpy MultiHot array for genres of the track the chunk is from
#     """
#     target_tracks = list(subset_tracks_with_genres(subset))
#     random.Random(random_number).shuffle(target_tracks)
#     for trackid, trackfile in target_tracks:
#         labels = fmadata.get_genres_for_track(trackid)
#         for chroma in generate_chromas_from_file(trackfile):
#             yield (chroma, labels)

def tf_track_data_pair(path):
    trackfile = Path(path.numpy().decode())
    trackid = int(trackfile.stem)
    labels = fmadata.get_genres_for_track(trackid)
    for chroma in generate_chromas_from_file(trackfile):
        return (chroma, labels)

files_list = list([str(x.path) for x in subset_tracks_with_genres("small")])
files_ds = tf.data.Dataset.from_tensor_slices(tf.constant(files_list))
files_ds.shuffle(len(files_list))

dataset = files_ds.map(
    lambda x: tf.py_function(tf_track_data_pair, [x,], (tf.float32, tf.float32)),
    num_parallel_calls=tf.data.AUTOTUNE,
)

# dataset = tf.data.Dataset.from_generator(
#     gen_chromas_with_labels,
#     output_types=(tf.float32, tf.float32),
# )

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

if __name__ == "__main__":

    if len(sys.argv) > 1:
        targetfile = tf.constant(sys.argv[1].encode())
        print(tf_track_data_pair(targetfile))

    print(f"{len(files_list)} files loaded as dataset sources")
    print(next(iter(train_dataset)))
