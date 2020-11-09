def check_up(y, i, img):
    """ Проверяет, является ли y границей перехода между черным и белым на маске. """
    for k in range(1, 5):
        if (y - k) < 0 or (y+k) > 1151:
            return False
        elif img[y-k][i] > 10 or img[y+k][i] < 245:
            return False
    return True


def check_down(y, i, img):
    """ Проверяет, является ли y границей перехода между белым и черным на маске. """
    for k in range(1, 5):
        if (y - k) < 0 or (y+k) > 1151:
            return False
        elif img[y-k][i] < 245 or img[y+k][i] > 10:
            return False
    return True


def find_y1_y2(start, end, step, img):
    """ Находит участок, на котором можно найти y1 и y2 такие, что расстояние между ними больше 60 пикселей. """
    y1, y2 = 0, 0
    for i in range(start, end, step):
        for j in range(0, 1152, 1):
            if check_up(j, i, img):
                y1 = j
                break
        for j in range(1151, 0, -1):
            if check_down(j, i, img):
                y2 = j
                break
        if (abs(y2 - y1) > 60) and (abs(y2 - y1) < 800):
            return i, y1, y2
        elif (abs(y2 - y1) > 800) or (abs(y2 - y1) < 60):
            return 0, 0, 0
        else:
            continue


def find_last_ys(img):
    """ Берет начальные y1 и y2 на участке 1/3 шва и 2/3 шва, и сравнивает их, чтобы разница между у не была больше 20
        пикселей. Если разница больше 50 пикселей, значит возможно в какой-то части был захвачен не шов, а какой-нибудь
        шум, если нейронка плохо распознала шов. Тогда берутся y1 и y2 на участке 1/2 шва, и рассчитывается разница.
        Если разница в каком-нибудь случае меньше 20 пикселей, тогда берется середина.
    """
    i_1_3, y1_1_3, y2_1_3 = find_y1_y2(int(1152 / 3), 0, -1, img)
    i_2_3, y1_2_3, y2_2_3 = find_y1_y2(int(1152/3*2), 1152, 1, img)
    if y1_1_3 == 0 and y2_1_3 == 0 or y1_2_3 == 0 and y2_2_3 == 0:
        return 0, 0, 0
    else:
        if abs(y1_1_3 - y1_2_3) < 50 and abs(y2_1_3-y2_2_3) < 50:
            return i_1_3, y1_1_3, y2_1_3
        else:
            i_1_2, y1_1_2, y2_1_2 = find_y1_y2(int(1152 / 2), 0, -1, img)
            if abs(y1_1_3 - y1_1_2) < 50 and abs(y2_1_3-y2_1_2) < 50 or abs(y1_2_3 - y1_1_2) < 50 and \
                    abs(y2_2_3-y2_1_2) < 50:
                return i_1_2, y1_1_2, y2_1_2
            else:
                return 0, 0, 0


def find_boundaries(start, end, step, y, boundaries, check, img):
    """ Динамичный поиск y1 и y2 в каждом столбце, двигаясь то вверх, то вниз. """
    stop = 15
    y_start1 = y
    y_start2 = y
    for i in range(start, end, step):
        k = 0
        l = 0
        while k < stop and l < stop:
            if check(y_start1, i, img) or check(y_start2, i, img):
                if check(y_start1, i, img):
                    boundaries[i] = y_start1
                elif check(y_start2, i, img):
                    boundaries[i] = y_start2
                break
            else:
                y_start1 = y_start1 + 1
                k = k + 1
                y_start2 = y_start2 - 1
                l = l + 1
        if boundaries[i] == 0:
            boundaries[i] = boundaries[i-1] if start < end else boundaries[i+1]
        y_start1 = boundaries[i]
        y_start2 = boundaries[i]


def get_list_ys(i, y1, y2, img):
    """ Находятся все границы и соединяются в два массива: вверх и низ шва. """
    boundar_y1 = [0 for i in range(1152)]
    boundar_y2 = [0 for i in range(1152)]

    find_boundaries(i, -1, -1, y1, boundar_y1, check_up, img)
    find_boundaries(i, 1152, 1, y1, boundar_y1, check_up, img)
    find_boundaries(i, -1, -1, y2, boundar_y2, check_down, img)
    find_boundaries(i, 1152, 1, y2, boundar_y2, check_down, img)
    return boundar_y1, boundar_y2


def paint_boundaries(boundar_y1, boundar_y2, paint):
    """ Отрисовка границ шва на изображение синим цветом. """
    for i in range(1152):
        for j in range(1152):
            if (j == boundar_y1[i]) or (j == boundar_y2[i]):
                paint[j][i][0] = 204
                paint[j][i][1] = 0
                paint[j][i][2] = 0
