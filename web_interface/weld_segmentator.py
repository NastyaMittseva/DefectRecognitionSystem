import numpy as np
import cv2
from keras.preprocessing import image
from search_boundaries import *
import tensorflow as tf
from grpc.beta import implementations
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2


class WeldSegmentator():
    """ Осуществляет сегментацию области шва.
        Изначально загружает данные, затем предсказывает вероятностную маску шва.
        После преобразует вероятностную маску в бинарную маску и сохраняет.
    """
    def __init__(self):
        self.threshold = 0.2
        self.X = None
        self.mask = None
        self.weld_mask = None

    def get_images(self, path_processing_img):
        """ Получает изображения. """
        self.X = image.load_img(path_processing_img, target_size=(800,800))
        self.X = image.img_to_array(self.X)
        self.X = np.expand_dims(self.X, axis=0)

    def predict_weld_mask(self):
        """ Предсказывает вероятностную маску шва. """
        
        channel = implementations.insecure_channel('localhost', 8500)
        stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)
        request = predict_pb2.PredictRequest()
        request.model_spec.name = 'weld_segmentator'
        request.model_spec.signature_name = 'predict'
        request.inputs['images'].CopyFrom(
            tf.contrib.util.make_tensor_proto(self.X, shape=self.X.shape))
        result = stub.Predict(request, 10.0)
        self.mask = np.array(result.outputs['scores'].float_val).reshape([800, 800])

    def apply_threshold(self):
        """ Преобразовывает вероятностную маску шва в бинарную маску с использованием порога. """
        y = self.mask
        y = cv2.resize(y, (1152, 1152))
        y[y < self.threshold] = 0.
        y[y >= self.threshold] = 1.
        self.weld_mask = y * 255
        self.weld_mask = self.weld_mask.astype(np.uint8)

    def determine_result(self):
        """ Определяет, найден ли шов или нет. """
        i, y1, y2 = find_last_ys(self.weld_mask)
        if y1 == 0 and y2 == 0 and i == 0:
            return "weld isn't found"
        else:
            return "weld is found"

    def save_weld_result(self, path_weld_mask):
        """ Сохраняет маску. """
        cv2.imwrite(path_weld_mask, self.weld_mask)

    def join_mask_img(self, path_weld_mask):
        """ Объединяет маску и изображение, перекрашивая шов в желтый цвет, а фон в синий цвет. """
        alpha = 0.5
        color_mask = np.zeros((1152, 1152, 3), dtype=np.uint8)
        color_mask[np.where((self.weld_mask == [0]))] = [255, 0, 0]
        color_mask[np.where((self.weld_mask == [255]))] = [0, 255, 255]
        self.X = cv2.resize(np.array(self.X[0], dtype=np.uint8), (1152, 1152))
        added_image = cv2.addWeighted(color_mask, alpha, self.X, 1 - alpha, 0)
        cv2.imwrite(path_weld_mask, added_image)