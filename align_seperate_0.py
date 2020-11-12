import cv2
import pdb, sys
from config import config
sys.path.append(config['linemod_root'])
import numpy as np
import cpu_matcher
import _pickle as cp
import image_process
from config import DEFECTS


class Aligner(object):
    def __init__(self, template_name, rough_template_name=None):
        self.rough_matcher = None
        if rough_template_name is not None:
            # 把料转到对的方向，角度的步长比较大，在料带上放的比较正，这一步不是必须的
            template = cp.load(open(rough_template_name, 'rb'))
            self.rough_matcher = cpu_matcher.Matcher(template)
        template = cp.load(open(template_name, 'rb'))
        self.matcher = cpu_matcher.Matcher(template)

    def align(self, mesh_bgr, mesh_bin, template_img):
        '''
        矫正钢网
        TODO:这里可以添加如果模板匹配没有成功，就返回变形
        :param img:
        :return:
        '''
        ret_dict = {
            'defect': DEFECTS.LIANGPIN,
            'defect_pts_list': [],
            'mesh_bgr': None,
            'mesh_bin': None,
            'mesh_outter': None,
            'templ_pos': None,
        }
        h, w = mesh_bin.shape
        kernel = np.ones((7,7), np.uint8)
        closed = cv2.morphologyEx(mesh_bin, cv2.MORPH_CLOSE, kernel)
        _, cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        base = np.zeros_like(mesh_bin)
        for cnt in cnts:
            base = cv2.fillPoly(base, [cnt], 255)
            cv2.imshow('base', base)
            cv2.waitKey(0)
        if self.rough_matcher is not None:
            # 把料转到对的方向，角度的步长比较大，在料带上放的比较正，这一步不是必须的
            match_ret = self.rough_matcher.match(base)
            print('roughmatch', match_ret)
            angle = -match_ret['templ_angle']
            scale = match_ret['templ_scale']
            pos = match_ret['max_pos']
            ah, aw = int(h / scale), int(w / scale)
            mesh_bgr = cv2.resize(mesh_bgr, (aw, ah))
            mesh_bin = cv2.resize(mesh_bin, (aw, ah))
            # pdb.set_trace()
            mesh_bgr = image_process.trans_xy_rotate(mesh_bgr, 0, 0, angle)
            mesh_bin = image_process.trans_xy_rotate(mesh_bin, 0, 0, angle)
            # mesh_bgr = trans_ret['image']
            # 画图
            # th, tw = template_img.shape[:2]
            # # draw = np.stack([binary, binary, binary], axis=-1)
            # max_pos = match_ret['max_pos']
            # mesh_bgr[max_pos[1]:max_pos[1] + th, max_pos[0]:max_pos[0]+tw, 2] = template_img
            # cv2.imshow('template', template_img)
            # cv2.imshow('rotate111', mesh_bgr)
            # cv2.waitKey(0)
        mesh_outter = cv2.morphologyEx(mesh_bin, cv2.MORPH_CLOSE, kernel)
        match_ret = self.matcher.match(mesh_outter)
        print('match_ret', match_ret)
        angle = -match_ret['templ_angle']
        scale = match_ret['templ_scale']
        pos = match_ret['max_pos']
        ah, aw = int(h / scale), int(w / scale)
        mesh_bgr = cv2.resize(mesh_bgr, (aw, ah))
        mesh_bin = cv2.resize(mesh_bin, (aw, ah))
        mesh_bgr = image_process.trans_xy_rotate(mesh_bgr, 0, 0, angle)
        mesh_bin = image_process.trans_xy_rotate(mesh_bin, 0, 0, angle)
        mesh_outter = cv2.morphologyEx(mesh_bin, cv2.MORPH_CLOSE, kernel)
        # 画图
        # th, tw = template_img.shape[:2]
        # # draw = np.stack([binary, binary, binary], axis=-1)
        # max_pos = match_ret['max_pos']
        # mesh_bgr[max_pos[1]:max_pos[1] + th, max_pos[0]:max_pos[0]+tw, 2] = template_img
        # draw = np.stack([closed, closed, closed], axis=-1)
        # draw[max_pos[1]:max_pos[1] + th, max_pos[0]:max_pos[0]+tw, 2] = template_img
        # cv2.imshow('rotate111', mesh_bgr)
        # cv2.imshow('draweawe', mesh_outter)
        # cv2.waitKey(0)
        ret_dict['mesh_bgr'] = mesh_bgr
        ret_dict['mesh_outter'] = mesh_outter
        ret_dict['mesh_bin'] = mesh_bin
        ret_dict['templ_pos'] = pos
        return ret_dict

