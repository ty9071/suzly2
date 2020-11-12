# -*- coding:utf8 -*-

from queue import Queue
import threading
from config import config
import requests
import sys
import struct
import base64
import json
import shutil
import pdb
import io
from PIL import Image
import numpy as np
import cv2
from ctypes import *
import time
from utils import QueueManager
import copy
from multiprocessing.managers import BaseManager

#os.system('taskset -p 64 %d' % os.getpid())

class QueueFounder:
    def __init__(self):
#        self.server_addr = config['queue_server']
        self.server_addr = '0.0.0.0'
        self.connectShow()
        self.connectObj()
        self.connectRet()
        self.connectButton()
        self.connectCapture()
        print('connected done')
        

    def connectCapture(self):
        # capture queue, for plc control 
        self.connectedCapture = True
        #server_addr = '0.0.0.0'
        server_addr = self.server_addr 
        # 检测结果队列
        self.capture_queue = Queue()
        QueueManager.register('capture', callable = lambda: self.capture_queue)
        cambar_manager = QueueManager(address=(server_addr, 9110), authkey= b'dihuge')
        try:
            cambar_manager.start()
        except Exception as e:
            print(e)
            cambar_manager.connect()
        self.capture = cambar_manager.capture()

    def connectShow(self):
        # 显示图像队列
        self.connectedCamShow = True
        #server_addr = '0.0.0.0'
        server_addr = self.server_addr 
        # 检测结果队列
        self.show_queue = Queue()
        QueueManager.register('show', callable = lambda: self.show_queue)
        cambar_manager = QueueManager(address=(server_addr, 9111), authkey= b'dihuge')
        try:
            cambar_manager.start()
        except Exception as e:
            print(e)
            cambar_manager.connect()
        self.show = cambar_manager.show()

    def connectObj(self):
        # 显示图像队列
        self.connectedObj = True
        #server_addr = '0.0.0.0'
        server_addr = self.server_addr 
        # 检测结果队列
        self.obj_queue_0 = Queue()
        self.obj_queue_1 = Queue()
        self.obj_queue_2 = Queue()
        self.obj_queue_3 = Queue()
        self.obj_queue_4 = Queue()
        self.obj_queue_5 = Queue()
        QueueManager.register('obj_0', callable = lambda: self.obj_queue_0)
        QueueManager.register('obj_1', callable = lambda: self.obj_queue_1)
        QueueManager.register('obj_2', callable = lambda: self.obj_queue_2)
        QueueManager.register('obj_3', callable = lambda: self.obj_queue_3)
        QueueManager.register('obj_4', callable = lambda: self.obj_queue_4)
        QueueManager.register('obj_5', callable = lambda: self.obj_queue_5)
        cambar_manager = QueueManager(address=(server_addr, 9112), authkey= b'dihuge')
        try:
            cambar_manager.start()
        except Exception as e:
            print(e)
            cambar_manager.connect()
        self.obj_0 = cambar_manager.obj_0()
        self.obj_1 = cambar_manager.obj_1()
        self.obj_2 = cambar_manager.obj_2()
        self.obj_3 = cambar_manager.obj_3()
        self.obj_4 = cambar_manager.obj_4()
        self.obj_5 = cambar_manager.obj_5()

    def connectRet(self):
        # 结果队列
        self.connectedRet = True
        #server_addr = '0.0.0.0'
        server_addr = self.server_addr 
        # 检测结果队列
        self.ret_queue = Queue()
        QueueManager.register('result', callable = lambda: self.ret_queue)
        camcolor_manager = QueueManager(address=(server_addr, 9113), authkey= b'dihuge')
        try:
            camcolor_manager.start()
        except Exception as e:
            print(e)
            camcolor_manager.connect()
        self.ret_sender = camcolor_manager.result()

    def connectButton(self):
        # 操作信息
        self.connectedButton = True
        #server_addr = '0.0.0.0'
        server_addr = self.server_addr 
        # 检测结果队列
        self.button_queue = Queue()
        QueueManager.register('button_type', callable = lambda: self.button_queue)
        button_manager = QueueManager(address=(server_addr, 9114), authkey= b'dihuge')
        try:
            button_manager.start()
        except Exception as e:
            print(e)
            button_manager.connect()
        self.button_type_sender =button_manager.button_type()

    def run(self):
        while True:
            if self.capture_queue.qsize() > 20:
                self.capture_queue.get()
            if self.show_queue.qsize() > 20:
                self.show_queue.get()
            if self.obj_queue_0.qsize() > 20:
                self.obj_queue_0.get()
            if self.obj_queue_1.qsize() > 20:
                self.obj_queue_1.get()
            if self.obj_queue_2.qsize() > 20:
                self.obj_queue_2.get()
            if self.obj_queue_3.qsize() > 20:
                self.obj_queue_3.get()
            if self.obj_queue_4.qsize() > 20:
                self.obj_queue_4.get()
            if self.obj_queue_5.qsize() > 20:
                self.obj_queue_5.get()
            if self.button_queue.qsize() > 20:
                self.button_queue.get()
#            if self.bar_image_sender_small.qsize() > 20:
#                self.bar_image_sender_small.get()
            time.sleep(3)

if __name__ == '__main__':
    qf = QueueFounder()
    qf.run()
