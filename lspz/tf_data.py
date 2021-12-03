
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

def track_has_genres(path):
    trackfile = Path(path.numpy().decode())
    trackid = int(str(trackfile.name).split('.')[0])
    return trackid in fmadata.track_genres_labels.index

# def tf_track_data_pair(path):
#     trackfile = Path(path.numpy().decode())
#     trackid = int(trackfile.stem)
#     labels = fmadata.get_genres_for_track(trackid)
#     for chroma in generate_chromas_from_file(trackfile):
#         return (chroma, labels)

def tf_pair_from_npz(path):
    trackfile = Path(path.numpy().decode())
    trackid = int(str(trackfile.name).split('.')[0])
    labels = fmadata.get_genres_for_track(trackid)
    for chroma in np.load(trackfile).values():
        return (chroma, labels)

# files_list = list([str(x.path) for x in subset_tracks_with_genres("small")])
files_list = tf.data.Dataset.list_files(
    str(fmadata.base_path / f"lspz_chromas_small") + "/*/*.chroma.npz",
    seed=42, name="lspz_npz_chromas",
)

files_ds = files_list.filter(
    # lambda x: track_has_genres(int(str(Path(x.numpy().decode()).name).split('.')[0])),
    lambda x: tf.py_function(track_has_genres, [x,], (tf.bool), name="track_has_genres"),
)

dataset = files_ds.map(
    lambda x: tf.py_function(tf_pair_from_npz, [x,], (tf.float32, tf.float32), name="tf_pair_from_npz"),
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

    # if len(sys.argv) > 1:
    #     targetfile = tf.constant(sys.argv[1].encode())
    #     print(tf_track_data_pair(targetfile))

    print(f"{files_list.cardinality()} chroma files")
    print(f"{dataset.cardinality()} entries in dataset")
    print(f"first entry:")
    print(next(iter(train_dataset)))
