
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from .chroma import window_count, chunk_sample_count
from .fma_data import data as fmadata

input_dimensions = (1025, 1025, 1)
# output_dimensions =
num_classes = fmadata.genres.index.size


def create_model_type_A():
    """The first model attempt..."""
    print(f"LSPZ constructing model type A")
    # NOTE hardcode: shape of output for 22050/2048/256
    inputs = keras.Input(input_dimensions)

    # scaling from chroma's dB (0 to -80)
    x = layers.Rescaling(1/16, offset=5)(inputs)
    # trying to prevent overfitting
    x = layers.GaussianNoise(0.02)(x)
    x = layers.Conv2D(
        32, (3, 3), activation="sigmoid",
    )(x)
    x = layers.MaxPooling2D(pool_size=(3, 3))(x)
    x = layers.Conv2D(filters=32, kernel_size=(3, 3), activation="relu")(x)
    x = layers.MaxPooling2D(pool_size=(3, 3))(x)
    x = layers.Dense(window_count, activation="relu")(x)

    outputs = layers.Dense(num_classes, activation="softplus")(x)

    model = keras.Model(inputs=inputs, outputs=outputs)

    return model

if __name__ == '__main__':
    print(f"")

    m_A = create_model_type_A()
    m_A.summary()
    m_A.compile(optimizer=keras.optimizers.RMSprop(learning_rate=1e-3),
        loss=keras.losses.CategoricalCrossentropy())
