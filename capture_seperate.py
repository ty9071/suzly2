# coding=utf-8
import pdb
import importlib
import cv2
import os
# from config import config
import os

import serial
from modbus_tk import modbus_rtu

from config import config
from utils import QueueManager
import time
import cv2
import numpy as np
import mvsdk
from datetime import datetime
import copy
import sys
from queue import Queue
import threading
from threading import Thread
import pdb
import logging_info
import modbus_tk.defines as cst
from global_singleton import GolbalSingleton


class ColorCamera:
    def __init__(self, camId, model_types, logger):
        self.logger = logger
        # pdb.set_trace()
        self.logger.info('Start')
        self.camId = camId
        self.N = 0
        self.mvsdk = None
        self.hCamera = None
        self.pFrameBuffer = None

        self.model_type = config['model_type']
        # pdb.set_trace()

        # 跟踪
        self.count_roi = 0
        track_module = importlib.import_module('track_seperate_%d' % camId)
        self.tracker = track_module.Tracker(model_types)

        # cam parameters
        self.cam_sn = config['cameras']['sns'][camId]
        self.exposetime = config['cameras']['exposetime'][camId]
        self.exposetime_below = config['cameras']['exposetime_below'][camId]
        self.gain = config['cameras']['gain'][camId]
        self.once_wb = config['cameras']['gains'][camId]
        self.trigger_num = config['cameras']['trigger_num'][camId]
        self.usb_cam = config['cameras']['usb_cam'][camId]

        # queue
        # local queue, used by tracker
        self.q = Queue()  # tracker
        self.singleton = GolbalSingleton()
        self.redis_db = self.singleton.conn_redis()
        self.server_addr = '127.0.0.1'
        if config['LOCAL_IMAGE'] == True:
            th = Thread(target=self.capture_local, args=())
            th.setDaemon(True)
            th.start()
        else:
            # object queue, for detect
            self.connectedObj = False
            self.connectObj()
            # show queue
            self.connectedShow = False
            self.connectShow()
            # capture flag queue
            self.connectedCapture = False
            self.connectCapture()

            self.startCam()
            th = Thread(target=self.capture, args=())
            th.setDaemon(True)
            th.start()
        print('Camera %d init done' % camId)

    def connectShow(self):
        while self.connectedShow == False:
            try:
                # color result queue
                QueueManager.register('show')
                manager = QueueManager(address=(self.server_addr, 9111), authkey=b'dihuge')
                manager.connect()
                self.show_sender = manager.show()
                self.connectedShow = True
            except Exception as e:
                print('Show_ConnectRefuseRec', e)
                time.sleep(1)

    def connectCapture(self):
        while self.connectedCapture == False:
            try:
                # color result queue
                QueueManager.register('capture')
                manager = QueueManager(address=(self.server_addr, 9110), authkey=b'dihuge')
                manager.connect()
                self.capture_sender = manager.capture()
                self.connectedCapture = True
            except Exception as e:
                print('Capture_ConnectRefuseRec', e)
                time.sleep(1)

    def connectObj(self):
        while self.connectedObj == False:
            try:
                QueueManager.register('obj_%d' % self.camId)
                manager = QueueManager(address=(self.server_addr, 9112), authkey=b'dihuge')
                manager.connect()
                if self.camId == 0:
                    self.obj_sender = manager.obj_0()
                elif self.camId == 1:
                    self.obj_sender = manager.obj_1()
                elif self.camId == 2:
                    self.obj_sender = manager.obj_2()
                elif self.camId == 3:
                    self.obj_sender = manager.obj_3()
                elif self.camId == 4:
                    self.obj_sender = manager.obj_4()
                elif self.camId == 5:
                    self.obj_sender = manager.obj_5()
                self.connectedObj = True
            except Exception as e:
                print('Obj_ConnectRefuseRec', e)
                time.sleep(1)

    def startCam(self):
        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        print('Camera numbers:', nDev)
        if nDev < 1:
            print("No camera was found!")
            return
        DevInfo = 0
        for i in range(nDev):
            if self.cam_sn == DevList[i].acSn:
                DevInfo = DevList[i]
        if DevInfo == 0:
            print('color_cam_sn is wrong, can not get Devinfo, please check')
            return
        print("Devinfo:", DevInfo)

        # 打开相机
        hCamera = 0
        try:
            hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message))
            return
        # 设置相机输出位RGB格式图像
        mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_RGB8)
        # 获取相机特性描述
        cap = mvsdk.CameraGetCapability(hCamera)
        # 判断是黑白相机还是彩色相机
        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)
        # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        # 相机模式切换, 0:连续采集; 2:触发采集
        mvsdk.CameraSetTriggerMode(hCamera, 1)
        mvsdk.CameraSetAeState(hCamera, 0)
        # 设置白平衡参数，根据demo里的一键白平衡来的
        mvsdk.CameraSetGain(hCamera, int(self.once_wb[0]), int(self.once_wb[1]), int(self.once_wb[2]))
        # 设置曝光时间，单位ms
        mvsdk.CameraSetExposureTime(hCamera, int(self.exposetime) * 1000)
        # gain
        mvsdk.CameraSetAnalogGain(hCamera, int(self.gain))
        # 让SDK内部取图线程开始工作
        mvsdk.CameraPlay(hCamera)

        # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)

        # 分配RGB buffer，用来存放ISP输出的图像
        # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
        pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

        self.mvsdk = mvsdk
        self.hCamera = hCamera
        self.pFrameBuffer = pFrameBuffer

    def releaseCam(self):
        # 关闭相机
        mvsdk.CameraUnInit(self.hCamera)

        # 释放帧缓存
        mvsdk.CameraAlignFree(self.pFrameBuffer)

    def logging_image(self, outdir, camId, img):
        strdate = datetime.strftime(datetime.now(), '%y_%m_%d_%H_%M_%S_%f.jpg')
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        outsub = os.path.join(outdir, str(camId))
        if not os.path.isdir(outsub):
            os.mkdir(outsub)
        outname = os.path.join(outsub, strdate)
        cv2.imwrite(outname, cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    def capture(self):

        # 不同的寄存器触发，trigger_number定义了每个相机每个步进的触发总次数
        red = -1
        num1 = 0
        while True:
            num1 += 1
            if self.camId == 0:
                trigger_number = 1
                red = self.redis_db.get("capture0")
                # self.redis_db.set("capture0", 0)
            else:
                trigger_number = 2
                red = self.redis_db.get("capture1")
            if 1 == int(red):
                self.N += 1
                # 一批次的采集只要有一张没采成功，这一批都报错
                print("------trigger_number----------", trigger_number)
                try:
                    for i in range(trigger_number):
                        if i == 0:
                            mvsdk.CameraSetExposureTime(self.hCamera, int(self.exposetime) * 1000)
                        else:
                            mvsdk.CameraSetExposureTime(self.hCamera, int(self.exposetime_below) * 1000)
                        self.mvsdk.CameraSoftTrigger(self.hCamera)
                        pRawData, FrameHead = self.mvsdk.CameraGetImageBuffer(self.hCamera, 150)
                        self.mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
                        self.mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

                        # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
                        # 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
                        frame_data = (self.mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                        frame = np.frombuffer(frame_data, dtype=np.uint8)
                        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth,
                                               1 if FrameHead.uiMediaType == self.mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
                        if config['logging_full']:
                            self.logging_image(config['full_dir'], self.camId, frame, self.N, i)
                        #     self.N += 1  # 注意self.N的更新一定要在put queue的前面，这样第一次触发才是1。一次软触发采集多张照片，计数只增加1，组内的图片通过batch_count来区分
                        print("----------n----------", self.N)
                        self.capture_sender.put({'camId': self.camId, 'trig_count': self.N, 'batch_count': i, })
                        self.q.put({'image': frame, 'count': self.N, 'batch_count': i})
                        time.sleep(0.05)

                        if self.camId == 0:
                            self.redis_db.set("capture0", 0)
                        else:
                            self.redis_db.set("capture1", 0)

                    print("send capture and q success", self.N)
                except self.mvsdk.CameraException as e:
                    if e.error_code != self.mvsdk.CAMERA_STATUS_TIME_OUT:
                        print("color_CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))

            else:
                time.sleep(0.05)

    def capture_local(self):
        while True:
            indir = '../data/local_inputs/cam_%d' % self.camId
            names = os.listdir(indir)
            if len(names) == 0:
                time.sleep(0.5)
            for name in names:
                inname = os.path.join(indir, name)
                print(inname)
                img = cv2.imread(inname)
                self.capture_sender.put(self.camId)
                self.q.put({'image': img, 'count': self.N, })
                self.N += 1
                if self.N > 100:
                    self.N = 0
                os.remove(inname)

    def run(self):
        area = []
        while True:
            if self.q.qsize() > 0:
                frame_dict = self.q.get()
                img = frame_dict['image']
                if config['cameras']['show_realtime'][camId] == True:
                    show_wh = (480, 270)
                    show_img = cv2.resize(img, show_wh)
                    show_dict = {
                        'type': 'image_real',
                        'image': show_img,
                        'camId': self.camId,
                        'batch_count': frame_dict['batch_count']
                    }
                    while self.show_sender.qsize() > 15:
                        self.show_sender.get()
                    self.show_sender.put(show_dict)
                frame_dict['area']=area
                track_dict = self.tracker.track(frame_dict, self.model_type)
                for obj in track_dict['objs']:
                    # 将相机数和触发计数放到obj里面去，这两个值要作为维护结果buffer的参数
                    obj['camID'] = self.camId
                    obj['trig_count'] = frame_dict['count']
                    obj['batch_count'] = frame_dict['batch_count']
                    while self.obj_sender.qsize() > 20:
                        print('obj sender full', self.obj_sender.qsize())
                        self.obj_sender.get()
                    self.obj_sender.put(obj)
                    if 'area' in obj:
                        area = obj['area']
            else:
                time.sleep(0.05)


if __name__ == '__main__':
    camId = int(sys.argv[1])
    model_types = ['624']
    logger = logging_info.set_logger(config['log_dir'], os.path.basename(__file__) + '_%d' % camId)
    colorcam = ColorCamera(camId, model_types, logger)
    colorcam.run()