import cv2
import numpy as np
import tensorflow as tf

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

    def get_defect_mask(self, path_scale_weld, path_defect_mask, path_white_bkg):
        """
            Формирует входные данные для Unet.
            Сначала, весь фон закрашивается белым цветом.
            Затем, снимок преобразуется к формату входных данных Unet.
        """
        processing_image = cv2.imread(path_scale_weld)
        defect_mask = cv2.imread(path_defect_mask,0)
        processing_image[np.where((defect_mask == [0]))] = [255, 255, 255]
        cv2.imwrite(path_white_bkg, processing_image)
        imgs = []
        imgs.append(processing_image)
        self.data = np.array(imgs)

    def predict_classes_defects(self, model):
        """ Предсказывает маски с дефектами по классам с помощью Unet. """
        graph = tf.get_default_graph()
        with graph.as_default():
            self.class_mask = model.predict(self.data)[0]

    def combine_and_save_mask(self, path_classification):
        """
            Комбинирует все предсказанные маски в одну, закрашивая каждый дефект определенным цветом,
            и сохраняет ее.
        """
        combined_mask = np.zeros(self.class_mask.shape[:-1])
        for lays in range(self.class_mask.shape[-1]):
            combined_mask += np.round(self.class_mask[:, :, lays]) * lays
        color_mask = np.zeros((combined_mask.shape[0], combined_mask.shape[1], 3), dtype=np.uint8)
        color_mask[np.where((combined_mask == [0.0]))] = [0, 0, 0]
        color_mask[np.where((combined_mask == [1.0]))] = [0, 0, 255]
        color_mask[np.where((combined_mask == [2.0]))] = [255, 0, 0]
        color_mask[np.where((combined_mask == [3.0]))] = [170, 170, 170]
        color_mask[np.where((combined_mask == [4.0]))] = [255, 255, 0]
        color_mask[np.where((combined_mask == [5.0]))] = [0, 255, 255]
        color_mask[np.where((combined_mask == [6.0]))] = [255, 0, 255]
        color_mask[np.where((combined_mask == [7.0]))] = [18, 255, 20]
        color_mask[np.where((combined_mask == [8.0]))] = [255, 255, 255]
        cv2.imwrite(path_classification, color_mask)

