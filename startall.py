# FastMOT + BEV All-in-One Script
# Usage : python3 startall.py -i ./input -o ./output -m ./input/edu_map.png
# 필수 옵션 : -i, -o, -m
# -i (--input-uri) : Input Video 들어있는 경로
# -o (--output-uri) : Output 폴더 경로
# -m (--map-uri) : BEV에서 사용할 Map Image File 경로
# -c (--config) : FastMOT Custom Config File 설정 (기본은 cfg/mot.json)
# -s (--show) : FastMOT 동작 중 처리되는 영상 보기
# -sm (--skip-mot) : FastMOT 생략 (이미 FastMOT Output Video가 있는 경우에 사용)
# -sp (--skip-point) : Point 선택 생략 (이미 BEV Point 선택 텍스트 파일 (temp/points_map1.txt) 있는 경우에 사용)

import argparse
import json
import logging
import os
import shutil
import traceback
import mimetypes
import fastmot
import cv2
from fastmot.utils import ConfigDecoder, Profiler
from pathlib import Path
from types import SimpleNamespace

from BEV import mouse_point
from BEV import BEV
from BEV import output_video
from BEV import global_BEV
from BEV import global_output_video

#from DTW import global_id_mapping


def start():
    #### Arguments Setting ####
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    optional = parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    group = parser.add_mutually_exclusive_group()
    required.add_argument('-i', '--input-uri', metavar="URI", required=True,
                          help='Input Video Folder',
                          default=Path(__file__).parent / 'input')
    required.add_argument('-o', '--output-uri', metavar="URI",
                          help='Output File (Video, Text, Frame) Folder',
                          default=Path(__file__).parent / 'output')
    required.add_argument('-m', '--map-uri', metavar="URI",
                          help='Map Image File URI')
    optional.add_argument('-c', '--config', metavar="FILE",
                          default=Path(__file__).parent / 'cfg' / 'mot.json',
                          help='path to JSON configuration file')
    optional.add_argument('-s', '--show', action='store_true', help='show visualizations')
    optional.add_argument('-sm', '--skip-mot', action='store_true', help='Skip FastMOT')
    optional.add_argument('-sp', '--skip-point', action='store_true', help='Skip Select Point')
    group.add_argument('-q', '--quiet', action='store_true', help='reduce output verbosity')
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser._action_groups.append(optional)
    args = parser.parse_args()

    if args.skip_mot and args.show:
        raise parser.error('argument -s/--show: not allowed with argument -sm/--skip-mot')

    # set up logging
    logging.basicConfig(format='%(asctime)s [%(levelname)8s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger("INC_BEV_FastMOT")
    if args.quiet:
        logger.setLevel(logging.WARNING)
    elif args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # load config file
    with open(args.config) as cfg_file:
        config = json.load(cfg_file, cls=ConfigDecoder, object_hook=lambda d: SimpleNamespace(**d))

    # ####################### Original ##################################

    # print(Path(args.output_uri))
    # # MOT Skip 아니면 Output 폴더 비우기
    # if not args.skip_mot:
    #     if os.path.isdir(Path(args.output_uri)):
    #         shutil.rmtree(Path(args.output_uri))
    #
    # # Input 경로에 있는 모든 파일 읽기
    # videolist = os.listdir(args.input_uri)
    #
    # # Temp 폴더 생성
    # Path(Path(__file__).parent / 'temp').mkdir(parents=True, exist_ok=True)
    #
    # # Output 폴더 생성
    # Path(args.output_uri).mkdir(parents=True, exist_ok=True)
    #
    # # MOT Skip 아니면 Output 폴더 비우기
    # if not args.skip_mot:
    #     if os.path.isdir(Path(args.output_uri)):
    #         shutil.rmtree(Path(args.output_uri))
    #
    # # 모든 File 읽기 위해 Loop
    # for videofile in videolist:
    #     # 이름과 확장자 분리
    #     name, ext = os.path.splitext(videofile)
    #
    #     filemime = mimetypes.guess_type(videofile)[0]
    #
    #     # MIME Type이 Video인 경우
    #     if filemime is not None and filemime.find('video') is not -1:
    #         # MOT 작업을 Skip하지 않은 경우
    #         if not args.skip_mot:
    #             # FastMOT 실행
    #             stream = fastmot.VideoIO(config.resize_to,
    #                                      args.input_uri + videofile,
    #                                      args.output_uri + "/mot_{}".format(videofile),
    #                                      **vars(config.stream_cfg))
    #             mot = fastmot.MOT(config.resize_to, **vars(config.mot_cfg), draw=True)
    #             mot.reset(stream.cap_dt)
    #
    #             txt = open(args.output_uri + '/' + name + '.txt', 'w')
    #
    #             Path(args.output_uri + '/frame/' + name).mkdir(parents=True, exist_ok=True)
    #             framecount = 0
    #
    #             if args.show:
    #                 cv2.namedWindow('Video', cv2.WINDOW_AUTOSIZE)
    #
    #             logger.info('Starting video capture... ({})'.format(videofile))
    #             stream.start_capture()
    #
    #             try:
    #                 with Profiler('app') as prof:
    #                     while not args.show or cv2.getWindowProperty('Video', 0) >= 0:
    #                         frame = stream.read()
    #                         if frame is None:
    #                             break
    #
    #                         mot.step(frame)
    #
    #                         for track in mot.visible_tracks():
    #                             tl = track.tlbr[:2] / config.resize_to * stream.resolution
    #                             br = track.tlbr[2:] / config.resize_to * stream.resolution
    #                             w, h = br - tl + 1
    #
    #                             # New Text Format
    #                             txt.write(f'{mot.frame_count} {track.trk_id} {int(tl[0] + w / 2)} {int((tl[1] + h) - 10)}\n')
    #
    #                         if args.show:
    #                             cv2.imshow('Video', frame)
    #                             if cv2.waitKey(1) & 0xFF == 27:
    #                                 break
    #
    #                         cv2.imwrite("{}/{}.jpg".format(Path(args.output_uri + '/frame/' + name), framecount), frame)
    #                         framecount += 1
    #                         stream.write(frame)
    #             finally:
    #                 # # clean up resources
    #                 # if txt is not None:
    #                 #     txt.close()
    #
    #                 stream.release()
    #                 cv2.destroyAllWindows()
    #
    #                 avg_fps = round(mot.frame_count / prof.duration)
    #                 logger.info('Average FPS: %d', avg_fps)
    #                 mot.print_timing_info()
    #         else:
    #             logger.info('Skip MOT...')
    #
    # try:
    #     # Point 지정 시작
    #     '''
    #     pixel : 실제 공간
    #     lonloat : 도면 공간
    #     실제 mapping 되는 곳에 좌표를 입력 @@@.py 사용
    #     오른쪽 위, 왼쪽 위, 왼쪽 아래, 오른쪽 아래 순서
    #     '''
    #
    #     # if not args.skip_point:
    #     #     logger.info('Waiting Select Points...')
    #     #     mouse_point.start(Path(__file__).parent / 'temp/points_map1.txt', Path(args.output_uri + '/frame/'), args.map_uri)
    #
    #     # BEV Start
    #     logger.info('Start BEV...')
    #
    #     file_exist = False
    #     for file in os.listdir(Path(args.output_uri)):
    #         if file.endswith(".txt"):
    #             file_exist = True
    #
    #     bev_success = False
    #     if file_exist:
    #         bev_success = BEV.start(Path(args.output_uri), Path(args.map_uri).absolute())
    #     else:
    #         logger.info('Not exist MOT result file! Stop BEV process.')
    #
    #     # # Write BEV Video
    #     # if bev_success:
    #     #     logger.info('Write BEV Video...')
    #     #     output_video.start(Path(args.output_uri).absolute())
    #     # else:
    #     #     logger.info('Stop Write BEV Video process.')
    #
    #     # # Global mapping start
    #     # is_exist_global_list = False
    #     # if bev_success:
    #     #     logger.info('Start global mapping...')
    #     #     is_exist_global_list = global_id_mapping.start(Path(args.output_uri))
    #     # else:
    #     #     logger.info('Stop global mapping process.')
    #     #
    #     # # Write Global BEV Video
    #     # if is_exist_global_list:
    #     #     logger.info('Create global mapping frames...')
    #     #     global_BEV.start(Path(args.output_uri), Path(args.map_uri).absolute())
    #     #
    #     #     logger.info('Write global BEV Video...')
    #     #     global_output_video.start(Path(args.output_uri))
    #     # else:
    #     #     logger.info('Stop Write Global BEV Video process.')
    #
    #     logger.info('Finished!')
    #
    # except:
    #     logger.error(traceback.format_exc())

    # ####################### For Test ##################################
    test_case = 20
    skip = 'skip10'
    out_path = os.path.join(args.output_uri, skip)

    for i in range(1, test_case + 1):
        inPath = os.path.join(args.input_uri, str(i)) + '/'
        outPath = os.path.join(out_path, str(i)) + '/'

        print(Path(outPath))

        # Input 경로에 있는 모든 파일 읽기
        videolist = os.listdir(inPath)

        # Temp 폴더 생성
        Path(Path(__file__).parent / 'temp').mkdir(parents=True, exist_ok=True)

        # Output 폴더 생성
        Path(args.output_uri).mkdir(parents=True, exist_ok=True)

        # MOT Skip 아니면 Output 폴더 비우기
        if not args.skip_mot:
            if os.path.isdir(Path(outPath)):
                shutil.rmtree(Path(outPath))

        # 모든 File 읽기 위해 Loop
        for videofile in videolist:
            # 이름과 확장자 분리
            name, ext = os.path.splitext(videofile)

            filemime = mimetypes.guess_type(videofile)[0]

            # MIME Type이 Video인 경우
            if filemime is not None and filemime.find('video') is not -1:
                # MOT 작업을 Skip하지 않은 경우
                if not args.skip_mot:
                    # FastMOT 실행
                    stream = fastmot.VideoIO(config.resize_to,
                                             inPath + videofile,
                                             outPath + "/mot_{}".format(videofile),
                                             **vars(config.stream_cfg))
                    mot = fastmot.MOT(config.resize_to, **vars(config.mot_cfg), draw=True)
                    mot.reset(stream.cap_dt)

                    txt = open(outPath + '/' + name + '.txt', 'w')

                    Path(outPath + '/frame/' + name).mkdir(parents=True, exist_ok=True)
                    framecount = 0

                    if args.show:
                        cv2.namedWindow('Video', cv2.WINDOW_AUTOSIZE)

                    logger.info('Starting video capture... ({})'.format(videofile))
                    stream.start_capture()

                    try:
                        with Profiler('app') as prof:
                            while not args.show or cv2.getWindowProperty('Video', 0) >= 0:
                                frame = stream.read()
                                if frame is None:
                                    break

                                mot.step(frame)

                                for track in mot.visible_tracks():
                                    tl = track.tlbr[:2] / config.resize_to * stream.resolution
                                    br = track.tlbr[2:] / config.resize_to * stream.resolution
                                    w, h = br - tl + 1

                                    # New Text Format
                                    txt.write(
                                        f'{mot.frame_count} {track.trk_id} {int(tl[0] + w / 2)} {int((tl[1] + h) - 10)}\n')

                                if args.show:
                                    cv2.imshow('Video', frame)
                                    if cv2.waitKey(1) & 0xFF == 27:
                                        break

                                cv2.imwrite("{}/{}.jpg".format(Path(outPath + '/frame/' + name), framecount),
                                            frame)
                                framecount += 1
                                stream.write(frame)
                    finally:
                        # # clean up resources
                        # if txt is not None:
                        #     txt.close()

                        stream.release()
                        cv2.destroyAllWindows()

                        avg_fps = round(mot.frame_count / prof.duration)
                        logger.info('Average FPS: %d', avg_fps)
                        mot.print_timing_info()
                else:
                    logger.info('Skip MOT...')

        try:
            # Point 지정 시작
            '''
            pixel : 실제 공간
            lonloat : 도면 공간
            실제 mapping 되는 곳에 좌표를 입력 @@@.py 사용
            오른쪽 위, 왼쪽 위, 왼쪽 아래, 오른쪽 아래 순서
            '''

            # if not args.skip_point:
            #     logger.info('Waiting Select Points...')
            #     mouse_point.start(Path(__file__).parent / 'temp/points_map1.txt', Path(args.output_uri + '/frame/'), args.map_uri)

            # BEV Start
            logger.info('Start BEV...')

            file_exist = False
            for file in os.listdir(Path(outPath)):
                if file.endswith(".txt"):
                    file_exist = True

            bev_success = False
            if file_exist:
                bev_success = BEV.start(Path(outPath), Path(args.map_uri).absolute())
            else:
                logger.info('Not exist MOT result file! Stop BEV process.')

            # # Write BEV Video
            # if bev_success:
            #     logger.info('Write BEV Video...')
            #     output_video.start(Path(args.output_uri).absolute())
            # else:
            #     logger.info('Stop Write BEV Video process.')

            # # Global mapping start
            # is_exist_global_list = False
            # if bev_success:
            #     logger.info('Start global mapping...')
            #     is_exist_global_list = global_id_mapping.start(Path(args.output_uri))
            # else:
            #     logger.info('Stop global mapping process.')
            #
            # # Write Global BEV Video
            # if is_exist_global_list:
            #     logger.info('Create global mapping frames...')
            #     global_BEV.start(Path(args.output_uri), Path(args.map_uri).absolute())
            #
            #     logger.info('Write global BEV Video...')
            #     global_output_video.start(Path(args.output_uri))
            # else:
            #     logger.info('Stop Write Global BEV Video process.')

            logger.info('Finished!')

        except:
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    start()

