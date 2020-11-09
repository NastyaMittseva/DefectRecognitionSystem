from keras.preprocessing import image as kImage
import numpy as np
import tensorflow as tf
from grpc.beta import implementations
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2


class WeldClassificator():
    """ Осуществляет класссификацию шва на два вида - "дефектный" и "годный".
        Если шов годный, то на этом заканчивается обработка снимка.
        Если шов дефектный, он подается дальше на сегментацию и классификацию.
    """
    def __init__(self):
        self.threshold = 0.9
        self.image = None
        self.result = None

    def get_weld_area(self, path_scale_weld):
        """ Получает входное изображение и нормализует его. """
        img = kImage.load_img(path_scale_weld)
        self.image = kImage.img_to_array(img)
        self.image = np.expand_dims(self.image, axis=0)
        self.image /= 255.
        
    def predict_weld_class(self):
        """ Классифицирует шов. """
        
        channel = implementations.insecure_channel('localhost', 8500)
        stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)
        request = predict_pb2.PredictRequest()
        request.model_spec.name = 'weld_classificator'
        request.model_spec.signature_name = 'predict'

        request.inputs['images'].CopyFrom(
            tf.contrib.util.make_tensor_proto(self.image, shape=self.image.shape))

        prediction = stub.Predict(request, 10.0)
        self.result = np.array(prediction.outputs['scores'].float_val)

    def set_label(self):
        """ По заданному порогу присваивает метку класса. """
        if self.result[0] > self.threshold:
            return "defects aren't found"
        else:
            return "defects are found"