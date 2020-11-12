#coding=utf-8
import pdb

import os
from config import config
from utils import QueueManager
import time 
import cv2
import numpy as np
import mvsdk

class ReleaseCamera:
    def __init__(self):
        self.mvsdk = None
        self.hCamera = None
        self.pFrameBuffer = None
        # cam parameters
        #self.startCam()
        self.releaseCam = False 
        print('ColorCamera init done')

    
    def startCam(self):
        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        print('Camera numbers:', nDev)
        if nDev < 1:
            print("No camera was found!")
            return
        DevInfo = 0
        for i in range(nDev):
            if self.color_cam_sn == DevList[i].acSn:
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
            print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
            return

        # 获取相机特性描述
        cap = mvsdk.CameraGetCapability(hCamera)

        # 判断是黑白相机还是彩色相机
        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

        # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)

        # 相机模式切换成连续采集
        mvsdk.CameraSetTriggerMode(hCamera, 0)

        # 手动曝光，曝光时间30ms
        mvsdk.CameraSetAeState(hCamera, 0)
#        mvsdk.CameraSetExposureTime(hCamera, 30 * 1000)
        mvsdk.CameraSetExposureTime(hCamera, int(self.exposetime) * 1000)


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


    def run(self):
        while self.releaseCam == False:
            try:
                DevList = mvsdk.CameraEnumerateDevice()
                for Dev in DevList:
                    time.sleep(1)
                    #hCamera = mvsdk.CameraInit(Dev, -1, -1)
                  #  print(mvsdk.CameraIsOpened(Dev))
                    print(Dev)
                    mvsdk.CameraUnInit(Dev)
               #     print(tmp)
               #     time.sleep(0.5)
                self.releaseCam = True 
                print('ReleaseCamera Done!', self.releaseCam)
            except mvsdk.CameraException as e:
                print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
                
if __name__ == '__main__':
    releasecam = ReleaseCamera()
    releasecam.run()

