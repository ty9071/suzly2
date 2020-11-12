# import cgitb
# cgitb.enable(format = 'text')
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import copy
import numpy as np
import sys
import subprocess
import os
import shutil
import math
import sys
import cv2
import time
# from datetime import datetime
import datetime
import pdb
from queue import Queue

from config import config, DEFECTS
from utils import QueueManager
from count import count

import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import serial
from global_singleton import GolbalSingleton


# from set_configure import setConfigure
# import set_configure
# import json
# from config import config
# import show_big
# from pyModbusTCP.client import ModbusClient
# import logging_info
# import test_link

class UI(QDialog):
    def __init__(self, logger, run_by_time=0):
        super(UI, self).__init__()
        self.logger = logger
        self.run_by_time = run_by_time
        self.current_model = 0
        self.init_ui()
        QDialog.setWindowTitle(self, '视觉检测')
        self.singleton = GolbalSingleton()
        self.redis_db = self.singleton.conn_redis()
        # if config['ui_in_win'] == False:
        self.server_addr = '0.0.0.0'
        self.show_sender = None
        self.connectedShow = False
        # self.connectShow()
        self.window2 = MyWindow2()
        self.count = 0

        # 定义一个数组 存放最新的20张图片
        self.file_array = []
        # 定义一个数组 存放图片相对应的异常类型
        self.type_array = []
        # 定义一个变量接收当前分页所在的位置
        self.wrong_lenghts = 0

        # self.recv_queue = QTimer(self)
        # self.recv_queue.timeout.connect(lambda: self.read_queue())
        # self.recv_queue.start(1)

        self.zongshu_num = count['zongshu_num']
        self.liangpin_num = count['liangpin_num']
        self.redis_db.set('zongshu_num', self.zongshu_num)
        self.redis_db.set('liangpin_num', self.liangpin_num)
        self.mopao_num = count['mopao_num']
        self.mohuashang_num = count['mohuashang_num']
        self.moque_num = count['moque_num']
        self.moyashang_num = count['moyashang_num']
        self.maoci_num = count['maoci_num']
        self.zangwu_num = count['zangwu_num']
        self.wukong_num = count['wukong_num']
        self.fanxiang_num = count['fanxiang_num']
        self.bukefamxiu_num = count['bukefamxiu_num']
        self.temp_num_all.setText(str(self.zongshu_num))
        if self.zongshu_num != 0:
            self.ok_num.setText(str(self.liangpin_num))
            self.ok_rate.setText(
                str(round((float(self.liangpin_num) / self.zongshu_num * 100), 2)) + '%')  # 显示两位小数
            self.list_temp_statics_rate[0].setText(
                str(round((float(self.mopao_num) / self.zongshu_num * 100), 2)) + '%')
            self.list_temp_statics_rate[1].setText(
                str(round((float(self.mohuashang_num) / self.zongshu_num * 100), 2)) + '%')
            self.list_temp_statics_rate[2].setText(
                str(round((float(self.moque_num) / self.zongshu_num * 100), 2)) + '%')
            self.list_temp_statics_rate[3].setText(
                str(round((float(self.moyashang_num) / self.zongshu_num * 100), 2)) + '%')
            self.list_temp_statics_rate[4].setText(
                str(round((float(self.maoci_num) / self.zongshu_num * 100), 2)) + '%')
            self.list_temp_statics_rate[5].setText(
                str(round((float(self.zangwu_num) / self.zongshu_num * 100), 2)) + '%')
            self.list_temp_statics_rate[6].setText(
                str(round((float(self.wukong_num) / self.zongshu_num * 100), 2)) + '%')
            self.list_temp_statics_rate[7].setText(
                str(round((float(self.fanxiang_num) / self.zongshu_num * 100), 2)) + '%')
            self.non_repairable_num.setText(str(self.zongshu_num - self.liangpin_num))
            self.non_repairable_num_rate.setText(
                str(round((float(self.zongshu_num - self.liangpin_num) / self.zongshu_num * 100), 2)) + '%')

        for d in DEFECTS:
            if d == DEFECTS.MOPAO:
                self.list_label_wrong_number[d.key - 1].setText(str(self.mopao_num))
            elif d == DEFECTS.MOHUASHANG:
                self.list_label_wrong_number[d.key - 1].setText(str(self.mohuashang_num))
            elif d == DEFECTS.MOQUE:
                self.list_label_wrong_number[d.key - 1].setText(str(self.moque_num))
            elif d == DEFECTS.MOYASHANG:
                self.list_label_wrong_number[d.key - 1].setText(str(self.moyashang_num))
            elif d == DEFECTS.MAOCI:
                self.list_label_wrong_number[d.key - 1].setText(str(self.maoci_num))
            elif d == DEFECTS.WUKONG:
                self.list_label_wrong_number[d.key - 1].setText(str(self.wukong_num))
            elif d == DEFECTS.FANXIANG:
                self.list_label_wrong_number[d.key - 1].setText(str(self.fanxiang_num))
            elif d == DEFECTS.ZANGWU:
                self.list_label_wrong_number[d.key - 1].setText(str(self.zangwu_num))

        self.ret_buffer = []
        for i in range(10):  # 12为工位1到工位2的排数，工位1检测0和2排，工位2检测9和11排
            tmp_none = []
            for j in range(2):  # 2排料
                tmp_none.append(None)
            self.ret_buffer.append(tmp_none)
        print(self.ret_buffer)

    def read_queue(self):
        # -1 : above frames
        # (0,1,2,3,4) : above, left, right, front, back wong
        # 5 : a couple of sequence result
        # 6 : a couple of counter
        # print("111")
        # pdb.set_trace()
        # datetime = QDateTime.currentDateTime()
        nowtime = datetime.datetime.now().strftime('    %Y-%m-%d   %H:%M:%S')
        text = nowtime
        # text = datetime.toString("dddap MMMM d hh:mm:ss")
        self.current_time.setText(text)
        if self.show_sender.qsize() > 0:
            print("show_sender_qsize", self.show_sender.qsize())
            show_dict = self.show_sender.get()
            if 'image' in show_dict['type']:
                image = show_dict['image']
                if image is None:
                    image = cv2.imread('./aligned.png')
                img = cv2.resize(image, (260, 160))
                print("shape of img begin", np.shape(img))
                img = cv2.merge((img, img, img))
                print("shape of img end", np.shape(img))

                camId = int(show_dict['camId'])

                if show_dict['type'] == 'image_real' and show_dict['batch_count'] == 0:
                    Qimg = QImage(img, 260, 160, QImage.Format_RGB888)
                    self.real_labels[camId].setPixmap(QPixmap.fromImage(Qimg))

                elif show_dict['type'] == 'image_defect':
                    # 根据触发数计算步进排数
                    trig_count = int(show_dict['trig_count'])
                    step_num = (trig_count - 1) // 2 * 4 + (trig_count - 1) % 2

                    self.zongshu_num = int(self.redis_db.get('zongshu_num'))
                    self.liangpin_num = int(self.redis_db.get('liangpin_num'))
                    self.ok_num.setText(str(self.liangpin_num))
                    idx = int(show_dict['idx'])
                    defect = show_dict['defect']
                    print("defect:", defect)

                    img = cv2.resize(image, (160, 120))

                    img = cv2.merge((img, img, img))

                    # print("img.shape:", img.shape)
                    # cv2.imwrite("test.png", img)
                    height, width, bytesPerComponent = img.shape
                    bytesPerLine = bytesPerComponent * width
                    Qimg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
                    # Qimg = QImage(img, 120, 120, QImage.Format_RGB888)

                    if camId == 0:
                        self.defect_labels[idx].setPixmap(QPixmap.fromImage(Qimg))

                        if defect is not DEFECTS.LIANGPIN:
                            self.label_left_cam_wrong_titles[idx].setText(defect.desc)
                            self.label_left_cam_wrong_titles[idx].setStyleSheet("color:red")
                            self.ret_buffer[((idx // 2) * 2 - step_num) % 10][(idx % 2)] = 1
                        else:
                            self.label_left_cam_wrong_titles[idx].setText(defect.desc)
                            self.label_left_cam_wrong_titles[idx].setStyleSheet("color:black")
                            self.ret_buffer[((idx // 2) * 2 - step_num) % 10][(idx % 2)] = 0

                    elif camId == 1 and show_dict['batch_count'] == 0:
                        self.defect_labels2[idx].setPixmap(QPixmap.fromImage(Qimg))
                        if defect is not DEFECTS.LIANGPIN:
                            self.label_front_cam_wrong_titles[idx].setText(defect.desc)
                            self.label_front_cam_wrong_titles[idx].setStyleSheet("color:red")
                        else:
                            self.label_front_cam_wrong_titles[idx].setText(defect.desc)
                            self.label_front_cam_wrong_titles[idx].setStyleSheet("color:black")
                            # ret_0 = self.ret_buffer[((idx // 2) * 2 + 7 - step_num) % 10][(idx % 2)]
                            # if ret_0 == 0:

                    # 写
                    # self.temp_num_all.setText(str(self.zongshu_num))
                    # self.zongshu_num = self.zongshu_num
                    self.temp_num_all.setText(str(self.zongshu_num))

                    # if defect != DEFECTS.LIANGPIN:
                    #     self.liangpin_num = self.liangpin_num + 1
                    #     self.ok_num.setText(str(self.liangpin_num))

                    # self.ok_rate.setText(str(int(self.liangpin_num / self.zongshu_num * 100))+'%')
                    if self.liangpin_num > 0:
                        self.ok_rate.setText(
                            str(round((float(self.liangpin_num) / (self.zongshu_num + 0) * 100), 2)) + '%')  # 显示两位小数

                    if defect == DEFECTS.MOPAO:
                        self.mopao_num = self.mopao_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.mopao_num))
                        self.bukefamxiu_num = self.bukefamxiu_num + 1

                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.mopao_num / self.zongshu_num * 100))+'%')
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(round((float(self.mopao_num) / int(self.zongshu_num * 100)), 2)) + '%')
                    if defect == DEFECTS.MOHUASHANG:
                        self.mohuashang_num = self.mohuashang_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.mohuashang_num))
                        self.bukefamxiu_num = self.bukefamxiu_num + 1
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.mohuashang_num / self.zongshu_num * 100))+'%')
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(round((float(self.mohuashang_num) / self.zongshu_num * 100), 2)) + '%')
                    if defect == DEFECTS.MOQUE:
                        self.moque_num = self.moque_num + 1
                        self.bukefamxiu_num = self.bukefamxiu_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.moque_num))
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.moque_num / self.zongshu_num * 100))+'%')
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(round((float(self.moque_num) / self.zongshu_num * 100), 2)) + '%')
                    if defect == DEFECTS.MOYASHANG:
                        self.moyashang_num = self.moyashang_num + 1
                        self.bukefamxiu_num = self.bukefamxiu_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.moyashang_num))
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.moyashang_num / self.zongshu_num * 100))+'%')
                    if defect == DEFECTS.MAOCI:
                        self.maoci_num = self.maoci_num + 1
                        self.bukefamxiu_num = self.bukefamxiu_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.maoci_num))
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.maoci_num / self.zongshu_num * 100))+'%')
                    if defect == DEFECTS.ZANGWU:
                        self.zangwu_num = self.zangwu_num + 1
                        self.bukefamxiu_num = self.bukefamxiu_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.zangwu_num))
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.zangwu_num / self.zongshu_num * 100))+'%')
                    if defect == DEFECTS.WUKONG:
                        self.wukong_num = self.wukong_num + 1
                        self.bukefamxiu_num = self.bukefamxiu_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.wukong_num))
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.wukong_num / self.zongshu_num * 100))+'%')
                    if defect == DEFECTS.FANXIANG:
                        self.fanxiang_num = self.fanxiang_num + 1
                        self.bukefamxiu_num = self.bukefamxiu_num + 1
                        self.list_label_wrong_number[defect.key - 1].setText(str(self.fanxiang_num))
                        # self.list_temp_statics_rate[defect.key - 1].setText(str(int(self.fanxiang_num / self.zongshu_num * 100))+'%')

                    # 在这里一次更新所有数值,增加百分比两位小数显示0712
                    self.list_temp_statics_rate[0].setText(
                        str(round((float(self.mopao_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    self.list_temp_statics_rate[1].setText(
                        str(round((float(self.mohuashang_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    self.list_temp_statics_rate[2].setText(
                        str(round((float(self.moque_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    self.list_temp_statics_rate[3].setText(
                        str(round((float(self.moyashang_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    self.list_temp_statics_rate[4].setText(
                        str(round((float(self.maoci_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    self.list_temp_statics_rate[5].setText(
                        str(round((float(self.zangwu_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    self.list_temp_statics_rate[6].setText(
                        str(round((float(self.wukong_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    self.list_temp_statics_rate[7].setText(
                        str(round((float(self.fanxiang_num) / (self.zongshu_num + 1) * 100), 2)) + '%')
                    # self.non_repairable_num.setText(str(self.zongshu_num - self.liangpin_num))
                    self.non_repairable_num.setText(str(self.bukefamxiu_num))
                    self.non_repairable_num_rate.setText(
                        str(round((float(self.bukefamxiu_num) / (self.zongshu_num + 1) * 100), 2)) + '%')

                    # self.list_temp_statics_rate[0].setText(str(int(self.mopao_num / self.zongshu_num * 100)) + '%')
                    # self.list_temp_statics_rate[1].setText(str(int(self.mohuashang_num / self.zongshu_num * 100)) + '%')
                    # self.list_temp_statics_rate[2].setText(str(int(self.moque_num / self.zongshu_num * 100))+'%')
                    # self.list_temp_statics_rate[3].setText(str(int(self.moyashang_num / self.zongshu_num * 100)) + '%')
                    # self.list_temp_statics_rate[4].setText(str(int(self.maoci_num / self.zongshu_num * 100)) + '%')
                    # self.list_temp_statics_rate[5].setText(str(int(self.zangwu_num / self.zongshu_num * 100)) + '%')
                    # self.list_temp_statics_rate[6].setText(str(int(self.wukong_num / self.zongshu_num * 100)) + '%')
                    # self.list_temp_statics_rate[7].setText(str(int(self.fanxiang_num / self.zongshu_num * 100)) + '%')
                    # self.non_repairable_num.setText(str(self.zongshu_num - self.liangpin_num))
                    # self.non_repairable_num_rate.setText(str(int((self.zongshu_num - self.liangpin_num) / self.zongshu_num * 100))+'%')

                    if defect is not DEFECTS.LIANGPIN:
                        self.file_array.append(QPixmap.fromImage(Qimg))
                        # self.type_array.append(defect)
                        for d in DEFECTS:
                            if d == defect:
                                self.type_array.append(d.desc)

                        self.page_of_num1()

                        # 如果图片数量大于20张就删除第一张图片；只存最新的20张图片,并且删除相对应的异常类型
                        if len(self.file_array) > 20:
                            self.file_array.pop(0)
                            self.type_array.pop(0)

    def show_real_frame(self, frame):
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (680, 270))
        Qimg = QImage(img, 680, 270, QImage.Format_RGB888)
        self.label_above_cam_real.setPixmap(QPixmap.fromImage(Qimg))

    def connectShow(self):
        while self.connectedShow == False:
            try:
                # label result queue
                QueueManager.register('show')
                retlabel_manager = QueueManager(address=(self.server_addr, 9111), authkey=b'dihuge')
                retlabel_manager.connect()
                self.show_sender = retlabel_manager.show()
                self.connectedShow = True
                print('have connected_queue_show')
            except Exception as e:
                print('Show_ConnectRefuseRec', e)
                time.sleep(1)

    def clear_data(self):
        self.zongshu_num = 0
        self.liangpin_num = 0
        self.mopao_num = 0
        self.mohuashang_num = 0
        self.moque_num = 0
        self.moyashang_num = 0
        self.maoci_num = 0
        self.zangwu_num = 0
        self.wukong_num = 0
        self.fanxiang_num = 0
        self.bukefamxiu_num = 0
        self.temp_num_all.setText('0')
        self.ok_num.setText('0')
        self.ok_rate.setText('0.0%')  # 显示两位小数
        self.non_repairable_num.setText('0')
        self.non_repairable_num_rate.setText('0.0%')
        for list in self.list_label_wrong_number:
            list.setText("0")
        for list2 in self.list_temp_statics_rate:
            list2.setText("0.0%")
        self.redis_db.set('zongshu_num', 0)
        self.redis_db.set('liangpin_num', 0)
        self.save_data()

    def do_btn(self, event):  # 自定义
        self.window2=MyWindow2()
        self.window2.show()


    def save_data(self):
        d = {'zongshu_num': self.zongshu_num, "liangpin_num": self.liangpin_num, "mopao_num": self.mopao_num,
             "mohuashang_num": self.mohuashang_num, "moque_num": self.moque_num,
             "moyashang_num": self.moyashang_num,
             "maoci_num": self.maoci_num, "zangwu_num": self.zangwu_num, "wukong_num": self.wukong_num,
             "fanxiang_num": self.fanxiang_num, "bukefamxiu_num": self.bukefamxiu_num}
        d = 'count=' + str(d)
        f = open('count.py', 'w')
        f.writelines(d)
        f.close()

    def closeEvent(self, event):
        self.save_data()

    def connectPlc(self):
        try:
            master = modbus_rtu.RtuMaster(
                serial.Serial(port=config['plc_modbus']['port'],
                              baudrate=config['plc_modbus']['baudrate'],
                              bytesize=config['plc_modbus']['bytesize'],
                              parity=config['plc_modbus']['parity'],
                              stopbits=config['plc_modbus']['stopbits']))
            master.set_timeout(5.0)
            master.set_verbose(True)
            result_det_0 = [1, 1, 1, 1]
            master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 10005, output_value=[1])
            master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 10001, output_value=result_det_0)
            master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 10000, output_value=[1])
            master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 11005, output_value=[1])
            master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 11001, output_value=result_det_0)
            master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 11000, output_value=[1])

            reply = QMessageBox.information(self, "消息框标题", "plc通信复位成功，请关闭此弹窗，在机台先按复位按钮在启动！",
                                            QMessageBox.Yes | QMessageBox.No)
        except Exception as exc:
            reply = QMessageBox.warning(self, "消息框标题", "plc通信中断，请多复位几次，如无效果，请联系现场工程师检测串口通信线是否松动！",
                                        QMessageBox.Yes | QMessageBox.No)
            print(str(exc))

    def init_ui(self):
        # self.resize(1366, 768)
        # self.setFixedSize(1366, 768)
        self.resize(1366, 709)
        self.setFixedSize(1366, 709)
        ###################################################3
        self.frame_show_real_cam = QFrame(self)
        self.frame_show_real_cam.resize(1000, 225)
        self.frame_show_real_cam.move(10, 10)
        self.frame_show_real_cam.setFrameShape(QFrame.Box)
        self.frame_show_real_cam.setLineWidth(2)

        self.frame_show_wrong_cam = QFrame(self)
        self.frame_show_wrong_cam.resize(1000, 225)
        self.frame_show_wrong_cam.move(10, 245)
        self.frame_show_wrong_cam.setFrameShape(QFrame.Box)
        self.frame_show_wrong_cam.setLineWidth(2)

        self.frame_show_wrong_small = QFrame(self)
        self.frame_show_wrong_small.resize(1000, 325)
        self.frame_show_wrong_small.move(10, 490)
        self.frame_show_wrong_small.setFrameShape(QFrame.Box)
        self.frame_show_wrong_small.setLineWidth(2)

        self.frame_count_number = QFrame(self)
        self.frame_count_number.resize(310, 150)
        self.frame_count_number.move(1050, 10)
        self.frame_count_number.setFrameShape(QFrame.Box)
        self.frame_count_number.setLineWidth(2)

        self.frame_real_wrong = QFrame(self)
        self.frame_real_wrong.resize(310, 758)
        self.frame_real_wrong.move(1050, 170)
        self.frame_real_wrong.setFrameShape(QFrame.Box)
        self.frame_real_wrong.setLineWidth(2)

        ######################################################################
        self.label_above_cam_real_title = QLabel(self)
        self.label_above_cam_real_title.setText("相机1实时图像")
        self.label_above_cam_real_title.setFont(QFont("Times", 17))
        self.label_above_cam_real_title.setFixedSize(200, 40)
        self.label_above_cam_real_title.move(110, 10)
        self.label_above_cam_real = QLabel(self)
        # self.label_above_cam_real.setText("实时图像")
        self.label_above_cam_real.setFont(QFont("Times", 28))
        self.label_above_cam_real.setFixedSize(260, 160)
        self.label_above_cam_real.move(50, 50)
        # self.label_above_cam_real.setStyleSheet("border-image: url('2.png');")

        self.label_left_cam_wrong_title = QLabel(self)
        self.label_left_cam_wrong_title.setText("相机1检测图像")
        self.label_left_cam_wrong_title.setFont(QFont("Times", 17))
        self.label_left_cam_wrong_title.setFixedSize(200, 40)
        self.label_left_cam_wrong_title.move(600, 10)

        self.label_left_cam_wrong_title1 = QLabel(self)
        self.label_left_cam_wrong_title1.setText("")
        self.label_left_cam_wrong_title1.setFont(QFont("Times", 17))
        self.label_left_cam_wrong_title1.setFixedSize(200, 40)
        self.label_left_cam_wrong_title1.move(390, 40)

        self.label_left_cam_wrong = QLabel(self)
        self.label_left_cam_wrong.setFont(QFont("Times", 28))
        self.label_left_cam_wrong.setFixedSize(160, 120)
        self.label_left_cam_wrong.move(330, 80)
        # self.label_left_cam_wrong.setStyleSheet("border-image: url('3.png');")

        self.label_left_cam_wrong_title2 = QLabel(self)
        self.label_left_cam_wrong_title2.setText("")
        self.label_left_cam_wrong_title2.setFont(QFont("Times", 17))
        self.label_left_cam_wrong_title2.setFixedSize(200, 40)
        self.label_left_cam_wrong_title2.move(555, 40)

        self.label_left_cam_wrong2 = QLabel(self)
        self.label_left_cam_wrong2.setFont(QFont("Times", 28))
        self.label_left_cam_wrong2.setFixedSize(160, 120)
        self.label_left_cam_wrong2.move(500, 80)
        # self.label_left_cam_wrong2.setStyleSheet("border-image: url('3.png');")

        self.label_left_cam_wrong_title3 = QLabel(self)
        self.label_left_cam_wrong_title3.setText("")
        self.label_left_cam_wrong_title3.setFont(QFont("Times", 17))
        self.label_left_cam_wrong_title3.setFixedSize(200, 40)
        self.label_left_cam_wrong_title3.move(725, 40)
        self.label_left_cam_wrong3 = QLabel(self)

        self.label_left_cam_wrong3.setFont(QFont("Times", 28))
        self.label_left_cam_wrong3.setFixedSize(160, 120)
        self.label_left_cam_wrong3.move(670, 80)
        # self.label_left_cam_wrong3.setStyleSheet("border-image: url('3.png');")

        self.label_left_cam_wrong_title4 = QLabel(self)
        self.label_left_cam_wrong_title4.setText("")
        self.label_left_cam_wrong_title4.setFont(QFont("Times", 17))
        self.label_left_cam_wrong_title4.setFixedSize(200, 40)
        self.label_left_cam_wrong_title4.move(900, 40)

        self.label_left_cam_wrong4 = QLabel(self)
        self.label_left_cam_wrong4.setFont(QFont("Times", 28))
        self.label_left_cam_wrong4.setFixedSize(160, 120)
        self.label_left_cam_wrong4.move(840, 80)
        # self.label_left_cam_wrong4.setStyleSheet("border-image: url('3.png');")

        #############################第一排 end

        self.label_above_cam_wrong_title = QLabel(self)
        self.label_above_cam_wrong_title.setText("相机2实时图像")
        self.label_above_cam_wrong_title.setFont(QFont("Times", 17))
        self.label_above_cam_wrong_title.setFixedSize(200, 40)
        self.label_above_cam_wrong_title.move(110, 245)
        self.label_above_cam_wrong = QLabel(self)
        # self.label_above_cam_wrong.setText("实时图像")
        self.label_above_cam_wrong.setFont(QFont("Times", 28))
        self.label_above_cam_wrong.setFixedSize(260, 160)
        self.label_above_cam_wrong.move(50, 285)
        # self.label_above_cam_wrong.setStyleSheet("border-image: url('2.png');")

        self.label_front_cam_wrong_title = QLabel(self)
        self.label_front_cam_wrong_title.setText("相机2检测图像")
        self.label_front_cam_wrong_title.setFont(QFont("Times", 17))
        self.label_front_cam_wrong_title.setFixedSize(200, 40)
        self.label_front_cam_wrong_title.move(600, 245)

        self.label_front_cam_wrong_title1 = QLabel(self)
        self.label_front_cam_wrong_title1.setText("")
        self.label_front_cam_wrong_title1.setFont(QFont("Times", 17))
        self.label_front_cam_wrong_title1.setFixedSize(200, 40)
        self.label_front_cam_wrong_title1.move(390, 275)

        self.label_front_cam_wrong = QLabel(self)
        self.label_front_cam_wrong.setFont(QFont("Times", 28))
        self.label_front_cam_wrong.setFixedSize(160, 120)
        self.label_front_cam_wrong.move(330, 315)
        # self.label_front_cam_wrong.setStyleSheet("border-image: url('3.png');")

        self.label_front_cam_wrong_title2 = QLabel(self)
        self.label_front_cam_wrong_title2.setText("")
        self.label_front_cam_wrong_title2.setFont(QFont("Times", 17))
        self.label_front_cam_wrong_title2.setFixedSize(200, 40)
        self.label_front_cam_wrong_title2.move(555, 275)

        self.label_front_cam_wrong2 = QLabel(self)
        self.label_front_cam_wrong2.setFont(QFont("Times", 28))
        self.label_front_cam_wrong2.setFixedSize(160, 120)
        self.label_front_cam_wrong2.move(500, 315)
        # self.label_front_cam_wrong2.setStyleSheet("border-image: url('3.png');")

        self.label_front_cam_wrong_title3 = QLabel(self)
        self.label_front_cam_wrong_title3.setText("")
        self.label_front_cam_wrong_title3.setFont(QFont("Times", 17))
        self.label_front_cam_wrong_title3.setFixedSize(200, 40)
        self.label_front_cam_wrong_title3.move(725, 275)

        self.label_front_cam_wrong3 = QLabel(self)
        self.label_front_cam_wrong3.setFont(QFont("Times", 28))
        self.label_front_cam_wrong3.setFixedSize(160, 120)
        self.label_front_cam_wrong3.move(670, 315)
        # self.label_front_cam_wrong3.setStyleSheet("border-image: url('3.png');")

        self.label_front_cam_wrong_title4 = QLabel(self)
        self.label_front_cam_wrong_title4.setText("")
        self.label_front_cam_wrong_title4.setFont(QFont("Times", 17))
        self.label_front_cam_wrong_title4.setFixedSize(200, 40)
        self.label_front_cam_wrong_title4.move(900, 275)

        self.label_front_cam_wrong4 = QLabel(self)
        self.label_front_cam_wrong4.setFont(QFont("Times", 28))
        self.label_front_cam_wrong4.setFixedSize(160, 120)
        self.label_front_cam_wrong4.move(840, 315)
        # self.label_front_cam_wrong4.setStyleSheet("border-image: url('3.png');")

        self.real_labels = [
            self.label_above_cam_real,
            self.label_above_cam_wrong,
        ]
        self.defect_labels = [
            self.label_left_cam_wrong,
            self.label_left_cam_wrong2,
            self.label_left_cam_wrong3,
            self.label_left_cam_wrong4,
        ]
        self.defect_labels2 = [
            self.label_front_cam_wrong,
            self.label_front_cam_wrong2,
            self.label_front_cam_wrong3,
            self.label_front_cam_wrong4,
        ]
        # 相机2检查小图文字描述
        self.label_front_cam_wrong_titles = [
            self.label_front_cam_wrong_title1,
            self.label_front_cam_wrong_title2,
            self.label_front_cam_wrong_title3,
            self.label_front_cam_wrong_title4,
        ]
        # 相机1检查小图文字描述
        self.label_left_cam_wrong_titles = [
            self.label_left_cam_wrong_title1,
            self.label_left_cam_wrong_title2,
            self.label_left_cam_wrong_title3,
            self.label_left_cam_wrong_title4,
        ]

        #############################第二排 end
        self.current_time = QLabel(self)
        self.current_time.setText("2020-06-28 03:27:45")
        self.current_time.setFont(QFont("Roman times", 16, QFont.Bold))
        self.current_time.setFixedSize(380, 60)
        self.current_time.move(1050, 10)
        self.current_time.setStyleSheet("color:red")

        self.current_type = QLabel(self)
        self.current_type.setText("当前生产物料:")
        self.current_type.setFont(QFont("Times", 17))
        self.current_type.setFixedSize(150, 40)
        self.current_type.move(1050, 60)

        self.current_type_context = QLabel(self)
        # self.current_type_context.setText("707")
        self.current_type_context.setFont(QFont("Times", 17))
        self.current_type_context.setFixedSize(50, 40)
        self.current_type_context.move(1060, 60)
        self.current_type_context.setStyleSheet("color:red")

        self.rb707 = QRadioButton('624', self)
        self.rb707.setFont(QFont("Times", 17))
        self.rb707.setFixedSize(60, 40)
        self.rb707.move(1220, 60)
        self.rb707.setChecked(True)
        # self.rb707.toggled.connect(lambda: self.send_exType(self.rb707.text()))
        self.rb875 = QRadioButton('625', self)
        self.rb875.setFont(QFont("Times", 17))
        self.rb875.setFixedSize(60, 40)
        self.rb875.move(1300, 60)
        # self.rb875.setChecked(True)
        # self.bg1 = QButtonGroup(self)
        # self.bg1.addButton(self.rb707, 707)
        # self.bg1.addButton(self.rb875, 875)
        # self.bg1.buttonClicked.connect(self.send_exType)

        self.buttom_set_param = QPushButton(self)
        self.buttom_set_param.setText("保存数据")
        self.buttom_set_param.setFont(QFont("Times", 15))
        self.buttom_set_param.setFixedSize(90, 40)
        self.buttom_set_param.move(1060, 110)
        self.buttom_set_param.clicked.connect(lambda: self.save_data())

        self.buttom_clear_data = QPushButton(self)
        self.buttom_clear_data.setText("清除数据")
        self.buttom_clear_data.setFont(QFont("Times", 15))
        self.buttom_clear_data.setFixedSize(90, 40)
        self.buttom_clear_data.move(1160, 110)
        self.buttom_clear_data.clicked.connect(lambda: self.clear_data())

        self.buttom_new_tray = QPushButton(self)
        self.buttom_new_tray.setText("设置参数")
        self.buttom_new_tray.setFont(QFont("Times", 15))
        self.buttom_new_tray.setFixedSize(90, 40)
        self.buttom_new_tray.move(1260, 110)
        self.buttom_new_tray.clicked.connect(self.do_btn)

        # self.button_test_link = QPushButton(self)
        # self.button_test_link.setText("测试设备")
        # self.button_test_link.setFont(QFont("Times", 15))
        # self.button_test_link.setFixedSize(80, 40)
        # self.button_test_link.move(1830, 10)

        self.label_show_wrong_num_title = QLabel(self)
        self.label_show_wrong_num_title.setText("检测统计")
        self.label_show_wrong_num_title.setFont(QFont("Times", 17))
        self.label_show_wrong_num_title.setFixedSize(270, 40)
        self.label_show_wrong_num_title.move(1060, 170)

        self.temp_num_all_title = QLabel(self)
        self.temp_num_all_title.move(1050, 220 - 6)
        self.temp_num_all_title.setFixedSize(100, 40)
        self.temp_num_all_title.setText("生产总数:")
        self.temp_num_all_title.setFont(QFont("Times", 16))
        self.temp_num_all_title.setAlignment(Qt.AlignRight)

        self.temp_num_all = QLabel(self)
        # self.temp_num_all.move(1160, 215)
        self.temp_num_all.move(1160, 220)
        self.temp_num_all.setFixedSize(150, 40)
        self.temp_num_all.setText('0')
        self.temp_num_all.setFont(QFont("Times", 16))
        self.temp_num_all.setAlignment(Qt.AlignLeft)

        self.ok_num_title = QLabel(self)
        self.ok_num_title.move(1050, 260 - 5)
        self.ok_num_title.setFixedSize(100, 40)
        self.ok_num_title.setText("良品数量:")
        self.ok_num_title.setFont(QFont("Times", 16))
        self.ok_num_title.setAlignment(Qt.AlignRight)

        self.ok_num = QLabel(self)
        # self.ok_num.move(1160, 255)
        self.ok_num.move(1160, 260)
        self.ok_num.setFixedSize(150, 40)
        self.ok_num.setText('0')
        self.ok_num.setFont(QFont("Times", 16))
        self.ok_num.setAlignment(Qt.AlignLeft)

        self.ok_rate_title = QLabel(self)
        self.ok_rate_title.move(1050, 300 - 6)
        self.ok_rate_title.setFixedSize(100, 40)
        self.ok_rate_title.setText("检测良率:")
        self.ok_rate_title.setFont(QFont("Times", 16))
        self.ok_rate_title.setAlignment(Qt.AlignRight)

        self.ok_rate = QLabel(self)
        self.ok_rate.move(1160, 300)
        self.ok_rate.setFixedSize(150, 40)
        self.ok_rate.setText('0.0%')
        self.ok_rate.setFont(QFont("Times", 16))
        self.ok_rate.setAlignment(Qt.AlignLeft)

        self.list_label_wrong_number = []
        self.list_temp_statics_rate = []

        for defect in DEFECTS:
            if defect is DEFECTS.LIANGPIN:
                continue
            temp_num_left = QLabel(self)
            temp_num_left.move(1050, 300 + defect.key * 40 - 6)
            temp_num_left.setFixedSize(100, 40)
            temp_num_left.setText('%s:' % defect.desc)
            temp_num_left.setFont(QFont("Times", 16))
            temp_num_left.setAlignment(Qt.AlignRight)

            temp_statics_number = QLabel(self)
            temp_statics_number.move(1160, (300 + defect.key * 40))
            temp_statics_number.setFixedSize(100, 40)
            temp_statics_number.setFont(QFont("Times", 16))
            temp_statics_number.setText('1')
            temp_statics_number.setAlignment(Qt.AlignLeft)

            temp_statics_rate = QLabel(self)
            temp_statics_rate.move(1260, 300 + defect.key * 40)
            temp_statics_rate.setFixedSize(150, 40)
            temp_statics_rate.setFont(QFont("Times", 16))
            temp_statics_rate.setText('0.0%')
            temp_statics_rate.setAlignment(Qt.AlignLeft)
            self.list_label_wrong_number.append(temp_statics_number)
            self.list_temp_statics_rate.append(temp_statics_rate)

        self.repairable_title = QLabel(self)
        self.repairable_title.move(1050, (300 + len(DEFECTS) * 40) - 6)
        self.repairable_title.setFixedSize(100, 40)
        self.repairable_title.setText("可返修:")
        self.repairable_title.setFont(QFont("Times", 16))
        self.repairable_title.setAlignment(Qt.AlignRight)

        self.repairable_num = QLabel(self)
        self.repairable_num.move(1160, 300 + len(DEFECTS) * 40)
        self.repairable_num.setFixedSize(100, 40)
        self.repairable_num.setText('0')
        self.repairable_num.setFont(QFont("Times", 16))
        self.repairable_num.setAlignment(Qt.AlignLeft)

        self.repairable_num_rate = QLabel(self)
        self.repairable_num_rate.move(1260, 300 + len(DEFECTS) * 40)
        self.repairable_num_rate.setFixedSize(150, 40)
        self.repairable_num_rate.setFont(QFont("Times", 16))
        self.repairable_num_rate.setText('0.0%')
        self.repairable_num_rate.setAlignment(Qt.AlignLeft)

        self.non_repairable_title = QLabel(self)
        self.non_repairable_title.move(1050, 340 + len(DEFECTS) * 40 - 20)
        self.non_repairable_title.setFixedSize(100, 40)
        self.non_repairable_title.setText("不可返修:")
        self.non_repairable_title.setFont(QFont("Times", 16))
        self.non_repairable_title.setAlignment(Qt.AlignRight)

        self.non_repairable_num = QLabel(self)
        self.non_repairable_num.move(1160, 340 + len(DEFECTS) * 40 - 13)
        self.non_repairable_num.setFixedSize(100, 40)
        self.non_repairable_num.setText('0')
        self.non_repairable_num.setFont(QFont("Times", 16))
        self.non_repairable_num.setAlignment(Qt.AlignLeft)

        self.non_repairable_num_rate = QLabel(self)
        self.non_repairable_num_rate.move(1260, 340 + len(DEFECTS) * 40 - 13)
        self.non_repairable_num_rate.setFixedSize(150, 40)
        self.non_repairable_num_rate.setFont(QFont("Times", 16))
        self.non_repairable_num_rate.setText('0.0%')
        self.non_repairable_num_rate.setAlignment(Qt.AlignLeft)
        ############# 右下 end

        #########################################################1111111
        # 0712修改move参数
        self.down_wrong_1_title = QLabel(self)
        self.down_wrong_1_title.move(110, 490)
        self.down_wrong_1_title.setFixedSize(150, 50)
        self.down_wrong_1_title.setFont(QFont("Times", 15))
        self.down_wrong_1_title.setText("")

        self.down_wrong_1_img = QLabel(self)
        self.down_wrong_1_img.move(50, 520)
        self.down_wrong_1_img.setFixedSize(200, 160)
        # self.down_wrong_1_img.setStyleSheet("border-image: url(3.png);")
        #########################################################22222222
        self.down_wrong_2_title = QLabel(self)
        self.down_wrong_2_title.move(345, 490)
        self.down_wrong_2_title.setFixedSize(150, 50)
        self.down_wrong_2_title.setFont(QFont("Times", 15))
        self.down_wrong_2_title.setText("")

        self.down_wrong_2_img = QLabel(self)
        self.down_wrong_2_img.move(290, 520)
        self.down_wrong_2_img.setFixedSize(200, 160)
        # self.down_wrong_2_img.setStyleSheet("border-image: url(3.png);")

        #########################################################33333333333
        self.down_wrong_3_title = QLabel(self)
        self.down_wrong_3_title.move(585, 490)
        self.down_wrong_3_title.setFixedSize(150, 50)
        self.down_wrong_3_title.setFont(QFont("Times", 15))
        self.down_wrong_3_title.setText("")

        self.down_wrong_3_img = QLabel(self)
        self.down_wrong_3_img.move(530, 520)
        self.down_wrong_3_img.setFixedSize(200, 160)
        # self.down_wrong_3_img.setStyleSheet("border-image: url(3.png);")

        #########################################################4444444444
        self.down_wrong_4_title = QLabel(self)
        self.down_wrong_4_title.move(825, 490)
        self.down_wrong_4_title.setFixedSize(150, 50)
        self.down_wrong_4_title.setFont(QFont("Times", 15))
        self.down_wrong_4_title.setText("")

        self.down_wrong_4_img = QLabel(self)
        self.down_wrong_4_img.move(770, 520)
        self.down_wrong_4_img.setFixedSize(200, 160)
        # self.down_wrong_4_img.setStyleSheet("border-image: url(3.png);")

        self.down_wrong = [
            self.down_wrong_1_img,
            self.down_wrong_2_img,
            self.down_wrong_3_img,
            self.down_wrong_4_img,
        ]
        self.down_wrong_title = [
            self.down_wrong_1_title,
            self.down_wrong_2_title,
            self.down_wrong_3_title,
            self.down_wrong_4_title,
        ]
        # self.down_wrong_4_date = QLabel(self)
        # self.down_wrong_4_date.move(1270, 920)
        # self.down_wrong_4_date.setFixedSize(100, 50)
        # self.down_wrong_4_date.setFont(QFont("Times", 15))
        # self.down_wrong_4_date.setText("2019-21-12")
        ################################################################

        self.buttom_first_page = QPushButton(self)
        self.buttom_first_page.setText("第一页")
        self.buttom_first_page.setFont(QFont("Times", 9))
        self.buttom_first_page.setFixedSize(80, 30)
        self.buttom_first_page.move(400, 678)
        self.buttom_first_page.clicked.connect(lambda: self.page_of_num1())

        self.buttom_previous_page = QPushButton(self)
        self.buttom_previous_page.setText("前一页")
        self.buttom_previous_page.setFont(QFont("Times", 9))
        self.buttom_previous_page.setFixedSize(80, 30)
        self.buttom_previous_page.move(490, 678)
        self.buttom_previous_page.clicked.connect(lambda: self.page_of_num2())

        self.buttom_next_page = QPushButton(self)
        self.buttom_next_page.setText("后一页")
        self.buttom_next_page.setFont(QFont("Times", 9))
        self.buttom_next_page.setFixedSize(80, 30)
        self.buttom_next_page.move(580, 678)
        self.buttom_next_page.clicked.connect(lambda: self.page_of_num3())

        self.buttom_last_page = QPushButton(self)
        self.buttom_last_page.setText("最后一页")
        self.buttom_last_page.setFont(QFont("Times", 9))
        self.buttom_last_page.setFixedSize(80, 30)
        self.buttom_last_page.move(670, 678)
        self.buttom_last_page.clicked.connect(lambda: self.page_of_num4())
        ################################################################

    def hideDiv(self):
        for i in self.down_wrong_title:
            i.hide()
        for i in self.down_wrong:
            i.hide()

    def page_of_num1(self):
        self.hideDiv()
        self.wrong_lenghts = 1
        for i in range(4):
            if len(self.file_array) > i:
                self.down_wrong[i].show()
                self.down_wrong_title[i].show()
                self.down_wrong[i].setPixmap(self.file_array[len(self.file_array) - (i + 1)])
                self.down_wrong_title[i].setText(str(self.type_array[len(self.file_array) - (i + 1)]))

    # 前一页

    def page_of_num2(self):
        if self.wrong_lenghts > 1:
            self.hideDiv()
            tot = self.wrong_lenghts - 1
            wrong_num = len(self.file_array) - int(tot) * 4 - 1
            if len(self.file_array) > wrong_num:
                self.wrong_lenghts = tot
                for i in range(4):
                    num = wrong_num + 1
                    if len(self.file_array) >= num:
                        self.down_wrong[i].show()
                        self.down_wrong_title[i].show()
                        self.down_wrong[i].setPixmap(self.file_array[num + 3 + i])
                        self.down_wrong_title[i].setText(str(self.type_array[num + 3 - i]))

        # 后一页

    def page_of_num3(self):
        if self.wrong_lenghts < math.ceil(len(self.file_array) / 4):
            self.hideDiv()
            tot = self.wrong_lenghts + 1
            wrong_num = len(self.file_array) - self.wrong_lenghts * 4 - 1
            if len(self.file_array) > wrong_num:
                for i in range(4):
                    num = wrong_num
                    if len(self.file_array) >= num and num - i >= 0:
                        self.wrong_lenghts = tot
                        self.down_wrong[i].show()
                        self.down_wrong_title[i].show()
                        self.down_wrong[i].setPixmap(self.file_array[num - i])
                        self.down_wrong_title[i].setText(str(self.type_array[num - i]))

        # 最后一页

    def page_of_num4(self):
        self.hideDiv()
        tot = math.ceil(len(self.file_array) / 4)
        self.wrong_lenghts = tot
        wrong_num = len(self.file_array) - (self.wrong_lenghts - 1) * 4 - 1
        for i in range(4):

            if len(self.file_array) >= wrong_num:
                if wrong_num - i > -1:
                    self.down_wrong[i].show()
                    self.down_wrong_title[i].show()
                    self.down_wrong[i].setPixmap(self.file_array[wrong_num - i])
                    self.down_wrong_title[i].setText(str(self.type_array[wrong_num - i]))


class MyWindow2(QWidget):
    '''自定义窗口'''
    # 知识点：
    # 1.为了得到返回值用到了自定义的信号/槽
    # 2.为了显示动态数字，使用了计时器

    def __init__(self):
        super().__init__()
        self.singleton = GolbalSingleton()
        self.redis_db = self.singleton.conn_redis()
        self.lay = QFormLayout()
        self.setLayout(self.lay)

        self.cam0_zangwu_flag_label = QLabel('相机0脏污检测')
        self.cam0_zangwu_flag_btn1 = QRadioButton('开启')
        self.cam0_zangwu_flag_btn2 = QRadioButton('关闭')
        if int(self.redis_db.get('cam0_zangwu_flag'))==0:
            self.cam0_zangwu_flag_btn1.setChecked(True)
        else:
            self.cam0_zangwu_flag_btn2.setChecked(True)

        self.cam0_zangwu_flag_h = QHBoxLayout()
        self.cam0_zangwu_flag_h.addWidget(self.cam0_zangwu_flag_btn1)
        self.cam0_zangwu_flag_h.addWidget(self.cam0_zangwu_flag_btn2)
        self.cam0_zangwu_flag_h1 = QButtonGroup()
        self.cam0_zangwu_flag_h1.addButton(self.cam0_zangwu_flag_btn1)
        self.cam0_zangwu_flag_h1.addButton(self.cam0_zangwu_flag_btn2)
        self.lay.addRow(self.cam0_zangwu_flag_label, self.cam0_zangwu_flag_h)

        self.cam1_zangwu_flag_label = QLabel('相机1脏污检测')
        self.cam1_zangwu_flag_btn1 = QRadioButton('开启')
        self.cam1_zangwu_flag_btn2 = QRadioButton('关闭')
        if int(self.redis_db.get('cam1_zangwu_flag'))==0:
            self.cam1_zangwu_flag_btn1.setChecked(True)
        else:
            self.cam1_zangwu_flag_btn2.setChecked(True)

        self.cam1_zangwu_flag_h = QHBoxLayout()
        self.cam1_zangwu_flag_h.addWidget(self.cam1_zangwu_flag_btn1)
        self.cam1_zangwu_flag_h.addWidget(self.cam1_zangwu_flag_btn2)
        self.cam1_zangwu_flag_h1 = QButtonGroup()
        self.cam1_zangwu_flag_h1.addButton(self.cam1_zangwu_flag_btn1)
        self.cam1_zangwu_flag_h1.addButton(self.cam1_zangwu_flag_btn2)

        self.lay.addRow(self.cam1_zangwu_flag_label, self.cam1_zangwu_flag_h)

        self.cam1_detect_circle_label = QLabel('相机1孔异常检测')
        self.cam1_detect_circle_btn1 = QRadioButton('开启')
        self.cam1_detect_circle_btn2 = QRadioButton('关闭')
        if int(self.redis_db.get('cam1_detect_circle'))==0:
            self.cam1_detect_circle_btn1.setChecked(True)
        else:
            self.cam1_detect_circle_btn2.setChecked(True)

        self.cam1_detect_circle_h = QHBoxLayout()
        self.cam1_detect_circle_h.addWidget(self.cam1_detect_circle_btn1)
        self.cam1_detect_circle_h.addWidget(self.cam1_detect_circle_btn2)
        self.cam1_detect_circle_h1 = QButtonGroup()
        self.cam1_detect_circle_h1.addButton(self.cam1_detect_circle_btn1)
        self.cam1_detect_circle_h1.addButton(self.cam1_detect_circle_btn2)
        self.lay.addRow(self.cam1_detect_circle_label, self.cam1_detect_circle_h)

        self.cam1_maoci_flag_label = QLabel('相机1毛刺检测')
        self.cam1_maoci_flag_btn1 = QRadioButton('开启')
        self.cam1_maoci_flag_btn2 = QRadioButton('关闭')
        if int(self.redis_db.get('cam1_maoci_flag'))==0:
            self.cam1_maoci_flag_btn1.setChecked(True)
        else:
            self.cam1_maoci_flag_btn2.setChecked(True)

        self.cam1_maoci_flag_h = QHBoxLayout()
        self.cam1_maoci_flag_h.addWidget(self.cam1_maoci_flag_btn1)
        self.cam1_maoci_flag_h.addWidget(self.cam1_maoci_flag_btn2)
        self.cam1_maoci_flag_h1 = QButtonGroup()
        self.cam1_maoci_flag_h1.addButton(self.cam1_maoci_flag_btn1)
        self.cam1_maoci_flag_h1.addButton(self.cam1_maoci_flag_btn2)
        self.lay.addRow(self.cam1_maoci_flag_label, self.cam1_maoci_flag_h)

        self.cam1_moque_flag_label = QLabel('相机1膜缺检测')
        self.cam1_moque_flag_btn1 = QRadioButton('开启')
        self.cam1_moque_flag_btn2 = QRadioButton('关闭')
        if int(self.redis_db.get('cam1_moque_flag'))==0:
            self.cam1_moque_flag_btn1.setChecked(True)
        else:
            self.cam1_moque_flag_btn2.setChecked(True)

        self.cam1_moque_flag_h = QHBoxLayout()
        self.cam1_moque_flag_h.addWidget(self.cam1_moque_flag_btn1)
        self.cam1_moque_flag_h.addWidget(self.cam1_moque_flag_btn2)
        self.cam1_moque_flag_h1 = QButtonGroup()
        self.cam1_moque_flag_h1.addButton(self.cam1_moque_flag_btn1)
        self.cam1_moque_flag_h1.addButton(self.cam1_moque_flag_btn2)
        self.lay.addRow(self.cam1_moque_flag_label, self.cam1_moque_flag_h)

        self.cam1_mohuashang_flag_label = QLabel('相机1膜划伤检测')
        self.cam1_mohuashang_flag_btn1 = QRadioButton('开启')
        self.cam1_mohuashang_flag_btn2 = QRadioButton('关闭')
        if int(self.redis_db.get('cam1_mohuashang_flag'))==0:
            self.cam1_mohuashang_flag_btn1.setChecked(True)
        else:
            self.cam1_mohuashang_flag_btn2.setChecked(True)

        self.cam1_mohuashang_flag_h = QHBoxLayout()
        self.cam1_mohuashang_flag_h.addWidget(self.cam1_mohuashang_flag_btn1)
        self.cam1_mohuashang_flag_h.addWidget(self.cam1_mohuashang_flag_btn2)
        self.cam1_mohuashang_flag_h1 = QButtonGroup()
        self.cam1_mohuashang_flag_h1.addButton(self.cam1_mohuashang_flag_btn1)
        self.cam1_mohuashang_flag_h1.addButton(self.cam1_mohuashang_flag_btn2)
        self.lay.addRow(self.cam1_mohuashang_flag_label, self.cam1_mohuashang_flag_h)

        self.cam1_moyashang_flag_label = QLabel('相机1膜压伤检测')
        self.cam1_moyashang_flag_btn1 = QRadioButton('开启')
        self.cam1_moyashang_flag_btn2 = QRadioButton('关闭')
        if int(self.redis_db.get('cam1_moyashang_flag'))==0:
            self.cam1_moyashang_flag_btn1.setChecked(True)
        else:
            self.cam1_moyashang_flag_btn2.setChecked(True)

        self.cam1_moyashang_flag_h = QHBoxLayout()
        self.cam1_moyashang_flag_h.addWidget(self.cam1_moyashang_flag_btn1)
        self.cam1_moyashang_flag_h.addWidget(self.cam1_moyashang_flag_btn2)
        self.cam1_moyashang_flag_h1 = QButtonGroup()
        self.cam1_moyashang_flag_h1.addButton(self.cam1_moyashang_flag_btn1)
        self.cam1_moyashang_flag_h1.addButton(self.cam1_moyashang_flag_btn2)
        self.lay.addRow(self.cam1_moyashang_flag_label, self.cam1_moyashang_flag_h)

        self.ok_btn = QPushButton('提交')
        self.cancel_btn = QPushButton('取消')
        self.ok_btn.clicked.connect(lambda: self.update())
        self.cancel_btn.clicked.connect(self.stopTimer)
        self.lay_h1 = QHBoxLayout()
        self.lay_h1.addWidget(self.ok_btn)
        self.lay_h1.addStretch()
        self.lay_h1.addWidget(self.cancel_btn)
        self.lay.addRow(self.lay_h1)

    def update(self):
        try:
            self.redis_db.set('cam0_zangwu_flag', 0 if self.cam0_zangwu_flag_btn1.isChecked() == True else 1)
            self.redis_db.set('cam1_zangwu_flag', 0 if self.cam1_zangwu_flag_btn1.isChecked() == True else 1)
            self.redis_db.set('cam1_detect_circle', 0 if self.cam1_detect_circle_btn1.isChecked() == True else 1)
            self.redis_db.set('cam1_maoci_flag', 0 if self.cam1_maoci_flag_btn1.isChecked() == True else 1)
            self.redis_db.set('cam1_moque_flag', 0 if self.cam1_moque_flag_btn1.isChecked() == True else 1)
            self.redis_db.set('cam1_mohuashang_flag', 0 if self.cam1_mohuashang_flag_btn1.isChecked() == True else 1)
            self.redis_db.set('cam1_moyashang_flag', 0 if self.cam1_moyashang_flag_btn1.isChecked() == True else 1)
            self.close()
        except Exception as e:
            print(e)

    def stopTimer(self):
        self.close()  # 然后窗口关闭

    # 默认关闭事件
    def closeEvent(self, e):
        self.stopTimer()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # run_by_time = int(sys.argv[1])
    run_by_time = 0
    # logger = logging_info.set_logger(config['log_dir'], os.path.basename(__file__))
    logger = None
    work = UI(logger, run_by_time)
    work.show()
    # work.showFullScreen()
    sys.exit(app.exec_())
