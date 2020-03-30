from keras.preprocessing import image as kImage
from keras import backend as K
import tensorflow as tf

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
        self.image = self.image.reshape((1,) + self.image.shape)
        self.image /= 255.

    def predict_weld_class(self, model):
        """ Классифицирует шов. """
        # session = tf.keras.backend.get_session()
        # graph = session.graph
        graph = tf.get_default_graph()
        with graph.as_default():
            self.result = model.predict([self.image])

    def set_label(self):
        """ По заданному порогу присваивает метку класса. """
        if self.result[0][0] > self.threshold:
            return "Дефекты не найдены"
        else:
            return "Дефекты найдены"