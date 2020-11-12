import mvsdk
from config import config
import cv2
import time
import numpy as np

class Camera:
    def __init__(self, camId):
        self.mvsdk = None
        self.hCamera = None
        self.pFrameBuffer = None
        # cam parameters
        self.camset_dict = {}
        self.camId = camId
        # cam sn
        self.cam_sn = config['cameras']['sns'][camId]
        self.exposetime = config['cameras']['exposetime'][camId]
        self.once_wb = config['cameras']['gains'][camId]
        self.trigger_num = config['cameras']['trigger_num'][camId]
        self.startCam()

    def startCam(self):
        # 枚举相机
        DevList = mvsdk.CameraEnumerateDevice()
        #	DevList = mvsdk.CameraEnumerateDeviceEx()
        nDev = len(DevList)
        print('Camera numbers:', nDev)
        for i in range(nDev):
            if self.cam_sn == DevList[i].acSn:
                DevInfo = DevList[i]
                break
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
        mvsdk.CameraSetGain(hCamera, int(self.once_wb[0]), int(self.once_wb[1]), int(self.once_wb[2]))
        # set gain to make the image lighter
        mvsdk.CameraSetAnalogGain(hCamera, 20)
        mvsdk.CameraSetExposureTime(hCamera, float(self.exposetime) * 1000)
        # mvsdk.CameraSetSaturation(hCamera, 0)
        # mvsdk.CameraSetSharpness(hCamera, 0)
        tmp_ok = mvsdk.CameraGetSharpness(hCamera)
        print(tmp_ok)

        # 设置分辨率
        #       sRoiResolution = mvsdk.CameraGetImageResolution(hCamera)
        #       print(type(sRoiResolution))
        #       print(sRoiResolution)
        #       sRoiResolution.iIndex = 10
        #       mvsdk.CameraSetImageResolution(hCamera, sRoiResolution)
        #       sRoiResolution = mvsdk.CameraGetImageResolution(hCamera)
        #       print(sRoiResolution)

        # 让SDK内部取图线程开始工作
        mvsdk.CameraPlay(hCamera)

        # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (
            1 if monoCamera else 3)

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
    
    def getUsbCamSns(self):
        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        print('Camera numbers:', nDev)
        if nDev < 1:
            print("No camera was found!")
            return
        DevInfo = 0
        for i in range(nDev):
            print("Cam %s====================================="%(i))
            DevInfo = DevList[i]
            print("Devinfo:", DevInfo)
        if DevInfo == 0:
            print('color_cam_sn is wrong, can not get Devinfo, please check')
            return

    def run(self):
        countIdx = 0
        tcount = time.time()
        tmp_FPS = 15
        tmp_bright = 100
        image_var = 60
        self.color_cam = True
        set_cam_sn = 0
        while (cv2.waitKey(1) & 0xFF) != ord('q'):
            # 从相机取一帧图片
            try:
                pRawData, FrameHead = self.mvsdk.CameraGetImageBuffer(self.hCamera, 200)
                self.mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
                self.mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

                # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
                # 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
                frame_data = (self.mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth,
                                       1 if FrameHead.uiMediaType == self.mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
                #                cv2.imwrite('img.png', frame)

                # color cam or not
                if FrameHead.uiMediaType == self.mvsdk.CAMERA_MEDIA_TYPE_MONO8:
                    self.color_cam = False
                else:
                    self.color_cam = True

                # print(type(frame))
                #                record_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                [height, width, pixels] = frame.shape
                img = cv2.resize(frame, (int(width/3), int(height/3)), interpolation=cv2.INTER_CUBIC)
                if pixels != 1:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                cv2.imshow('Cam_%s, Sn_%s'%(self.camId, self.cam_sn), img)

            except self.mvsdk.CameraException as e:
                if e.error_code != self.mvsdk.CAMERA_STATUS_TIME_OUT:
                    print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))

if __name__ == '__main__':
    camId = 1
    cam = Camera(camId)
    cam.run()
