import BEV
import cv2
import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import DB.database as Database
##############################################################################

# Todo: bev import error확인
def start(output_path, map_path, group_id):

    global_output_path = os.path.join(output_path, 'global_map_frame')

    if not os.path.exists(global_output_path):
        os.makedirs(global_output_path)
    else:
        shutil.rmtree(global_output_path)
        os.makedirs(global_output_path)

    # ==============  Global ID BEV result  ===================
    # Get Global info in DB table
    global_info_list = Database.getGlobalTrackingDatas(group_id)
    globals()['g_frame'], globals()['g_point'] = BEV.save_dict(global_info_list)

    map = cv2.imread(str(map_path), -1)

    for frames in range(1, int(globals()['g_frame']) + 1):
        if globals()['g_point'].get(frames) is not None:
            for label in globals()['g_point'].get(frames):
                lonlat = [label[1], label[2]]
                color = BEV.getcolor(abs(label[0]))
                cv2.circle(map, (lonlat[0], lonlat[1]), 3, color, -1)

        src = os.path.join(global_output_path, str(frames) + '.jpg')
        cv2.imwrite(src, map)

