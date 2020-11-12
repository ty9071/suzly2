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

if config['use_torch'] == True:
    import obj_model_0


class Worker:
    def __init__(self, mesh_settings, liner_settings, model_types):
        self.model_type = None
        self.mesh_setting = None
        self.liner_setting = None
        self.liner_settings = liner_settings
        self.mesh_settings = mesh_settings
        self.mesh_templates = {}
        if config['use_torch'] == True:
            self.obj_worker = obj_model_0.ModelObj(thresh=0.4)

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
            for i, lab in enumerate(all_lab_list):
                pts = all_pts_list[i]
                # if 2 == lab:
                #     max_edge = max(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0])
                #     if max_edge < 15:
                #         continue
                lab_list.append(lab)
                pts_list.append(pts)
            used_lab = -1
            if 1 in lab_list:
                defect = DEFECTS.MOPAO
                used_lab = 1
            if used_lab > 0:
                for i in range(len(lab_list)):
                    if lab_list[i] == used_lab:
                        ret_dict['defect_pts_list'].append(pts_list[i])
        ret_dict['defect'] = defect
        return ret_dict


def detect_dir(indir):
    model_types = ['6244']
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

