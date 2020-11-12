import pdb
import utils
import os
import cv2
import numpy as np
from config import config
# from config import DEFECTS


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

        # 同轴光
        area_idx0 = org_img[255:1451, 50:1707]
        h, w = area_idx0.shape[:2]
        sh, sw = int(h/self.scale), int(w/self.scale)
        small_idx0 = cv2.resize(area_idx0, (sw, sh))

        area_idx1 = org_img[1700:2860, 50:1707]
        h, w = area_idx1.shape[:2]
        sh, sw = int(h / self.scale), int(w / self.scale)
        small_idx1 = cv2.resize(area_idx1, (sw, sh))

        area_idx2 = org_img[255:1451, 3900:5450]
        h, w = area_idx2.shape[:2]
        sh, sw = int(h / self.scale), int(w / self.scale)
        small_idx2 = cv2.resize(area_idx2, (sw, sh))

        area_idx3 = org_img[1700:2860, 3900:5450]
        h, w = area_idx3.shape[:2]
        sh, sw = int(h / self.scale), int(w / self.scale)
        small_idx3 = cv2.resize(area_idx3, (sw, sh))

        '''
        环形光
        area_idx0 = org_img[273:1921, 0:1817]
        area_idx1 = org_img[2017:3609, 73:1841]
        area_idx2 = org_img[153:1833, 3585:5385]
        area_idx3 = org_img[1825:3585, 3609:5401]
        '''
        org_part = [area_idx0, area_idx1, area_idx2, area_idx3]
        small_part = [small_idx0, small_idx1, small_idx2, small_idx3]
        for num in range(4):
            sh, sw = small_part[num].shape[:2]
            # print("small_shape:", small_part[num].shape)
            # gray = cv2.cvtColor(small_part[num], cv2.COLOR_BGR2GRAY)
            gray = small_part[num]
            # print(gray.shape)
            # cv2.imshow('gray', gray)
            # cv2.waitKey()
            if num == 1:
                _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
            else:
                _, binary = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)
            # _, binary = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY_INV)
            # cv2.namedWindow('binary', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('binary', 700, 500)
            # cv2.imshow('binary', binary)
            # cv2.waitKey()
            # 0707找轮廓处理
            # 提取轮廓
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # 标记轮廓
            # cv2.drawContours(small_part[num], contours, -1, (255, 0, 255), 1)
            # 计算轮廓面积
            area_accept = 0
            pad = 3  # 保留一些边缘
            for i in contours:
                area_contours = cv2.contourArea(i)
                cnt = i
                if area_contours < 10000 or area_contours > 20000:  # 环形光
                    # if area_contours < 8000 or area_contours > 11000: #同轴光
                    continue
                else:
                    print('area_contours', area_contours)
                    rx, ry, rw, rh = cv2.boundingRect(cnt)
                    # cv2.rectangle(small_part[num], (rx, ry), (rx + rw, ry + rh), (255, 0, 255), 2)
                    # cv2.imshow('small_part[num]', small_part[num])
                    start_w = max(0, rx - pad) * self.scale
                    start_h = max(0, ry - pad) * self.scale
                    end_w = min(sw, rx + rw + pad) * self.scale
                    end_h = min(sh, ry + rh + pad) * self.scale
                    roi = org_part[num]
                    roi = roi[start_h:end_h, start_w:end_w]
                    obj = {
                        'image': roi,
                        'idx': num,
                    }
                    # cv2.imwrite("./cam0_obj/"+ '_' + str(obj['idx']) + '.png', roi)
                    area_accept = area_accept + 1
                    # 每个区域只接受一个产品
                    if area_accept == 1:
                        # print("area_contours:", area_contours)
                        objs.append(obj)
                        break
            # 如果一个产品都没有找到，把原小图压进去，并在后续判定为缺膜或者脏污
            if area_accept < 1:
                obj = {
                    'image': org_part[num],
                    'idx': num,
                }
                objs.append(obj)
                # print('area_contours', area_contours)
            #
            # cv2.namedWindow('binary', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('binary', 700, 500)
            #  cv2.imshow('binary', binary)
            # cv2.waitKey()
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
