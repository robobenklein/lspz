
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from .chroma import window_count, chunk_sample_count
from .fma_data import data as fmadata
from . import tf_data

image2d_dimensions = (1025, 1025, 1)
# output_dimensions =
num_classes = fmadata.genres.index.size


def create_model_type_A():
    """The first model attempt..."""
    print(f"LSPZ constructing model type A")
    # NOTE hardcode: shape of output for 22050/2048/256
    inputs = keras.Input(shape=tf_data.chroma_dimensions)

    # scaling from chroma's dB (0 to -80)
    x = layers.Rescaling(1/16, offset=5)(inputs)
    # trying to prevent overfitting
    x = layers.GaussianNoise(0.02)(x)
    x = layers.Reshape(image2d_dimensions)(x)
    x = layers.Conv2D(
        1, 26, activation="sigmoid",
        data_format="channels_last",
    )(x)
    x = layers.MaxPooling2D(pool_size=(5, 5))(x)
    x = layers.Conv2D(filters=32, kernel_size=5, activation="relu")(x)
    x = layers.MaxPooling2D(pool_size=(20, 20))(x)
    # x = layers.MaxPooling2D(pool_size=(100, 100))(x)
    x = layers.Dense(num_classes, activation="relu")(x)

    x = layers.Flatten()(x)

    outputs = layers.Dense(num_classes, activation="softplus")(x)

    model = keras.Model(inputs=inputs, outputs=outputs)

    return model

def create_model_type_B():
    """The second model attempt..."""
    print(f"LSPZ constructing model type B")
    # NOTE hardcode: shape of output for 22050/2048/256
    inputs = keras.Input(shape=tf_data.chroma_dimensions)

    # scaling from chroma's dB (0 to -80)
    x = layers.Rescaling(1/16, offset=5)(inputs)
    # trying to prevent overfitting
    x = layers.GaussianNoise(0.02)(x)
    x = layers.Reshape(image2d_dimensions)(x)

    x = layers.Conv2D(
        1, 26, activation="sigmoid",
        data_format="channels_last",
    )(x)
    x = layers.MaxPooling2D(pool_size=(5, 5))(x)
    x = layers.Conv2D(filters=32, kernel_size=6, activation="relu")(x)
    # x = layers.MaxPooling2D(pool_size=(20, 20))(x)
    x = layers.MaxPooling2D(pool_size=(5, 5))(x)
    x = layers.Dense(num_classes, activation="relu")(x)

    x = layers.Flatten()(x)

    outputs = layers.Dense(num_classes, activation="softplus")(x)

    model = keras.Model(inputs=inputs, outputs=outputs)

    return model

if __name__ == '__main__':
    print(f"")

    model = create_model_type_B()
    model.summary()
    model.compile(optimizer=keras.optimizers.RMSprop(learning_rate=1e-3),
        loss=keras.losses.CategoricalCrossentropy())

    print(f"Model output shape: {model.output_shape}")

    train_batch_size = 16
    ds = tf_data.train_dataset.batch(train_batch_size)
    ds = ds.prefetch(train_batch_size * 4)
    val_dataset = tf_data.test_dataset.batch(train_batch_size // 4)
    val_dataset = val_dataset.prefetch(train_batch_size)

    callbacks = [
        keras.callbacks.ModelCheckpoint(
            filepath='data/model/model_{epoch}',
            save_freq='epoch'
        ),
        keras.callbacks.TensorBoard(log_dir='./data/logs'),
    ]

    history = model.fit(
        ds, epochs=10, validation_data=val_dataset, callbacks=callbacks,
    )

    loss, acc = model.evaluate(val_dataset)  # returns loss and metrics
    print("loss: %.2f" % loss)
    print("acc: %.2f" % acc)
