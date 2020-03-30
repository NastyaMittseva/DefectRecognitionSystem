import keras
from keras.models import Model
from keras.layers import Conv2D, UpSampling2D, MaxPooling2D, Dropout,  Input, concatenate
from keras.optimizers import Adam
from keras import backend as keras
import tensorflow as tf
import numpy as np


class Unet_module():
    """
        Модуль с нейронной сетью Unet для семантической сегментации.
    """
    def __init__(self,input_shape,filters_dims):
        self.input_shape = input_shape
        self.filters_dims = filters_dims

    def Unet(self, activation='elu', kernel_initializer='glorot_uniform', padding='same'):
        """ Инициализация Unet. """
        inputs = Input(self.input_shape)
        new_inputs = inputs
        conv_layers = []

        # Фаза кодирования
        for i in range(len(self.filters_dims) - 1):
            conv = Conv2D(self.filters_dims[i], 3, activation=activation, padding=padding,
                          kernel_initializer=kernel_initializer)(new_inputs)
            conv = Conv2D(self.filters_dims[i], 3, activation=activation, padding=padding,
                          kernel_initializer=kernel_initializer)(conv)
            conv_layers.append(conv)
            new_inputs = MaxPooling2D(pool_size=(2, 2))(conv)

        # Промежуточная фаза
        conv = Conv2D(self.filters_dims[-1], 3, activation=activation, padding=padding,
                      kernel_initializer=kernel_initializer)(new_inputs)
        conv = Conv2D(self.filters_dims[-1], 3, activation=activation, padding=padding,
                      kernel_initializer=kernel_initializer)(conv)
        new_inputs = Dropout(0.5)(conv)

        self.filters_dims.reverse()
        conv_layers.reverse()

        # Фаза декодирования
        for i in range(1, len(self.filters_dims)):
            up = Conv2D(self.filters_dims[i], 3, activation=activation, padding=padding,
                        kernel_initializer=kernel_initializer)(UpSampling2D(size=(2, 2))(new_inputs))
            concat = concatenate([conv_layers[i - 1], up], axis=3)
            conv = Conv2D(self.filters_dims[i], 3, activation=activation, padding=padding,
                          kernel_initializer=kernel_initializer)(concat)
            new_inputs = Conv2D(self.filters_dims[i], 3, activation=activation, padding=padding,
                                kernel_initializer=kernel_initializer)(conv)
        outputs = Conv2D(9, 1, activation='softmax', padding='same',
                         kernel_initializer='glorot_uniform')(new_inputs)
        model = Model(input=inputs, output=outputs, name='UNet')
        model.compile(optimizer=Adam(lr=1e-4), loss='categorical_crossentropy', metrics=[mean_iou])
        return model


def mean_iou(y_true, y_pred):
    """ Метрика точности mIoU. """
    prec = []
    for t in np.arange(0.5, 1.0, 0.05):
        y_pred_ = tf.to_int32(y_pred > t)
        score, up_opt = tf.metrics.mean_iou(y_true, y_pred_, 2)
        keras.get_session().run(tf.local_variables_initializer())
        with tf.control_dependencies([up_opt]):
            score = tf.identity(score)
        prec.append(score)
    return keras.mean(keras.stack(prec), axis=0)
