import os
import utils
from config import config, DEFECTS
import cv2
# import worker_boundary
# import worker_jiao
import worker_model_0 as worker_model
import numpy as np
import pdb
import time
import datetime
from global_singleton import GolbalSingleton


# import gen_train

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
        self.singleton = GolbalSingleton()
        self.redis_db = self.singleton.conn_redis()
        if self.redis_db.exists('cam0_zangwu_flag') == 0:
            self.redis_db.set('cam0_zangwu_flag', 0)

    def zangwu_detect(self, mesh_bgr, model_type, name=None):
        zangwu_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],  # pts的list，每一个元素是一组缺陷的pts
        }
        if self.redis_db.get('cam0_zangwu_flag')==0:
            if model_type != self.current_model:
                self.current_model = model_type
                self.mesh_setting = self.mesh_settings[model_type]
                self.liner_setting = self.liner_settings[model_type]

            # gray = cv2.cvtColor(mesh_bgr, cv2.COLOR_BGR2GRAY)
            gray = mesh_bgr

            # t_start = time.time()
            sh, sw = gray.shape[:2]
            img_gray = gray[95:sh - 80, 95:sw - 95]

            # 局部自适应二值化
            binary_mean = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 79, 9)

            # 同轴光拍的图片对binary再进行中值滤波，去掉椒盐噪声
            img_binary_blur = cv2.medianBlur(binary_mean, 5)

            sh, sw = img_binary_blur.shape[:2]
            # 左下角
            img_binary_blur[sh - 120:sh, 0:120] = 0
            # 右上角
            img_binary_blur[0:120, sw - 120:sw] = 0
            # 左上角
            img_binary_blur[0:60, 0:60] = 0
            # 右下角
            img_binary_blur[sh - 60:sh, sw - 60:sw] = 0

            # 用连通域面积过滤
            # mask = np.zeros(binary_mean.shape)
            cnts, hierarchy = cv2.findContours(img_binary_blur, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            white_counter = 0
            white_big = 0
            if len(cnts) > 0:
                cnts.sort(key=cv2.contourArea, reverse=True)
                for i in range(0, len(cnts)):
                    # print("contourArea: %s" % cv2.contourArea(cnts[i]))
                    area_contours_circle = cv2.contourArea(cnts[i])
                    if i == 0:
                        white_big = area_contours_circle
                    if area_contours_circle > 200:
                        # 画轮廓：temp为白色幕布，contours为轮廓， -1表示画所有轮廓，颜色：绿色，厚度
                        # cv2.drawContours(temp, cnts[i], -1, (0, 0, 255), 3)
                        # img = cv2.drawContours(img_zangwu_src, cnts, -1, (0, 255, 0), 5)  # img为三通道才能显示轮廓
                        print("contourArea: %s" % cv2.contourArea(cnts[i]))
                        white_counter = white_counter + 1
                    else:
                        break
            else:
                white_counter = 0

            num_p_all_zangwu = np.count_nonzero(img_binary_blur)
            print("num_p_all_zangwu:", num_p_all_zangwu, "white_counter:", white_counter, "white_big:", white_big)

            if (num_p_all_zangwu > 1500) or (white_counter > 3) or (white_big > 800):
                zangwu_dict['defect'] = DEFECTS.ZANGWU
                # cv2.putText(img_zangwu_src, 'ZW', (10, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 0), 3)
            else:
                zangwu_dict['defect'] = DEFECTS.LIANGPIN

        return zangwu_dict

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
        if model_type != self.current_model:
            self.current_model = model_type
            self.mesh_setting = self.mesh_settings[model_type]
            self.liner_setting = self.liner_settings[model_type]
        mesh_bgr = img_dict['image']
        time_now = int(time.time() * 1000)
        now_time = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        print('dangqian time: ', now_time)
        # model_ret = self.model_worker.detect(mesh_bgr, model_type, name)
        # print('model_worker detect time: %s ms' % (int(time.time() * 1000) - time_now))
        # if model_ret['defect'] != DEFECTS.LIANGPIN:
        #     for key, val in model_ret.items():
        #         ret_dict[key] = val
        # 按脏污-模型膜泡顺序进行判断
        time_now1 = int(time.time() * 1000)
        # zangwu_ret = self.zangwu_detect(mesh_bgr, model_type, name)
        print('tuxiangchuli time: %s ms' % (int(time.time() * 1000) - time_now1))
        # if zangwu_ret['defect'] != DEFECTS.LIANGPIN:
        #     for key, val in zangwu_ret.items():
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
        utils.save_by_idx(ret_dict, self.camId, mesh_bgr)
        if ret_dict['defect'] != DEFECTS.LIANGPIN:
            ret_dict['image'] = utils.draw_defect(img_dict['image'], ret_dict)

        print('results', ret_dict['defect'])
        # utils.show_tmp(mesh_bgr)

        return ret_dict


def detect_dir(indir, camId):
    import track_seperate_0
    model_types = ['624']
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
