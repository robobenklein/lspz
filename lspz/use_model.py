
import sys
import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow import keras
from tensorflow.keras import layers

from .chroma import generate_chromas_from_file
from .fma_data import data as fmadata
# from . import tf_data

image2d_dimensions = (1025, 1025, 1)
# output_dimensions =
num_classes = fmadata.genres.index.size


def load_model_from_path(path: Path):
    """Load'n up"""
    return tf.keras.models.load_model(str(path))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'model',
        type=Path,
        help="Path to the saved model to load",
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Audio file to run model across",
    )

    args = parser.parse_args()

    model = load_model_from_path(args.model)
    model.summary()

    print(f"Model output shape: {model.output_shape}")

    genre_names = list(fmadata.genre_name_list)

    print(f"Getting chromas from file...")

    chromas = list(generate_chromas_from_file(args.file))

    print(f"First chroma:")
    print(chromas[0])

    for chroma in chromas:
        chroma = np.expand_dims(chroma, axis=0)
        prediction = model.predict(chroma)
        # print(prediction)

        preds = prediction.tolist()[0]
        # print(preds)
        genre_scores = dict(zip(genre_names, preds))
        top_genres = {k: v for k, v in sorted(genre_scores.items(), key=lambda item: item[1], reverse=True)[:10]}

        print(top_genres)

        plt.bar(*zip(
            *top_genres.items()
        ))

        break

    plt.show()
