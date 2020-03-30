import subprocess
import struct
from PIL import Image
import shutil
import os

class DataHandler():
    """ Осуществляет сбор данных с сервера.
        Изначально забирает 7z с сервера и распаковывает их.
        Затем конвертирует VRC в TIFF и сохраняет их.
    """
    def __init__(self):
        self.z_location = 'C:/Program Files/7-Zip/7z.exe'

    def extract_vrc_from_7z(self, path_to_file, file_name, extact_folder):
        """ Получает 7z с сервера, извлекает VRC, сохраняет их в папки, предварительно очищенные,
            и возвращает имена файлов.
        """
        if os.path.exists(extact_folder):
            shutil.rmtree(extact_folder)
        os.makedirs(extact_folder)
        vrc_name = file_name[:-2] + 'VRC'
        extract_file = path_to_file + '/' + file_name
        extract_target = self.z_location + ' e ' + '"' + extract_file + '"' + ' -o' + '"' + extact_folder + '"'
        subprocess.run(extract_target)
        return vrc_name

    def convert_vrc_to_png(self, vrc_name, extact_folder, path_input_img):
        """ Конвертирует VRC в формат TIFF, подтягивая метр трубы, на котором сделан снимок. """
        begin_sep = b'\xe0\xff\xff\xff\xff\xfe\xff\xdd\xe0\xff\xff\xff\xff\x01p\x01\x01SL'  # начало снимка
        end_sep = b'\xff\r\xe0\xff\xff\xff\xff\xfe\xff\x00\xe0\xff\xff\xff\xff\x08\x00"\x00DA\n'  # конец снимка
        f = open(extact_folder + '/' + vrc_name, "rb").read()
        image = f.split(end_sep, maxsplit=-1)
        # временные поправки, берем только по 3 снимка с каждого VRC
        png_names = []
        for number in range(len(image)):
            image[number] = image[number].split(begin_sep, maxsplit=-1)
            sep_width_height = b'\x80\x04\x00\x00\x80\x04\x00\x00'  # строка 1152 на 1152 -65535
            find_metr = image[number][0].split(sep_width_height, maxsplit=-1)
            if len(find_metr) == 2:
                png_name = save_png(find_metr, image, number, path_input_img, vrc_name)
                png_names.append(png_name)
        return png_names


def save_png(find_metr, image, number, path_input_img, vrc_name):
    """ Определяет метр и конвертирует байты в tiff. """
    start_metr = struct.unpack('d', find_metr[1][4:12])
    finish_metr = struct.unpack('d', find_metr[1][12:20])
    print('Линейка: от ' + str(start_metr[0]) + ' до ' + str(finish_metr[0]))

    image[number][1] = image[number][1][30:]
    if number == len(image) - 1:
        image[number][1] = image[number][1][:(len(image[number][1]) - 23)]

    im = Image.frombytes('I;16', (int(len(image[number][1]) / 1152 / 2), 1152), image[number][1])
    name = vrc_name[:-4] + "_" + "frame" + str(number) + "_" + str(round(start_metr[0])) + "_" + str(
        round(finish_metr[0])) + ".png"
    im.save(path_input_img + name)
    return name
