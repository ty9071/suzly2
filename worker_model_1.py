import cv2
import os
import pdb
import image_process
import numpy as np
import utils
from config import DEFECTS
import importlib
import copy
import time
import math
from config import config
import utils
import gen_train
from global_singleton import GolbalSingleton
if config['use_torch'] == True:
    import obj_model_1


class Worker:
    def __init__(self, mesh_settings, liner_settings, model_types):
        self.model_type = None
        self.mesh_setting = None
        self.liner_setting = None
        self.liner_settings = liner_settings
        self.mesh_settings = mesh_settings
        self.mesh_templates = {}
        if config['use_torch'] == True:
            self.obj_worker = obj_model_1.ModelObj(thresh=0.4)

        self.singleton = GolbalSingleton()
        self.redis_db = self.singleton.conn_redis()
        if self.redis_db.exists('cam1_maoci_flag') == 0:
            self.redis_db.set('cam1_maoci_flag', 0)

        if self.redis_db.exists('cam1_moque_flag') == 0:
            self.redis_db.set('cam1_moque_flag', 0)

        if self.redis_db.exists('cam1_mohuashang_flag') == 0:
            self.redis_db.set('cam1_mohuashang_flag', 0)

        if self.redis_db.exists('cam1_moyashang_flag') == 0:
            self.redis_db.set('cam1_moyashang_flag', 0)

    def crop_rois(self, mesh_bgr, mesh_outter):
        '''
        截取小图
        :param mesh_bgr:
        :param mesh_rect:
        :return:
        '''
        h, w = mesh_outter.shape
        sum_w = np.sum(mesh_outter, axis=0)
        idx_w = np.wGGhere(sum_w > 0)
        min_w, max_w = np.min(idx_w), np.max(idx_w)
        sum_h = np.sum(mesh_outter, axis=1)
        idx_h = np.where(sum_h > 0)
        min_h, max_h = np.min(idx_h), np.max(idx_h)
        mid_w = int((min_w + max_w) / 2)
        mid_h = int((min_h + max_h) / 2)
        pad_bound = 50
        pad_inter = 50
        pts_list = [
            (max(0, min_w - pad_bound), max(0, min_h - pad_bound), mid_w + pad_inter, mid_h + pad_inter),
            (mid_w - pad_inter, max(0, min_h - pad_bound), min(w, max_w + pad_bound), mid_h + pad_inter),
            (max(0, min_w - pad_bound), mid_h - pad_inter, mid_w + pad_inter, min(h, max_h + pad_bound)),
            (mid_w - pad_inter, max(0, min_h + pad_bound), min(w, max_w + pad_bound), min(h, max_h + pad_bound)),
        ]
        objs = []
        for pts in pts_list:
            image = mesh_bgr[pts[1]:pts[3], pts[0]:pts[2]]
            obj_dict = {
                'image': image,
                'pts': pts,
            }
            objs.append(obj_dict)
            # cv2.imshow('roi', image)
            # cv2.waitKey(0)
        return objs

    def detect(self, mesh_bgr, model_type, name=None):
        '''
        :param mesh_bgr:
        :param model_type:
        :return:
        '''
        ret_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
        }
        #        objs = self.crop_rois(mesh_bgr, mesh_outter)
        #        if config['OUTPUT_TRAIN'] == True:
        #            gen_train.detect(mesh_bgr, objs, name)
        #        for obj in objs:
        #            if config['use_torch'] == True:
        #                pts_list = self.obj_worker.detect(obj['image'])
        defect = DEFECTS.LIANGPIN
        if config['use_torch'] == True:
            model_dict = self.obj_worker.detect(mesh_bgr)
            all_lab_list = model_dict['lab_list']
            all_pts_list = model_dict['pts_list']
            # 太小的异物先不算
            lab_list = []
            pts_list = []
            # 长度2mm-3mm的划痕数量
            huashang_num_middle = 0
            # 长度3mm以上的划痕数量
            huashang_num_long = 0
            # 面积0.02-0.08的压伤数量
            yashang_num_middle = 0
            # 面积0.08以上的压伤数量
            yashang_num_large = 0
            # 面积0.08以上的膜缺数量
            moque_num_large = 0
            mozhou_flag = 0
            maici_flag = 0
            for i, lab in enumerate(all_lab_list):
                pts = all_pts_list[i]
                # if 1 == lab:
                #     length = np.linalg.norm(np.array(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0]))
                #     if length < 315:
                #         continue
                #     elif (length >= 315) and (length < 475):
                #         huashang_num_middle = huashang_num_middle + 1
                #     else:
                #         huashang_num_long = huashang_num_long + 1
                # elif 2 == lab:
                #     area = (pts[1][1] - pts[0][1]) * (pts[1][0] - pts[0][0])
                #     if area < 500:
                #         continue
                #     elif (area >= 500) and (area < 2000):
                #         yashang_num_middle = yashang_num_middle + 1
                #     else:
                #         yashang_num_large = yashang_num_large + 1
                # elif 3 == lab:
                #     area = (pts[1][1] - pts[0][1]) * (pts[1][0] - pts[0][0])
                #     if area < 2000:
                #         continue
                #     else:
                #         moque_num_large = moque_num_large + 1
                if 1 == lab:
                    length = np.linalg.norm(np.array(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0]))
                    if length < 200:
                        continue
                    elif (length >= 200) and (length < 475):
                        huashang_num_middle = huashang_num_middle + 1
                    else:
                        huashang_num_long = huashang_num_long + 1
                elif 2 == lab:
                    area = (pts[1][1] - pts[0][1]) * (pts[1][0] - pts[0][0])
                    if area < 1600:
                        continue
                    else:
                        moque_num_large = moque_num_large + 1
                elif 3 == lab:
                    area = (pts[1][1] - pts[0][1]) * (pts[1][0] - pts[0][0])
                    if area < 500:
                        continue
                    elif (area >= 500) and (area < 2000):
                        yashang_num_middle = yashang_num_middle + 1
                    else:
                        yashang_num_large = yashang_num_large + 1
                elif 4 == lab:
                    mozhou_flag = 1
                elif 5 == lab:
                    length = np.linalg.norm(np.array(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0]))
                    if length < 8:
                        continue
                    else:
                        maici_flag = 1
                    # maici_flag = 1
                lab_list.append(lab)
                pts_list.append(pts)
            used_lab = -1
            if maici_flag == 1:
                if not self.redis_db.set('cam1_maoci_flag')==0:
                    defect = DEFECTS.MAOCI
                used_lab = 5
            if mozhou_flag == 1:
                if not self.redis_db.set('cam1_moque_flag')==0:
                    defect = DEFECTS.MOQUE
                used_lab = 4
            elif (huashang_num_middle > 1) or (huashang_num_long > 0):
                if not self.redis_db.set('cam1_mohuashang_flag')==0:
                    defect = DEFECTS.MOHUASHANG
                used_lab = 1
            elif moque_num_large > 0:
                if not self.redis_db.set('cam1_moque_flag')==0:
                    defect = DEFECTS.MOQUE
                used_lab = 2
            elif (yashang_num_middle > 1) or (yashang_num_large > 0):
                if not self.redis_db.set('cam1_moyashang_flag')==0:
                    defect = DEFECTS.MOYASHANG
                used_lab = 3
            if used_lab > 0:
                for i in range(len(lab_list)):
                    if lab_list[i] == used_lab:
                        ret_dict['defect_pts_list'].append(pts_list[i])
        ret_dict['defect'] = defect
        return ret_dict


def detect_dir(indir):
    model_types = ['624']
    model_type = config['model_type']
    mesh_settings = utils.load_mesh_settings(model_types)
    liner_settings = utils.load_liner_settings(model_types)
    worker = Worker(mesh_settings, liner_settings, model_types)
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
        worker.detect(img, None, None, None)


if __name__ == '__main__':
    indir = '../../obj_detect/data/707/0623/20200623/images/'
    detect_dir(indir)

