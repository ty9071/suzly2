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
import align_seperate_0


class Worker:
    def __init__(self, mesh_settings, liner_settings, model_types):
        self.model_type = None
        self.mesh_setting = None
        self.liner_setting = None
        self.liner_settings = liner_settings
        self.mesh_settings = mesh_settings
        self.mesh_templates = {}
        self.load_mesh_templates(model_types)
        self.alinger = align_seperate_0.Aligner(config['mesh_template'], config['rough_template'])

    def load_mesh_templates(self, model_types):
        '''
        读取
        :param model_types:
        :return:
        '''
        indir = config['template_dir']
        for model_type in model_types:
            self.mesh_templates[model_type] = {}
            inname = os.path.join(indir, model_type + '.png')
            img = cv2.imread(inname, 0)
            _, img = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)
            self.mesh_templates[model_type] = img

    def bianxing(self, mesh_outter, templ_pos):
        '''
        检测变形，4边，4个角分别检测
        :param mesh_outter:
        :param templ_pos:
        :return:
        '''
        ret_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
        }
        templ_bin = self.mesh_templates[self.model_type]
        # pdb.set_trace()
        th, tw = templ_bin.shape
        mesh_roi = mesh_outter[templ_pos[1]:templ_pos[1] + th, templ_pos[0]:templ_pos[0] + tw]
        inter = cv2.bitwise_and(mesh_roi, templ_bin)
        mesh_extra = mesh_roi - inter
        templ_extra = ((templ_bin - inter).astype(np.int32) / 2).astype(np.uint8)
        mesh_area = mesh_extra + templ_extra

        cv2.imshow('inter', mesh_area)
        cv2.waitKey(0)
        '''
        下来算mesh_area边的厚度就行
        注意4边和4角分开始UAN
        变形一般有3种
        1. 整体弯了，一边的厚度比较大
        2. 一部分多出去或者缺了，一边厚度比较大
        3. 两边不一样粗，测下滑动的最粗和最细的边（比较长的mesh会有，707不一定）
        '''
        return ret_dict

    def detect(self, mesh_bgr, model_type):
        '''
        mesh_bgr: 一截mesh区域的bgr图像
        '''
        ret_dict = {
            'valid': True,
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
            'mesh_outter': None,
            'mesh_bgr': None,
            'mesh_bin': None,
            'msg': '',
        }
        if model_type != self.model_type:
            self.model_type = model_type
            self.mesh_setting = self.mesh_settings[model_type]
            self.liner_setting = self.liner_settings[model_type]
        # 旋转90度，现有算法钢网是平着的
        cv2.imshow('imgorg', mesh_bgr)
        mesh_bgr = cv2.transpose(mesh_bgr)
        gray = cv2.cvtColor(mesh_bgr, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, self.mesh_setting['bin_thresh'], 255, cv2.THRESH_BINARY_INV)
        _, binary = cv2.threshold(gray, self.mesh_setting['bin_thresh'], 255, cv2.THRESH_BINARY_INV)
        cv2.imshow('imgqqq', mesh_bgr)
        cv2.imshow('imgbin', binary)
        cv2.waitKey(0)
        # 矫正
        ret = self.alinger.align(mesh_bgr, binary, self.mesh_templates[model_type])
        if ret['defect'] != DEFECTS.LIANGPIN:
            for key, val in ret.items():
                ret_dict[key] = val
            return ret_dict
        mesh_bgr = ret['mesh_bgr']
        mesh_bin = ret['mesh_bin']
        mesh_outter = ret['mesh_outter']
        templ_pos = ret['templ_pos']
        # 变形
        ret = self.bianxing(mesh_outter, templ_pos)
        if ret['defect'] != DEFECTS.LIANGPIN:
            for key, val in ret.items():
                ret_dict[key] = val
            return ret_dict
        ret_dict['mesh_outter'] = mesh_outter
        ret_dict['mesh_bgr'] = mesh_bgr
        ret_dict['mesh_bin'] = mesh_bin
        return ret_dict
