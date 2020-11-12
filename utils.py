from multiprocessing.managers import BaseManager
import time
from config import config
import os
import cv2
import importlib
import numpy as np
import pdb
import datetime


class QueueManager(BaseManager):
    pass


def load_liner_settings(model_types):
    settings = {}
    for model_type in model_types:
        model_name = 'liner_setting_' + model_type
        if not os.path.isfile(model_name + '.py'):
            idx = model_name.rfind('_')
            model_name = model_name[:idx]
        liner = importlib.import_module(model_name).liner
        settings[model_type] = liner
    return settings


def load_templates(model_types, scale):
    temp_liners = {}
    for model_type in model_types:
        tempname = os.path.join(config['template_dir'], 'liner_template_%s.png' % model_type)
        liner_temp = cv2.imread(tempname, 0)
        _, liner_temp = cv2.threshold(liner_temp, 120, 255, cv2.THRESH_BINARY_INV)
        h, w = liner_temp.shape[:2]
        sh, sw = int(h / scale), int(w / scale)
        liner_temp = cv2.resize(liner_temp, (sw, sh))
        temp_liners[model_type] = liner_temp
    return temp_liners


def load_mesh_settings(model_types):
    setting_dict = {}
    for model_type in model_types:
        setting = importlib.import_module('mesh_setting_' + model_type).mesh
        setting_dict[model_type] = setting
    return setting_dict


def load_mesh_temps(model_types):
    # 读取每种mesh的二值化图像
    meshdir = config['template_dir']
    mesh_dict = {}
    for model_type in model_types:
        mesh_name = os.path.join(meshdir, 'mesh_template_' + model_type) + '.png'
        img = cv2.imread(mesh_name, 0)
        _, binary = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
        # kernel = np.ones((13, 13), np.uint8)
        # binary = cv2.erode(binary, kernel)
        idx = np.where(binary > 0)
        min_y, max_y = np.min(idx[0]), np.max(idx[0])
        pad = 5
        binary[min_y:min_y + pad] = 0
        binary[max_y - pad:min_y + 1] = 0
        mesh_dict[model_type] = binary
    return mesh_dict


def load_mesh_temp_holes(model_types):
    # 读取每种mesh的二值化图像
    meshdir = config['template_dir']
    mesh_dict = {}
    for model_type in model_types:
        mesh_name = os.path.join(meshdir, 'mesh_template_hole_' + model_type) + '.png'
        img = cv2.imread(mesh_name, 0)
        _, binary = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
        mesh_dict[model_type] = binary
    return mesh_dict


def get_liner_bin(img, thresh, do_close=True):
    # 返回liner的二值化图像
    img = img.astype(np.float32)
    diff = img[:, :, 0] * 2 - img[:, :, 1] - img[:, :, 2]
    # diff = diff.astype(np.uint8)
    # base = diff
    _, base = cv2.threshold(diff, thresh, 255, cv2.THRESH_BINARY)
    #    base = base.astype(np.uint8)
    #    cv2.imshow('base1', base)
    #    cv2.waitKey(0)
    # h, w = diff.shape[:2]
    # base = np.zeros((h, w), np.uint8)
    # if thresh is None:
    #     idx = np.where(diff > liner_setting['blue_diff'])
    # else:
    # idx = np.where(diff > thresh)
    # base[idx] = 255
    # 去掉钢网附近的蓝边
    diff = img[:, :, 1] - img[:, :, 2]
    idx = np.where(diff < 30)
    if idx[0].shape[0] > 0:
        base[idx] = 0

    # max_gr = np.max(img[:, :, 1:], axis=-1)
    # idx = np.where(max_gr < 110)
    # base[idx] = 0
    # idx = np.where(img[:, :, 0] < 160)
    # base[idx] = 0
    if do_close == True:
        kernel = np.ones((7, 7), np.uint8)
        # for i in range(3):
        base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, kernel)
    # cv2.imshow('base', base)
    # cv2.waitKey(0)
    return base


def show_tmp(img):
    h, w = img.shape[:2]
    scale = 2
    if h > 2000:
        scale = 4
    show_img = cv2.resize(img, (int(w / scale), int(h / scale)))
    cv2.imshow(str(time.time()), show_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def draw_defect(img, defect_ret):
    pts_list = defect_ret['defect_pts_list']
    pad = 20
    if len(img.shape) == 2:
        draw = np.stack([img, img, img], np.uint8)
        # ret = cv2.rectangle(np.stack([img, img, img], axis=-1), (pts[0, 0], pts[0, 1]), (pts[1, 0], pts[1,1]), (0, 0, 255), 4)
    else:
        draw = img
    # draw = cv2.merge((img, img, img))
    for pts in pts_list:
        print("type of pts:", type(draw))
        print(draw.shape)
        print("pts:", pts)
        print("pad:", pad)
        pts = pts.astype(np.int32)
        draw = cv2.rectangle(draw, (pts[0, 0] - pad, pts[0, 1] - pad), (pts[1, 0] + pad, pts[1, 1] + pad), (0, 0, 255),
                             4)
    return draw
    # cv2.imshow('img', ret)
    # cv2.waitKey(0)
    # utils.show_tmp(img)


def save_by_idx(ret_dict, camId, img):
    # 按数字存文件
    # 拼回big
    nowtime = datetime.datetime.now().strftime('%Y-%m-%d')
    base_dir = '/home/ta/sdb2T/logs/'
    retPath = 'ret_idx_%d' % camId+'-'+nowtime
    if not os.path.exists(base_dir+retPath):
        os.mkdir(base_dir+retPath)
    wrong = str(ret_dict['defect'])[8:]
    out_dir = os.path.join(base_dir, retPath + '/' + wrong)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    pts_list = ret_dict['defect_pts_list']
    draw = ret_dict['image']

    trig_count = ret_dict['trig_count']
    idx = ret_dict['idx']
    # name = '%d_%d' % (trig_count, idx)
    name = datetime.datetime.now().strftime('%y_%m_%d_%H_%M_%S_%f')
    out_name = os.path.join(out_dir, name)
    print('cuntulujing', out_name)
    with open(out_name + '.txt', 'w') as f:
        f.write(wrong + '\n')
        if len(pts_list) > 0:
            for pts in pts_list:
                f.write(
                    " ".join(list(map(str, [int(pts[0, 0]), int(pts[0, 1]), int(pts[1, 0]), int(pts[1, 1])]))) + '\n')
    cv2.imwrite(os.path.join(out_name + '.jpg'), draw)
    #    cv2.imwrite(os.path.join(out_name + '_org.jpg'), img)
    return ret_dict
