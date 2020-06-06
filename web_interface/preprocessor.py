import cv2
import numpy as np
import time


class Preprocessor():
    """ Осуществляет предобработку изображения.
        Изначально обрабатывает по градиенту, затем нормализует по гистограмме интенсивности цвета.
        Обработанное изображение конверитиркует в 8-битный формат и сохраняет.
    """
    def __init__(self, tiff_name):
        # self.processing_img = None
        self.processing_img = np.zeros((1152, 1152), dtype=np.uint16)
        self.name = tiff_name

    def process_by_gradient(self, path_input_img):
        """ Обрабатывает изображение по градиенту. """
        img = cv2.imread(path_input_img + self.name, -1)
        img = img.astype(np.uint32)
        for i in range(2, len(img) - 2):
            self.processing_img[i] = (np.uint16(-img[i - 2]) + 8 * img[i - 1] - 8 * img[i + 1] + img[i + 2]) / 12

    def normalize_img(self):
        """ Нормализует изображение по гистограмме интенсивности цвета. """
        hist, bins = np.histogram(self.processing_img.flatten(), 65536, [0, 65536])
        cdf = hist.cumsum()
        cdf_m = np.ma.masked_equal(cdf, 0)
        cdf_m = (cdf_m - cdf_m.min()) * 65535 / (cdf_m.max() - cdf_m.min())
        cdf = np.ma.filled(cdf_m, 0).astype('uint16')
        self.processing_img = cdf[self.processing_img]

    def convert_to_8bit(self, path_processing_img):
        """ Конвертирует изображение из 16 бит в 8 бит и сохраняет. """
        self.processing_img = (self.processing_img / 256).astype('uint8')
        self.processing_img = cv2.cvtColor(self.processing_img, cv2.COLOR_GRAY2RGB)
        cv2.imwrite(path_processing_img + self.name, self.processing_img)
