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


class Worker:
    def __init__(self, mesh_settings, liner_settings, model_types):
        self.model_type = None
        self.mesh_setting = None
        self.liner_setting = None
        self.liner_settings = liner_settings
        self.mesh_settings = mesh_settings
        self.mesh_templates = {}

    def crop_jiaos(self, mesh_bgr, mesh_bin):
        '''
        截出胶的区域,
        TODO：可能会需要根据模板位置扣
        :param mesh_bin:
        :return:
        '''
        ret_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
            'jiao_list': [],
        }
        sum_w = np.sum(mesh_bin, axis=0) / 255
        idx_w = np.where(sum_w > 20)
        start_w, end_w = np.min(idx_w), np.max(idx_w)
        sum_h = np.sum(mesh_bin, axis=1) / 255
        idx_h = np.where(sum_h > 20)
        start_h, end_h = np.min(idx_h), np.max(idx_h)
        mesh_hight = end_h - start_h
        mesh_width = int(end_w - start_w)
        # cv2.imshow('minbin', mesh_bin)
        # cv2.waitKey(0)
        jiao_thresh = 0.90  # 胶比网的位置像素多的比例
        radis = self.mesh_setting['radis']
        # 考虑到胶的位置可能有洞，分开两边找
        left = mesh_bin[:, start_w+radis:start_w+int(mesh_width/2)]
        # cv2.imshow('left', left)
        # cv2.waitKey(0)
        # TODO: 胶有问题的时候可能一个阈值搞不好，可以考虑用钢网的洞来找
        left_w = np.where(sum_w[start_w+radis:start_w+int(mesh_width/2)] > jiao_thresh * mesh_hight)
        right_w = np.where(sum_w[start_w+int(mesh_width/2):end_w-radis] > jiao_thresh * mesh_hight)
        if left_w[0].shape[0] == 0 or right_w[0].shape[0] == 0:
            ret_dict['defect'] = DEFECTS.QUEJIAO
            pts = ((start_w, end_w), (start_h, end_h))
            ret_dict['defect_pts_list'] = [np.array(pts)]
            return ret_dict
        left_edge, right_edge = np.max(left_w), np.min(right_w)
        ws_list = [
            (start_w, start_w + radis + left_edge),
            (start_w + int(mesh_width/2) + right_edge, end_w),
        ]
        # pdb.set_trace()
        jiao_list = []
        for ws in ws_list:
            jiao_bin = mesh_bin[start_h:end_h, ws[0]:ws[1]]
            jiao_bgr = mesh_bgr[start_h:end_h, ws[0]:ws[1]]
            jiao_dict = {
                'jiao_bin': jiao_bin,
                'jiao_bgr': jiao_bgr
            }
            print('jiaoshape', jiao_bin.shape)
            cv2.imshow('jiaobin', jiao_bin)
            cv2.waitKey(0)
            jiao_list.append(jiao_dict)
        ret_dict['jiao_list'] = jiao_list
        return ret_dict

    def daxiaojiao(self, jiao_bgr):
        '''
        大小胶检测
        # TODO: 数胶区域洞的个数
        :return:
        '''
        ret_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
        }
        return ret_dict

    def quejiao(self, jiao_bgr):
        '''
        缺胶检测
        # TODO: 数胶区域洞的个数
        :return:
        '''
        ret_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
        }
        return ret_dict

    def detect(self, mesh_bgr, mesh_outter, mesh_bin, model_type):
        '''

        :param mesh_bgr:
        :param mesh_outter:
        :param mesh_bin:
        :param templ_pos:
        :return:
        '''
        ret_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
        }
        if model_type != self.model_type:
            self.model_type = model_type
            self.mesh_setting = self.mesh_settings[model_type]
            self.liner_setting = self.liner_settings[model_type]
        ret = self.crop_jiaos(mesh_bgr, mesh_bin)
        if ret['defect'] != DEFECTS.LIANGPIN:
            for key, val in ret.items():
                ret_dict[key] = val
            return ret_dict
        for jiao_bgr in ret['jiao_list']:
            ret = self.daxiaojiao(jiao_bgr)
            if ret['defect'] != DEFECTS.LIANGPIN:
                for key, val in ret.items():
                    ret_dict[key] = val
                break
            ret = self.quejiao(jiao_bgr)
            if ret['defect'] != DEFECTS.LIANGPIN:
                for key, val in ret.items():
                    ret_dict[key] = val
                break
        return ret_dict
