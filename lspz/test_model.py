
import sys
import argparse
from pathlib import Path
import pprint

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow import keras
from tensorflow.keras import layers
from mediafile import MediaFile
import audioread

from .chroma import generate_chromas_from_file
from .fma_data import data as fmadata
from . import tf_data

image2d_dimensions = (1025, 1025, 1)
# output_dimensions =
num_classes = fmadata.genres.index.size
genre_names = list(fmadata.genre_name_list)


def load_model_from_path(path: Path):
    """Load'n up"""
    model = tf.keras.models.load_model(str(path), compile=False)
    model.compile(
        metrics=[
            "binary_accuracy",
            "binary_crossentropy",
            "mae",
            keras.metrics.Precision(),
            keras.metrics.Recall(),
        ],
        # metrics=["accuracy", "precision", "truenegatives", "truepositives"],
    )
    return model

def predict_genres(model, file: Path, plotstuff=False):
    # print(f"Getting chromas from file...")
    chromas = list(generate_chromas_from_file(file))
    # print(f"First chroma:")
    # print(chromas[0])
    total_preds = None
    for idx, chroma in enumerate(chromas):
        chroma = np.expand_dims(chroma, axis=0)
        # print(f"Predicting chroma {idx+1}/{len(chromas)} ...")
        prediction = model.predict(chroma)

        if total_preds is not None:
            total_preds = np.add(total_preds, prediction)
        else:
            total_preds = prediction

    if total_preds is None:
        print(f"No predictions returned for {file}")
        return []

    preds = (total_preds / len(chromas)).tolist()[0]
    # print(preds)
    genre_scores = dict(zip(genre_names, preds))
    top_genres = {k: v for k, v in sorted(genre_scores.items(), key=lambda item: item[1], reverse=True)[:10]}
    # print(top_genres)

    genre_scores_unordered = [v for v in genre_scores.values()]
    # breaks = jenkspy.jenks_breaks(genre_scores_unordered, nb_class=50)
    # # print(f"breaks: {breaks}")
    # cutoff = breaks[-2]
    cutoff = list(top_genres.values())[0] * 0.85
    output_genres_names = []
    for k, v in top_genres.items():
        if v >= cutoff:
            output_genres_names.append(k)

    if plotstuff:
        plt.bar(*zip(
            *top_genres.items()
        ))
        plt.show()

    return output_genres_names

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p", "--plot",
        action="store_true",
        help="Show a plot of the model's scores",
    )
    parser.add_argument(
        'model',
        type=Path,
        help="Path to the saved model to load",
    )
    parser.add_argument(
        "files",
        type=Path,
        help="Audio files to run model across",
        # action="append",
        nargs="*",
    )

    args = parser.parse_args()

    model = load_model_from_path(args.model)
    model.summary()
    print(f"Model output shape: {model.output_shape}")

    test_dataset = tf_data.test_dataset.batch(4)
    metrics = model.evaluate(test_dataset, return_dict=True)

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(metrics)
