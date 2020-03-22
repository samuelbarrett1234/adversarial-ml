import numpy as np
import pandas as pd
from sklearn.metrics import auc, roc_curve
import argparse as ap
import models.data_util
from tensorflow.python.keras import Sequential
from tensorflow.python.keras.layers import Flatten, Dropout, Conv2D, Dense
from tensorflow.python.keras.utils.np_utils import to_categorical


n = 10000
n_features = 213
positive_k = 800
num_f = 1196

data = '../../data/Co_600K_Jul2019_6M.pkl'
train_test_split = 0.2
threshold = 0.9



if __name__ == '__main__':
    print("Loading training data...")

    # Use helper function to convert everything to numpy etc:
    x, y = models.data_util.load_data(data, shuffle=True)
    y = y.reshape(len(y), 1)
    n = 10000
    n_features = 213
    positive_k = 800
    num_f = 1196

    x, y = x[:n], y[:n]

    # Split data into train/test
    n_train = int(n * (1 - train_test_split))

    x_train, y_train = np.row_stack((x[:positive_k], x[num_f:n_train])), np.row_stack(
        (y[:positive_k], y[num_f:n_train]))
    x_test, y_test = np.row_stack((x[n_train:], x[positive_k:num_f])), np.row_stack((y[n_train:], y[positive_k:num_f]))

    x_train = x_train.reshape(len(x_train), n_features, 1, 1)
    x_test = x_test.reshape(len(x_test), n_features, 1, 1)

    y_train = to_categorical(y_train.reshape(-1, 1))
    model = Sequential()
    model.add(Conv2D(32, kernel_size=3, activation='tanh', padding='same', input_shape=(n_features, 1, 1)))
    model.add(Conv2D(64, kernel_size=3, activation='tanh', padding='same'))
    model.add(Dropout(0.5))
    model.add(Flatten())
    model.add(Dense(300, activation='relu'))
    model.add(Dense(2, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy'])
    model.fit(x_train, y_train,
              batch_size=200,
              epochs=2,
              validation_split=train_test_split)

    model.evaluate(x_test, to_categorical(y_test.reshape(-1, 1)), batch_size=200)
    y_pred = model.predict(x=x_test, batch_size=200)
    y_pred = y_pred[:, 1].reshape(y_test.shape)

    fpr, tpr, _ = roc_curve(y_test, y_pred)
    roc = auc(fpr, tpr)
    # convert probabilities to predictions via thresholding:
    y_pred = models.data_util.threshold(y_pred, threshold)

    # compute accuracy separately on positive and negative examples
    true_neg, true_pos = models.data_util.get_accuracy(
        y_test, y_pred
    )
    print("Results:", "True negative rate =",
          true_neg, "True positive rate =", true_pos,
          "ROC curve =", roc)

    performance_name = str(np.int(np.floor(100 * roc)))
    model.save(filepath="../model_weights/" + "conv_net_model_with_auc_" + performance_name
                        + "_posExamples_" + str(positive_k) + "_datapoints_" + str(n), overwrite=True)