import numpy as np
import cv2
from search_boundaries import *


class IntermediateProcessor():
    """ Осуществляет обработку маски шва и формирует область шва.
        Изначально осуществляет поиск границ шва по маске.
        Затем к полученным границам добавляет припуски по 5 мм.
        После вырезает и формирует область шва.
    """
    def __init__(self):
        self.boundar_y1 = None
        self.boundar_y2 = None
        self.weld_gray_bgr = np.zeros((1152, 1152, 1), np.uint8)

    def find_weld_boundaries(self, path_weld_mask):
        """ Определяет границы шва по маске. """
        img = cv2.imread(path_weld_mask, -1)
        paint = cv2.imread(path_weld_mask)
        i, y1, y2 = find_last_ys(img)
        if y1 == 0 and y2 == 0 and i == 0:
            return -1
        else:
            self.boundar_y1, self.boundar_y2 = get_list_ys(i, y1, y2, img)
            paint_boundaries(self.boundar_y1, self.boundar_y2, paint)
            cv2.imwrite(path_weld_mask, paint)
            return 0

    def add_allowances(self):
        """ Добавляет припуски на швы по 5 мм. """
        self.boundar_y1 = [x - 50 for x in self.boundar_y1]
        self.boundar_y2 = [x + 50 for x in self.boundar_y2]

    def get_weld_and_gray_bgr(self, path_processing_img):
        """ Заполняет фон (т.е. то, что не является областью шва) серым цветом. """
        processing_img = cv2.imread(path_processing_img, 0)
        self.weld_gray_bgr.fill(128)
        for m in range(len(self.boundar_y1)):
            for k in range(self.boundar_y1[m], self.boundar_y2[m], 1):
                self.weld_gray_bgr[k][m] = processing_img[k][m]

    def form_weld_area(self, path_scale_weld):
        """ Вырезает область шва, масштабирует ее и сохраняет. """
        min_boundar_y1 = min(self.boundar_y1)
        max_boundar_y2 = max(self.boundar_y2)
        crop_img = self.weld_gray_bgr[min_boundar_y1:max_boundar_y2, 0:1152]
        scale_img = cv2.resize(crop_img, (1152, 384))
        cv2.imwrite(path_scale_weld, scale_img)
        return min_boundar_y1, max_boundar_y2
