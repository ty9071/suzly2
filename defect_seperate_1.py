import os
import utils
from config import config, DEFECTS
import cv2
# import worker_boundary
# import worker_jiao
import worker_model_1 as worker_model
import numpy as np
import pdb
import time
import datetime
# import gen_train
from global_singleton import GolbalSingleton


class Worker(object):
    def __init__(self, model_types, mesh_settings, liner_settings, camId):
        self.camId = camId
        self.current_model = None
        self.liner_settings = liner_settings
        self.mesh_settings = mesh_settings
        self.mesh_templates = {}
        # self.boundary_worker= worker_boundary.Worker(mesh_settings, liner_settings, model_types)
        # self.jiao_worker= worker_jiao.Worker(mesh_settings, liner_settings, model_types)
        self.model_worker = worker_model.Worker(mesh_settings, liner_settings, model_types)

        # 0731更新孔相关判断

        self.singleton = GolbalSingleton()
        self.redis_db = self.singleton.conn_redis()
        if self.redis_db.exists('cam1_zangwu_flag') == 0:
            self.redis_db.set('cam1_zangwu_flag', 0)

        if self.redis_db.exists('cam1_detect_circle') == 0:
            self.redis_db.set('cam1_detect_circle', 0)

        if self.redis_db.exists('cam1_maoci_flag') == 0:
            self.redis_db.set('cam1_maoci_flag', 0)

        def zangwu_detect(self, mesh_bgr, model_type, name=None):
            zangwu_dict = {
                'defect': DEFECTS.LIANGPIN,
                'defect_pts_list': [],  # pts的list，每一个元素是一组缺陷的pts
            }
            if self.redis_db.get('cam1_zangwu_flag') == 0:
                if model_type != self.current_model:
                    self.current_model = model_type
                    self.mesh_setting = self.mesh_settings[model_type]
                    self.liner_setting = self.liner_settings[model_type]

                # gray = cv2.cvtColor(mesh_bgr, cv2.COLOR_BGR2GRAY)
                gray = mesh_bgr

                # t_start = time.time()
                sh, sw = gray.shape[:2]
                # img_gray = gray[55:sh - 50, 55:sw - 50]
                img_gray = gray[85:sh - 80, 85:sw - 80]

                # # 均值滤波
                img_blur = cv2.blur(img_gray, (39, 39))
                img_gray = cv2.blur(img_gray, (3, 3))

                img_diff1 = cv2.subtract(img_gray, img_blur)
                img_diff2 = cv2.subtract(img_blur, img_gray)
                ret, img_binary1 = cv2.threshold(img_diff1, 30, 255, cv2.THRESH_BINARY)
                ret, img_binary2 = cv2.threshold(img_diff2, 15, 255, cv2.THRESH_BINARY)
                img_binary2 = cv2.bitwise_or(img_binary1, img_binary2)

                sh, sw = img_binary1.shape[:2]

                # 同轴光拍的图片对binary再进行中值滤波，去掉椒盐噪声
                img_binary_blur = cv2.medianBlur(img_binary2, 5)
                # 四个角减去干扰区域
                # sh, sw = img_binary_blur.shape[:2]
                img_binary_blur[sh - 123:sh, 0:134] = 0
                img_binary_blur[0:130, sw - 125:sw] = 0
                img_binary_blur[0:90, 0:90] = 0
                img_binary_blur[sh - 90:sh, sw - 90:sw] = 0
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (6, 6))
                img_binary_blur = cv2.morphologyEx(img_binary_blur, cv2.MORPH_CLOSE, kernel)

                # 用连通域面积过滤
                mask = np.zeros(img_binary2.shape)
                cnts, hierarchy = cv2.findContours(img_binary_blur, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                for cnt in cnts:
                    cv2.drawContours(mask, [cnt], -1, (255, 255, 255), -1)
                if len(cnts) > 0:
                    cnt_max = sorted(cnts, key=cv2.contourArea, reverse=True)[0]
                    num_p_max_zangwu = cv2.contourArea(cnt_max)
                else:
                    num_p_max_zangwu = 0

                num_p_all_zangwu = np.count_nonzero(mask)

                # print("num_p_all_zangwu:", num_p_all_zangwu, "num_p_max_zangwu:", num_p_max_zangwu, "num_p_all_moque:",
                #       num_p_all_moque)
                # origin 3500/350
                if (num_p_all_zangwu > 13500) or (num_p_max_zangwu > 2080):
                    # zangwu_judge = True
                    zangwu_dict['defect'] = DEFECTS.ZANGWU
                else:
                    # zangwu_judge = False
                    zangwu_dict['defect'] = DEFECTS.LIANGPIN
                # print("zangwu_judge:", zangwu_judge)
                # print("time of total:", time.time() - t_start)
                # t_start = time.time()

                # cv2.namedWindow('img_gray', cv2.WINDOW_NORMAL)
                # cv2.resizeWindow('img_gray', 400, 400)
                # cv2.imshow("img_gray", img_gray)
                # cv2.namedWindow('mask', cv2.WINDOW_NORMAL)
                # cv2.resizeWindow('mask', 400, 400)
                # cv2.imshow("mask", mask)
                # cv2.namedWindow('img_binary_blur', cv2.WINDOW_NORMAL)
                # cv2.resizeWindow('img_binary_blur', 400, 400)
                # cv2.imshow("img_binary_blur", img_binary_blur)
                # # cv2.imwrite("./img_gray.png", img_gray)
                # cv2.waitKey()
            return zangwu_dict

        def detect_circle_step(self, img_circle_src, model_type, name=None):
            ret_dict = {
                'defect': DEFECTS.LIANGPIN,
            }
            if self.redis_db.get('cam1_detect_circle') == 0:
                defect = DEFECTS.LIANGPIN
                # time_now_circle = int(time.time() * 1000)  # 统计运行时间
                img_circle = img_circle_src.copy()
                circle_num_normal = 0  # 统计正常小孔的数目(0无孔1良品2反向）
                white_counter = 0  # 统计白色像素点的数目
                circle_shape = img_circle.shape
                img_circle_height = circle_shape[0]  # height(rows) of image
                img_circle_width = circle_shape[1]  # width(colums) of image
                _, binary_circle = cv2.threshold(img_circle, 240, 255, cv2.THRESH_BINARY)
                # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))  # 定义矩形结构元素
                white_counter = cv2.countNonZero(binary_circle)
                black_counter = img_circle_height * img_circle_width - white_counter
                if white_counter > black_counter:
                    # cv2.putText(img_circle, 'WUMO', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 0), 3)
                    defect = DEFECTS.MOQUE  # 这里应该是无膜
                elif img_circle_height < 710 or img_circle_width < 1100:
                    defect = DEFECTS.MOQUE
                    # cv2.putText(img_circle, 'MOQUE', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 0), 3)
                elif img_circle_height > 900 or img_circle_width > 1300:
                    defect = DEFECTS.MOQUE
                    # cv2.putText(img_circle, 'MOQUE', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 0), 3)
                else:
                    # 右上角区域
                    roi_circle_youshang = binary_circle[50:img_circle_height // 4,
                                          img_circle_width // 6 * 5:img_circle_width - 50]
                    # cv2.imshow('roi_circle_youshang', roi_circle_youshang)
                    white_counter = cv2.countNonZero(roi_circle_youshang)
                    # print('roi_circle_youshang：', white_counter)
                    # if white_counter > 3000:
                    if white_counter > 2400:
                        # 左下角区域
                        roi_circle_zuoxia = binary_circle[img_circle_height // 4 * 3:img_circle_height - 50,
                                            50:img_circle_width // 6]
                        # cv2.imshow('roi_circle_zuoxia', roi_circle_zuoxia)
                        white_counter = cv2.countNonZero(roi_circle_zuoxia)
                        # print('roi_circle_zuoxia：', white_counter)
                        # if white_counter > 3000:
                        if white_counter > 2400:
                            circle_num_normal = 1
                        else:
                            circle_num_normal = 0
                    else:
                        circle_num_normal = 0
                    if circle_num_normal == 0:
                        # 左上角区域
                        roi_circle_zuoshang = binary_circle[50:img_circle_height // 4, 50:img_circle_width // 6]
                        # cv2.imshow('roi_circle_zuoshang', roi_circle_zuoshang)
                        white_counter = cv2.countNonZero(roi_circle_zuoshang)
                        # print('roi_circle_zuoshang：', white_counter)
                        # if white_counter > 3000:
                        if white_counter > 2400:
                            # 右下角区域
                            roi_circle_youxia = binary_circle[img_circle_height // 4 * 3:img_circle_height - 50,
                                                img_circle_width // 6 * 5:img_circle_width - 50]
                            # cv2.imshow('roi_circle_youxia', roi_circle_youxia)
                            white_counter = cv2.countNonZero(roi_circle_youxia)
                            # print('roi_circle_youxia：', white_counter)
                            # if white_counter > 3000:
                            if white_counter > 2400:
                                circle_num_normal = 2
                            else:
                                circle_num_normal = 0
                        else:
                            circle_num_normal = 0
                    if circle_num_normal == 0:
                        defect = DEFECTS.WUKONG
                        # cv2.putText(img_circle, 'WUKONG', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 0), 3)
                    elif circle_num_normal == 1:
                        defect = DEFECTS.LIANGPIN
                        # cv2.putText(img_circle, 'LIANGPIN', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 0), 3)
                    elif circle_num_normal == 2:
                        defect = DEFECTS.FANXIANG
                        # cv2.putText(img_circle, 'FANXIANG', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 0), 3)
                # print('circle detect time: %s ms' % (int(time.time() * 1000) - time_now_circle))
                ret_dict['defect'] = defect
            return ret_dict

        def maoci_detect(self, mesh_bgr, model_type, name=None):
            maoci_dict = {
                'defect': DEFECTS.LIANGPIN,
                'defect_pts_list': [],  # pts的list，每一个元素是一组缺陷的pts
            }
            if self.redis_db.get('cam1_maoci_flag') == 0:
                if model_type != self.current_model:
                    self.current_model = model_type
                    self.mesh_setting = self.mesh_settings[model_type]
                    self.liner_setting = self.liner_settings[model_type]
                defect = DEFECTS.LIANGPIN
                counte_maoci = 0
                circle_num = 0
                img_maoci = mesh_bgr.copy()
                img_maoci_height = img_maoci.shape[0]  # height(rows) of image
                img_maoci_width = img_maoci.shape[1]  # width(colums) of image
                _, binary_circle = cv2.threshold(img_maoci, 200, 255, cv2.THRESH_BINARY)
                roi_circle_right = binary_circle[0:img_maoci_height // 4, img_maoci_width // 4 * 3:img_maoci_width]
                roi_circle_left = binary_circle[img_maoci_height // 4 * 3:img_maoci_height, 0:img_maoci_width // 4]
                # 右上角
                contours_circle, hierarchy_circle = cv2.findContours(roi_circle_right, cv2.RETR_TREE,
                                                                     cv2.CHAIN_APPROX_NONE)
                print('maocilalalala1111111: ')
                for num_cirle in contours_circle:
                    area_contours_circle = cv2.contourArea(num_cirle)
                    # long_contours = cv2.arcLength(num_cirle, True)
                    if area_contours_circle < 2100 or 4300 < area_contours_circle:
                        continue
                    elif 2100 < area_contours_circle < 4300:
                        x_rect, y_rect, w_rect, h_rect = cv2.boundingRect(num_cirle)
                        # print("右长宽高： ", x_rect, y_rect, w_rect, h_rect)
                        if 88 > w_rect > 50 and 88 > h_rect > 50:
                            circle_num = circle_num + 1
                            roi_circle_right = roi_circle_right[y_rect:y_rect + h_rect, x_rect:x_rect + w_rect]
                # 左下角
                contours_circle, hierarchy_circle = cv2.findContours(roi_circle_left, cv2.RETR_TREE,
                                                                     cv2.CHAIN_APPROX_NONE)
                for num_cirle in contours_circle:
                    area_contours_circle = cv2.contourArea(num_cirle)
                    # long_contours = cv2.arcLength(num_cirle, True)
                    if area_contours_circle < 2100 or 4300 < area_contours_circle:
                        continue
                    elif 2100 < area_contours_circle < 4300:
                        x_rect, y_rect, w_rect, h_rect = cv2.boundingRect(num_cirle)
                        # print("左长宽高： ", x_rect, y_rect, w_rect, h_rect)
                        if 88 > w_rect > 50 and 88 > h_rect > 50:
                            circle_num = circle_num + 1
                            roi_circle_left = roi_circle_left[y_rect:y_rect + h_rect, x_rect:x_rect + w_rect]
                gray = roi_circle_left
                for i in range(2):
                    print('idezhi:', i)
                    if i == 0:
                        gray = roi_circle_left
                    else:
                        gray = roi_circle_right
                    # _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
                    if gray.shape[0] > 0:
                        # print('maocilalalala222222: ')
                        # counte_maoci = 0
                        img1 = np.zeros(gray.shape)
                        img2 = np.zeros(gray.shape)
                        contours, hierarchy = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                        # contours_circle, hierarchy = cv2.findContours(gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                        counte_maoci = 0
                        for cnt in contours:
                            # 凸包
                            hull = cv2.convexHull(cnt)
                            # 画轮廓和凸包轮廓，并相减
                            cv2.drawContours(img1, [hull], -1, (255, 255, 255), -1)
                            kernel = np.ones((3, 3), np.uint8)
                            erosion = cv2.erode(img1, kernel, iterations=1)
                            cv2.drawContours(img2, [cnt], -1, (255, 255, 255), -1)
                            # img3 = cv2.bitwise_xor(img1, img2)
                            img3 = cv2.bitwise_and(cv2.bitwise_xor(img1, img2), erosion)
                            img3_height = img3.shape[0]  # height(rows) of image
                            img3_width = img3.shape[1]  # width(colums) of image
                            img3 = img3[2:img3_height - 2, 2:img3_width - 2]
                            counte_maoci = np.count_nonzero(img3)
                            if counte_maoci > 20:
                                break
                    if counte_maoci > 20:
                        defect = DEFECTS.MAOCI
                        break
                    else:
                        # defect = DEFECTS.LIANGPIN
                        continue
                if circle_num < 2:
                    defect = DEFECTS.LIANGPIN
                maoci_dict['defect'] = defect
            return maoci_dict

        def detect(self, img_dict, model_type, name=None):
            ret_dict = {
                'defect': DEFECTS.LIANGPIN,
                'image': img_dict['image'],
                'defect_pts_list': [],  # pts的list，每一个元素是一组缺陷的pts
                'idx': img_dict['idx'],
                'result': DEFECTS.LIANGPIN,  # 要在config中把result的赋值范围设置成0,1,2
                'trig_count': img_dict['trig_count'],
                'batch_count': img_dict['batch_count']
            }
            # print('img1---------',img_dict['image'])
            if model_type != self.current_model:
                self.current_model = model_type
                self.mesh_setting = self.mesh_settings[model_type]
                self.liner_setting = self.liner_settings[model_type]
            # mesh_bgr = img_dict['image']
            # time_now = int(time.time() * 1000)
            now_time = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
            print('dangqianshijian time: ', now_time)
            # 按无膜、反向、无孔、膜缺、划痕的顺序进行判断
            circle_bgr_dect = ret_dict['image']
            mesh_bgr = img_dict['image']
            # print('img----------',img_dict['image'])
            if img_dict['batch_count'] == 0:
                time_now1 = int(time.time() * 1000)
                circle_ret = self.detect_circle_step(circle_bgr_dect, model_type, name)
                print('tuxiangchuli detect time: %s ms' % (int(time.time() * 1000) - time_now1))
                if circle_ret['defect'] != DEFECTS.LIANGPIN:
                    for key, val in circle_ret.items():
                        ret_dict[key] = val
                else:
                    time_now = int(time.time() * 1000)
                    model_ret = self.model_worker.detect(mesh_bgr, model_type, name)
                    print('model_worker detect time: %s ms' % (int(time.time() * 1000) - time_now))
                    if model_ret['defect'] != DEFECTS.LIANGPIN:
                        for key, val in model_ret.items():
                            ret_dict[key] = val
            else:
                maoci_ret = self.maoci_detect(mesh_bgr, model_type, name)
                if maoci_ret['defect'] != DEFECTS.LIANGPIN:
                    for key, val in maoci_ret.items():
                        ret_dict[key] = val
                # else:
                #     zangwu_ret = self.zangwu_detect(mesh_bgr, model_type, name)
                #     # print('tuxiangchuli time: %s ms' % (int(time.time() * 1000) - time_now1))
                #     if zangwu_ret['defect'] != DEFECTS.LIANGPIN:
                #         for key, val in zangwu_ret.items():
                #             ret_dict[key] = val

            # model_ret = self.model_worker.detect(mesh_bgr, model_type, name)
            # print('model_worker detect time: %s ms' % (int(time.time() * 1000) - time_now))
            # if model_ret['defect'] != DEFECTS.LIANGPIN:
            #     for key, val in model_ret.items():
            #         ret_dict[key] = val

            # # 边缘相关检测
            # bound_ret = self.boundary_worker.detect(mesh_bgr, model_type)
            # if bound_ret['defect'] != DEFECTS.LIANGPIN:
            #     for key, val in bound_ret.items():
            #         ret_dict[key] = val
            #     return ret_dict
            # mesh_bgr = bound_ret['mesh_bgr']
            # mesh_bin = bound_ret['mesh_bin']
            # mesh_outter = bound_ret['mesh_outter']
            # if ret_dict['defect'] == DEFECTS.LIANGPIN:
            #     # 胶相关检测
            #     jiao_ret = self.jiao_worker.detect(mesh_bgr, mesh_outter, mesh_bin, model_type)
            #     if jiao_ret['defect'] != DEFECTS.LIANGPIN:
            #         for key, val in jiao_ret.items():
            #             ret_dict[key] = val
            #         return ret_dict
            # if ret_dict['defect'] == DEFECTS.LIANGPIN:
            #     model_ret = self.model_worker.detect(mesh_bgr, mesh_outter, mesh_bin, model_type, name)
            #     if model_ret['defect'] != DEFECTS.LIANGPIN:
            #         for key, val in model_ret.items():
            #             ret_dict[key] = val
            #         return ret_dict
            # utils.save_by_idx(ret_dict, self.camId, mesh_bgr)
            # if ret_dict['defect'] != DEFECTS.LIANGPIN:
            #     ret_dict['image'] = utils.draw_defect(img_dict['image'], ret_dict)

            # 0709加入小孔相关判断
            # time_now_circle = int(time.time() * 1000)
            # img_circle = ret_dict['image'].copy()
            # # gray_circle = cv2.cvtColor(img_circle, cv2.COLOR_BGR2GRAY)
            # _, binary_circle = cv2.threshold(img_circle, 200, 255, cv2.THRESH_BINARY)
            # contours_circle, hierarchy_circle = cv2.findContours(binary_circle, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            # for num_cirle in contours_circle:
            #     area_contours_circle = cv2.contourArea(num_cirle)
            #     long_contours = cv2.arcLength(num_cirle, True)
            #     if area_contours_circle > 4000 and area_contours_circle < 6000:
            #         # print('long_contours', long_contours)
            #         if long_contours > 200 and long_contours < 380:
            #             # 圆的直径在85左右
            #             # print('area_contours_circle', area_contours_circle)
            #             x_rect, y_rect, w_rect, h_rect = cv2.boundingRect(num_cirle)
            #             if w_rect > 75 and h_rect > 75:
            #                 # print('w_rect', w_rect)
            #                 # print('h_rect', h_rect)
            #                 (x_circle, y_circle), radius_circle = cv2.minEnclosingCircle(num_cirle)
            #                 center = (int(x_circle), int(y_circle))
            #                 radius = int(radius_circle)
            #                 print('radius_wai', radius_circle)
            #                 cv2.circle(ret_dict['image'], center, radius, (0, 0, 0), 3)
            # print('circle detect time: %s ms' % (int(time.time() * 1000) - time_now_circle))
            # ret_dict['image'] = detect_circle(ret_dict['image'])
            # 到这里小孔相关判断结束

            utils.save_by_idx(ret_dict, self.camId, mesh_bgr)
            if ret_dict['defect'] != DEFECTS.LIANGPIN:
                ret_dict['image'] = utils.draw_defect(img_dict['image'], ret_dict)
            print('results', ret_dict['defect'])
            # utils.show_tmp(mesh_bgr)

            return ret_dict

        # 0709加入小孔相关判断

    def detect_circle(img_circle):
        time_now_circle = int(time.time() * 1000)
        img_circle = img_circle.copy()
        # gray_circle = cv2.cvtColor(img_circle, cv2.COLOR_BGR2GRAY)
        _, binary_circle = cv2.threshold(img_circle, 200, 255, cv2.THRESH_BINARY)
        contours_circle, hierarchy_circle = cv2.findContours(binary_circle, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for num_cirle in contours_circle:
            area_contours_circle = cv2.contourArea(num_cirle)
            long_contours = cv2.arcLength(num_cirle, True)
            if area_contours_circle > 4000 and area_contours_circle < 6000:
                # print('long_contours', long_contours)
                if long_contours > 200 and long_contours < 380:
                    # 圆的直径在85左右
                    # print('area_contours_circle', area_contours_circle)
                    x_rect, y_rect, w_rect, h_rect = cv2.boundingRect(num_cirle)
                    if w_rect > 75 and h_rect > 75:
                        # print('w_rect', w_rect)
                        # print('h_rect', h_rect)
                        (x_circle, y_circle), radius_circle = cv2.minEnclosingCircle(num_cirle)
                        center = (int(x_circle), int(y_circle))
                        radius = int(radius_circle)
                        print('radius_wai', radius_circle)
                        cv2.circle(img_circle, center, radius, (0, 0, 0), 3)
        print('circle detect time: %s ms' % (int(time.time() * 1000) - time_now_circle))
        return img_circle
        # 到这里小孔相关判断结束

    def detect_dir(indir, camId):
        import track_seperate_0
        model_types = ['707']
        tracker = track_seperate_0.Tracker(model_types)
        model_type = config['model_type']
        mesh_settings = utils.load_mesh_settings(model_types)
        liner_settings = utils.load_liner_settings(model_types)
        worker = Worker(model_types, mesh_settings, liner_settings, camId)
        start = False
        count = 0
        for name in os.listdir(indir):
            inname = os.path.join(indir, name)
            if not os.path.isfile(inname):
                continue
            print(inname)
            #        if '432.jpg' == name:
            #            start = True
            #        if start == False:
            #            continue
            #         if '2020_06_03_17_27_33.jpg' != name:
            #           continue
            img = cv2.imread(inname)
            frame_dict = {
                'image': img,
            }
            track_ret = tracker.track(frame_dict, model_type)
            for obj in track_ret['objs']:
                print('idx', obj['idx'], '^^^^^^^^^^^^^^^^^^^^^^^^^^^')
                #            if not (obj['row_idx'] == 304 and obj['side'] == 0):
                #                 continue
                # if obj['side'] == 0:
                #     continue
                ret_dict = worker.detect(obj, model_type, name)
                print('defect,result', ret_dict['idx'], ret_dict['defect'])

    if __name__ == '__main__':
        camId = 0
        #    indir = '../data/local_buf/0520/'
        #    indir = '../record/0601/0/pre/'
        #     indir = '../record/0601/0/used/'
        # indir = 'D:/projects/lingyi/data/ly_live/0603/2000_1/images/'
        # indir = 'D:/projects/lingyi/data/ly_live/0521/0521/imgs/'
        indir = '../data/707/707loubai/'
        detect_dir(indir, camId)
