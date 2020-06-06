import cv2
import numpy as np
from skimage import io
from skimage.measure import label, regionprops
from grpc.beta import implementations
import tensorflow as tf
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2
from keras.preprocessing import image


keys = {0: 'Прожёг', 1: 'Трещина', 2: 'Несплаление-подрез', 3: 'Перехват', 4: 'Непровар', 5: 'Шлаки-поры', 6: 'Обрыв шва', 7: 'Визуал. дефект'}


class DefectClassificator():
    """
        Осуществляет классификацию дефектов по 7 типам + фон.
        Сначала проверяет, найдены ли были вообще дефекты с помощью  FgSegNet_M.
        Если дефекты найдены, тогда все то, что не дефекты, закрашивается белым цветом.
        Затем подается на вход Unet для классификации.
    """
    def __init__(self):
        self.data = None
        self.class_mask = None
        self.results = []
        
    def check_mask_on_defects(self, path_defect_mask):
        """ Проверяет по маске, нашла ли FgSegNet_M дефекты и возвращает ответ. """
        defect_mask = cv2.imread(path_defect_mask, 0)
        hist, bins = np.histogram(defect_mask.flatten(), 256, [0, 256])
        black_color = hist[0]
        white_color = hist[-1]
        if white_color == 0 and black_color == defect_mask.shape[0]*defect_mask.shape[1]:
            return False
        else:
            return True

    def predict_classes_defects(self, path_scale_weld, path_defect_mask):
        """ Вырезает дефекты по маске, затем для каждого дефекта предсказываются классы по топ-2. """
        processing_image = cv2.imread(path_scale_weld)
        defect_mask = io.imread(path_defect_mask)
        label_mask = label(defect_mask)
        props = regionprops(label_mask)
        for prop in props:
            if int(prop.bbox[0]-7) > 0 and int(prop.bbox[2]+7) < 384 and int(prop.bbox[1]-7) > 0 and int(prop.bbox[3]+7) < 1152:
                bbox = [int(prop.bbox[0]-7), int(prop.bbox[1]-7), int(prop.bbox[2]+7), int(prop.bbox[3]+7)]
            else:
                bbox = prop.bbox
            crop_defect = processing_image[bbox[0]:bbox[2],bbox[1]:bbox[3]]
            crop_defect = np.array(cv2.resize(crop_defect, (256, 256)), dtype=np.float32)
            crop_defect = np.expand_dims(crop_defect, axis=0)
            crop_defect /= 255.
            
            channel = implementations.insecure_channel('localhost', 8500)
            stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)
            request = predict_pb2.PredictRequest()
            request.model_spec.name = 'defect_classificator'
            request.model_spec.signature_name = 'predict'

            request.inputs['images'].CopyFrom(
                tf.contrib.util.make_tensor_proto(crop_defect, shape=crop_defect.shape))

            result = stub.Predict(request, 10.0)
            pred = np.array(result.outputs['scores'].float_val)
            classes = np.argsort(pred, axis=0)[-2:]
            
            defect_classes = {}
            for i in range(len(classes)):
                group = keys[classes[i]]
                prob = pred[classes[i]]
                defect_classes[group] = prob
            self.results.append([bbox, defect_classes])
