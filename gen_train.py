import os
import cv2
import pdb
import numpy as np

def detect(img, objs, name):
    outdir = '../data/'
    outname = name
    cv2.imwrite(outdir, outname)
    for i, obj in enumerate(objs):
        pts = obj['pts']
        objname = name[:-4] + '_' + '_'.join([pts.tolist()]) + '.png'
        cv2.imwrite(os.path.join(outdir, objname), obj['image'])
