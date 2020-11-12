import numpy as np
import base64
import time
import json
import pdb
import os, sys
import cv2
from config_model import config
sys.path.append('detectron_path')
from detectron2.data import DatasetCatalog, MetadataCatalog
import random
# import get_labelme_data
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer

class ModelObj(object):
    def __init__(self, thresh=0.4):
        cfg = get_cfg()
        # DETECTRON2_REPO_PATH = '/home/dihuge/projects/obj_detect/detectron2'
        DETECTRON2_REPO_PATH = config['detectron_path']
        model_file = config['modelfile_yiwu']
        cfg.merge_from_file(DETECTRON2_REPO_PATH + model_file)
        cfg.MODEL.WEIGHTS = config['weight_yiwu1']
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = thresh  # set the testing threshold for this model
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = config['classes_yiwu1']

        cfg.INPUT.MIN_SIZE_TEST = 280
        cfg.INPUT.MAX_SIZE_TEST = 450
        # cfg.DATASETS.TEST = ("apollo_tl_demo_data/testsets", )
        #        cfg.DATASETS.TEST = ('cmesh_yiwu_big/train')
        self.predictor = DefaultPredictor(cfg)
        self.metadata = None
        # dataset_dicts = get_tl_dicts("apollo_tl_demo_data/testsets")
        # dataset_dicts = get_tl_dicts("apollo_tl_demo_data/testsets")
        # dataset_dicts = get_tl_dicts("cmesh_yiwu_big/train")
        # indir = '../../data/yiwu/train/'

    def ret2pts_list(self, ret):
        pts_list = []
        lab_list = []
        boxes = ret.get_fields()['pred_boxes'].tensor.numpy()
        labs = ret.get_fields()['pred_classes'].numpy()
        num, _ = boxes.shape
        for i in range(num):
            pts = ((boxes[i][0], boxes[i][1]), (boxes[i][2], boxes[i][3]))
            pts_list.append(np.array(pts))
            lab_list.append(labs[i])
        ret_dict = {
            'pts_list': pts_list,
            'lab_list': lab_list,
        }
        return ret_dict

    def detect_ret(self, img):
        # 输入是一张BGR图像
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.merge((img, img, img))
        ret = self.predictor(img)
        ret = ret["instances"].to("cpu")
        print('objinstance', ret)
        return ret

    def detect(self, img):
        # 输入是BGR
        t0 = time.time()
        ret = self.detect_ret(img)
        ret_dict = self.ret2pts_list(ret)
        t1 = time.time()
        print('objtime', t1 - t0)
        return ret_dict

    def detect_batch(self, imgs):
        t0 = time.time()
        min_h = 10000
        min_w = 10000
        for img in imgs:
            h, w = img.shape[:2]
            min_h = min(h, min_h)
            min_w = min(w, min_w)
        new_imgs = []
        for img in imgs:
            h, w = img.shape[:2]
            if h != min_h or w != min_w:
                img = cv2.resize(img, (min_w, min_h))
            new_imgs.append(img)
        pdb.set_trace()
        bach_imgs = np.stack(new_imgs, axis=0)
        rets = self.detect_ret(img)
        t1 = time.time()
        print('batchdetectime', t1 - t0)

    def draw(self, img, ret):
        if self.metadata is None:
            self.metadata = MetadataCatalog.get('cmesh_yiwu_big/train')
        v = Visualizer(img,
                       metadata=self.metadata,
                       scale=1,
                       )
        v = v.draw_instance_predictions(ret)
        # cv2.imshow('img', v.get_image())
        # cv2.waitKey(0)


def ret2labelme(img, name, inname, ret_dict):
    pts_list = ret_dict['pts_list']
    lab_list = ret_dict['lab_list']
    h, w = img.shape[:2]
    lab_dict = {
        'version': '4.4.0',
        'flags': {},
        'shapes': [],
        'imagePath': name,
        'imageData': base64.b64encode(open(inname, 'rb').read()).decode('utf-8'),
        'imageHeight': h,
        'imageWidth': w,
    }
    for i, pts in enumerate(pts_list):
        one_shape = {
            'label': str(lab_list[i]),
            'grou_id': None,
            'shape_type': 'rectangle',
            'flags': {},
            'points': [
                [float(pts[0, 0]), float(pts[0, 1])],
                [float(pts[1, 0]), float(pts[1, 1])]
            ]
        }
        lab_dict['shapes'].append(one_shape)
    return lab_dict


def detect_dir(indir, outdir):
    model = ModelObj(0.1)
    #    tl_metadata = MetadataCatalog.get(indir)
    for name in os.listdir(indir):
        #        if name != '176_0_side_0_big_0.png':
        #            continue
        inname = os.path.join(indir, name)
        print(inname)
        img = cv2.imread(inname)

        #        outputs = model.detect_ret(img)
        #        model.draw(img, outputs)
        pts_list = model.detect(img)
        lab_dict = ret2labelme(img, name, inname, pts_list)
        outname = os.path.join(outdir, name[:-4] + '.json')
        json.dump(lab_dict, open(outname, 'w'))


def detect_batch_dir(indir, outdir, batch_size=5):
    imgs = []
    model = ModelObj()
    #    tl_metadata = MetadataCatalog.get(indir)
    for name in os.listdir(indir):
        #        if name != '176_0_side_0_big_0.png':
        #            continue
        inname = os.path.join(indir, name)
        print(inname)
        img = cv2.imread(inname)
        imgs.append(img)
        if len(imgs) == batch_size:
            model.detect_batch(imgs)
            imgs = []


if __name__ == '__main__':
    # indir = '../data/0521_bao/images/'
    #    indir = '../data/'
    # indir = '../data/0601/images_11/'
    # outdir = '../data/0601/jsons_yiwu_11/'
    #    indir = '/home/ta/projects/obj_detect/data/0601/images_11/'
    #    outdir = '../data/tmp'
    #    indir = '../data/yiwu_train/0620/images/'
    #    outdir = '../data/yiwu_train/0620/jsons/'
    indir = '../../obj_detect/data/707/0623/20200623/images/'
    outdir = '../../obj_detect/data/707/0623/20200623/rets/'
    detect_dir(indir, outdir)
    # detect_batch_dir(indir, outdir)
