import numpy as np
import cv2
from keras.preprocessing import image as kImage
from skimage.transform import pyramid_gaussian
import tensorflow as tf

class DefectDetector():
    """ Осуществляет распознавание дефектов в области шва.
        Изначально получает входные данные.
        Затем предсказывает вероятностную маску дефектов.
        После конвертирует вероятностную маску в бинарную и сохраняет ее.
    """
    def __init__(self):
        self.threshold = 0.45
        self.data = None
        self.probs = None
        self.defect_mask = None

    def prepare_input(self, path_scale_weld):
        """ Получает входное изображение и конвертирует его в три масштаба. """
        x = kImage.load_img(path_scale_weld)
        x = kImage.img_to_array(x)
        s1 = []
        s2 = []
        s3 = []
        s1.append(x)
        s1 = np.asarray(s1)
        pyramid = tuple(pyramid_gaussian(x / 255., max_layer=2, downscale=2))
        s2.append(pyramid[1] * 255.)
        s3.append(pyramid[2] * 255.)
        s2 = np.asarray(s2)
        s3 = np.asarray(s3)
        self.data = [s1, s2, s3]

    def predict_defect_mask(self, model):
        """ Предсказывает вероятностную маску дефектов. """
        graph = tf.get_default_graph()
        with graph.as_default():
            self.probs = model.predict(self.data, batch_size=1, verbose=1)
        self.probs = self.probs.reshape([self.probs.shape[0], self.probs.shape[1], self.probs.shape[2]])

    def apply_threshold(self):
        """ Преобразовывает вероятностную маску шва в бинарную маску с использованием порога. """
        y = self.probs[0]
        y[y < self.threshold] = 0.
        y[y >= self.threshold] = 1.
        self.defect_mask = y * 255
        self.defect_mask = self.defect_mask.astype(np.uint8)

    def save_defect_mask(self, path_defect_mask):
        """ Сохраняет маску. """
        dir_and_name = path_defect_mask[:-3]+'png'
        cv2.imwrite(dir_and_name, self.defect_mask)
