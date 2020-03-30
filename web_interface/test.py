import os
from preprocessor import Preprocessor
from data_handler import DataHandler
import cv2
import numpy as np

data_handler = DataHandler()
filename = '1900745798_13966_013853.VRC'
extact_folder = 'C:/Users/Nastya/Desktop/extract/'
png_names = data_handler.convert_vrc_to_png(filename, extact_folder, extact_folder)
for png_name in png_names:
    print(png_name)
    # img = cv2.imread(extact_folder+png_name, -1)
    # processing_img = np.zeros((1152, 1152, 1), dtype=np.uint16)
    # processing_img = [(-img[i - 2][j] + 8 * img[i - 1][j] - 8 * img[i + 1][j] + img[i + 2][j]) / 12 for j in range(len(img)) for i
    #         in range(2, len(img[j]) - 2, 1)]
    # preprocessor = Preprocessor(png_name)
    # preprocessor.process_by_gradient(extact_folder)
    # preprocessor.normalize_img()
    # preprocessor.convert_to_8bit(extact_folder)