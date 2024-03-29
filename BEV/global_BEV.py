from BEV import getcolor
import cv2
import os
import sys
import shutil

##############################################################################

def start(output_path, map_path):

    global_output_path = os.path.join(output_path, 'global_map_frame')

    if not os.path.exists(global_output_path):
        os.makedirs(global_output_path)
    else:
        shutil.rmtree(global_output_path)
        os.makedirs(global_output_path)

    filename = 'global_result.txt'
    # ==============  Global ID BEV result  ===================
    file = open(os.path.join(output_path, filename), 'r')
    globals()['g_frame'.format(filename)], globals()['g_point'.format(filename)] = save_dict(file)

    map = cv2.imread(str(map_path), -1)

    for frames in range(1, int(globals()['g_frame']) + 1):
        if globals()['g_point'].get(frames) is not None:
            for label in globals()['g_point'].get(frames):
                lonlat = [label[1], label[2]]
                color = getcolor(abs(label[0]))
                cv2.circle(map, (lonlat[0], lonlat[1]), 3, color, -1)

        src = os.path.join(global_output_path, str(frames) + '.jpg')
        cv2.imwrite(src, map)


def save_dict(file):
    frame = 0
    point = dict()
    while True:
        line = file.readline()

        if not line:
            break

        info = line[:-1].split(" ")

        frame = info[0]

        if info[0] in point:
            line = point.get(info[0])
            line.append(list(map(int, info[1:])))
        else:
            point[info[0]] = [list(map(int, info[1:]))]

    file.close()

    return frame, point