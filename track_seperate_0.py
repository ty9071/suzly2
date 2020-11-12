import pdb
import utils
import os
import cv2
import numpy as np
from config import config


class Tracker(object):
    def __init__(self, model_types):
        self.scale = 8
        self.liner_setting = None
        self.mesh_setting = None
        self.model_type = None
        self.liner_settings = utils.load_liner_settings(model_types)
        self.mesh_settings = utils.load_mesh_settings(model_types)
        self.start_row = None
        # 用liner定位
        self.row_idx = 0
        self.mid_xy = None

    def find_objs(self, org_img):
        '''
        返回obj的列表
        TODO：这个函数是需要根据机台上拍摄的料带去改的，这里先写了能跑
        :param img:
        :return: objs, list
        '''
        objs = []
        # cv2.namedWindow('org_img', cv2.WINDOW_NORMAL)
        # cv2.resizeWindow('org_img', 1000, 800)
        # cv2.imshow('org_img', org_img)

        thre = 220
        _, binary = cv2.threshold(org_img, thre, 255, cv2.THRESH_BINARY_INV)
        # print(binary.shape)
        # cv2.namedWindow('binary', cv2.WINDOW_NORMAL)
        # cv2.resizeWindow('binary', 360, 540)
        # cv2.imshow("img_part", img_part)
        # cv2.imshow("binary", binary)
        # k = cv2.waitKey()

        # 用于找上下边界的区域范围
        width1 = 900
        height1 = 600
        # 用于找左右边界的区域范围
        width2 = 900
        height2 = 750
        # 四个产品中心点
        center = []
        center0 = [580, 960]
        center1 = [2000, 930]
        center2 = [560, 4700]
        center3 = [2000, 4700]
        center.append(center0)
        center.append(center1)
        center.append(center2)
        center.append(center3)

        for i in range(4):
            center_height1 = center[i][0] - height1
            if center_height1 < 0:
                center_height1 = 0
            center_widh1 = center[i][1] - width1
            if center_widh1 < 0:
                center_widh1 = 0
            center_height2 = center[i][0] - height2
            if center_height2 < 0:
                center_height2 = 0
            center_widh2 = center[i][1] - width2
            if center_widh2 < 0:
                center_widh2 = 0
            # 上半部分
            # print('i的值： ', i)
            up_part = binary[center_height1:center[i][0], center_widh1:center[i][1] + width1]
            # cv2.namedWindow('up_part', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('up_part', 600, 500)
            # cv2.imshow("up_part", up_part)
            # 下半部分
            down_part = binary[center[i][0]:center[i][0] + height1, center_widh1:center[i][1] + width1]
            # cv2.namedWindow('down_part', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('down_part', 600, 500)
            # cv2.imshow("down_part", down_part)
            # 左半部分
            left_part = binary[center_height2:center[i][0] + height2, center_widh2:center[i][1]]
            # cv2.namedWindow('left_part', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('left_part', 600, 500)
            # cv2.imshow("left_part", left_part)
            # 右半部分
            right_part = binary[center_height2:center[i][0] + height2, center[i][1]:center[i][1] + width2]
            # cv2.namedWindow('right_part', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('right_part', 600, 500)
            # cv2.imshow("right_part", right_part)

            # cv2.waitKey(0)

            # 矩阵的行向量相加，计算每行非零像素点个数
            sum_h = np.sum(up_part, axis=1) / 255
            idx_h = np.where(sum_h > 1300)
            # print('idx_h: ', idx_h[0].shape)
            # cv2.waitKey(0)
            # 如果tuple为空
            if idx_h[0].shape == (0,):
                start_h = 0
            else:
                start_h = np.min(idx_h)
            # cv2.waitKey(0)
            sum_h = np.sum(down_part, axis=1) / 255
            idx_h = np.where(sum_h > 1300)
            if idx_h[0].shape == (0,):
                end_h = height1
            else:
                end_h = np.max(idx_h)

            # 矩阵的列向量相加,计算每列非零像素点个数
            sum_w = np.sum(left_part, axis=0) / 255
            idx_w = np.where(sum_w > 900)
            if idx_w[0].shape == (0,):
                start_w = 0
            else:
                start_w = np.min(idx_w)

            sum_w = np.sum(right_part, axis=0) / 255
            idx_w = np.where(sum_w > 800)
            if idx_w[0].shape == (0,):
                end_w = width2
            else:
                end_w = np.max(idx_w)

            # print(start_h, end_h, start_w, end_w)
            # cv2.waitKey(0)
            if i == 0:
                img_part = org_img[center_height1 + start_h + 140:center[i][0] + end_h - 100,
                           center_widh2 + start_w + 150:center[i][1] + end_w - 110]
            elif i == 1:
                img_part = org_img[center_height1 + start_h + 110:center[i][0] + end_h - 120,
                           center_widh2 + start_w + 140:center[i][1] + end_w - 110]
            elif i == 2:
                img_part = org_img[center_height1 + start_h + 130:center[i][0] + end_h - 120,
                           center_widh2 + start_w + 100:center[i][1] + end_w - 140]
            else:
                img_part = org_img[center_height1 + start_h + 120:center[i][0] + end_h - 110,
                           center_widh2 + start_w + 100:center[i][1] + end_w - 140]

            # cv2.namedWindow('img_part', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('img_part', 508, 380)
            # cv2.imshow("img_part", img_part)
            # cv2.waitKey(0)
            obj = {
                'image': img_part,
                'idx': i,
            }
            objs.append(obj)

        return objs



    def track(self, frame_dict, model_type):
        '''
        输入相机拍摄的图，返回每个料的小图
        objs: list，每个元素是一个dict
        {
            'image': 每个料小图，
            'row_idx': 每行，
            'idx': 每行的第几个，
        }
        '''
        ret_dict = {
            'valid': True,
            'objs': [],
            'msg': '',
        }
        img = frame_dict['image']
        if self.model_type != model_type:
            self.liner_setting = self.liner_settings[model_type]
            self.mesh_setting = self.mesh_settings[model_type]
            self.model_type = model_type

        objs = self.find_objs(img)
        ret_dict['objs'] = objs
        # 画图
        # for obj in objs:
        #     # print('objidx', obj['idx'])
        #     cv2.imshow('img', obj['image'])
        #     cv2.waitKey(0)
        return ret_dict

def track_dir(indir):
    model_types = ['624']
    tracker = Tracker(model_types)
    model_type = config['model_type']
    for name in os.listdir(indir):
        inname = os.path.join(indir, name)
        print(inname)
#        if '260.jpg' != name:
#            continue
        img = cv2.imread(inname)
        frame_dict = {
        'image': img,
        }
        tracker.track(frame_dict, model_type)


if __name__ == '__main__':
#    indir = '../data/lingyi_live/2020_04_20_15_56_43/'
#     indir = '../data/local_buf/cam_0'
#     indir = 'D:/projects/lingyi/data/ly_live/0603/2000_1/images/'
    indir = '../data/707/707loubai/'
    track_dir(indir)
