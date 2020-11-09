import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import operator

colors = {'Burnout':(0, 0, 255), 'Crack':(255, 0, 0), 'Unfused-undercut': (255, 0, 255),
          'Interception': (255, 166, 0), 'Lack of fusion': (255, 255, 0), 'Slags-Pores': (0, 255, 0),
          'Welding break': (0, 191, 255), 'Visual defect': (255, 192, 203)}


class Postprocessor():
    """ Осуществляет постобработку изображений.
        Изначально преобразует маску к размеру исходного изображения.
        Затем накладывает маску на исходное изображение.
        Формируются результаты в двух форматах - распознавание и классификация, и затем сохраняются.
    """
    def __init__(self):
        self.scaling_mask = np.zeros((1152, 1152, 3), dtype=np.uint8)
        self.alpha = 0.35
        self.weld_delta = 50

    def scale_mask(self, initial_boundar1, initial_boundar2, path_mask):
        """ Преобразует маску к размеру 1152 на 1152, предворительно масштабируя ее к начальной ширине изображения. """
        initial_width = initial_boundar2 - initial_boundar1
        weld_mask = cv2.imread(path_mask)
        weld_mask = cv2.resize(weld_mask, (1152, initial_width))
        final_mask = np.zeros((1152, 1152, 3), dtype=np.uint8)
        final_mask[initial_boundar1:initial_boundar2, 0:1152] = weld_mask
        self.scaling_mask = final_mask

    def overlay_binary_mask_on_image(self, path_processing_img, path_results_detection):
        """ Накладывает маску на исходное изображение для задачи детекции и сохраняет результаты.
        """
        processing_image = cv2.imread(path_processing_img)
        self.scaling_mask[np.where((self.scaling_mask == [0, 0, 0]).all(axis=2))] = [255, 0, 0]
        self.scaling_mask[np.where((self.scaling_mask == [255, 255, 255]).all(axis=2))] = [0, 255, 255]
        result = cv2.addWeighted(self.scaling_mask, self.alpha, processing_image, 1 - self.alpha, 0)
        cv2.imwrite(path_results_detection, result)

    def overlay_classes_mask_on_image(self, path_processing_img, path_results_by_class):
        """ Накладывает маску на исходное изображение для задачи классификации и сохраняет результаты.
        """
        processing_image = cv2.imread(path_processing_img )
        result = cv2.addWeighted(self.scaling_mask, self.alpha, processing_image, 1 - self.alpha, 0)
        cv2.imwrite(path_results_by_class, result)

    def paint_bb_and_classes(self, path_processing_img, path_classification, results, initial_boundar1, initial_boundar2):
        """ Рисует bounding box вокруг дефекта с id + внизу для каждого id одписывает классы с вероятностями.
            Цвет bounding box зависит от класса дефекта по топ-1.
        """
        scale = (initial_boundar2 - initial_boundar1) / 384

        processing_image = Image.open(path_processing_img).convert("RGB")
        draw = ImageDraw.Draw(processing_image)
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
        _, h = font.getsize('font')
        draw.rectangle((0, 1152 - h * len(results), 1152, 1152), fill='white')

        id = 0
        for i in range(len(results)):
            bbox, classes = results[i]
            sorted_classes = dict(sorted(classes.items(), key=operator.itemgetter(1), reverse=True))
            new_bbox = (bbox[0] * scale + initial_boundar1 - 3, bbox[1] - 3, bbox[2] * scale + initial_boundar1 + 3,
                        bbox[3] + 3)

            visual_defect = False
            if new_bbox[2] < initial_boundar1 + self.weld_delta or new_bbox[0] > initial_boundar2 - self.weld_delta:
                visual_defect = True

            if visual_defect:
                prior_color = second_color = colors['Visual defect']
                output = 'id ' + str(id) + ' - Visual defect: 100%'
            else:
                prior_color, second_color = get_get_colors(sorted_classes)
                # write classes for every id defect in weld
                output = 'id ' + str(id) + ' - '
                for class_ in sorted_classes.keys():
                    prob = np.round(sorted_classes[class_] * 100, 1)
                    if prob > 0.0:
                        output += str(class_) + ': ' + str(prob) + '%; '
                output += '\n'
            draw.text((0, 1152 - h * (len(results) - id) - 2), output, font=font, fill=(0, 0, 0))

            # paint bb with id
            draw.rectangle(((new_bbox[1], new_bbox[0]), (new_bbox[3], new_bbox[2])), outline=prior_color, width=4)
            draw.line(((new_bbox[1], new_bbox[2] - 3), (new_bbox[3], new_bbox[2] - 3)), fill=second_color, width=6)
            legend = str(id)
            w, h = font.getsize(legend)
            draw.rectangle((new_bbox[1], new_bbox[0] - h, new_bbox[1] + w, new_bbox[0]), fill=prior_color)
            draw.text((new_bbox[1], new_bbox[0] - h), legend, font=font, fill=(0, 0, 0))
            id += 1
        processing_image.save(path_classification, "JPEG")

def get_get_colors(sorted_classes):
    """ Определяет цвета bounding box по топ-1 и топ-2."""
    prior_class, second_class = list(sorted_classes.keys())[0], list(sorted_classes.keys())[1]
    prior_color = colors[prior_class]
    if np.round(list(sorted_classes.values())[1] * 100, 1) > 0.0:
        second_color = colors[second_class]
    else:
        second_color = prior_color
    return prior_color, second_color