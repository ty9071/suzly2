import os
import importlib
import utils
import sys
from utils import QueueManager
import time
import logging_info
import pdb
import numpy as np
import cv2
from config import config
from threading import Thread


class Detector(object):
    def __init__(self, camId, model_types, mesh_settings, liner_settings, logger):
        self.logger = logger
        self.logger.info('Start')
        self.camId = camId
        self.server_addr = '0.0.0.0'
        # 物料标识，可以从界面选择
        self.model_type = '624'

        defect_module = importlib.import_module('defect_seperate_%d' % camId)
        self.defect_worker = defect_module.Worker(model_types, mesh_settings, liner_settings, self.camId)

        # object queue, for detect
        self.connectedObj = False
        self.connectObj()
        # result queue
        self.connectedRet = False
        self.connectRet()
        # show queue
        self.connectedShow = False
        self.connectShow()
        print('init done')

    def connectShow(self):
        while self.connectedShow == False:
            try:
                QueueManager.register('show')
                manager = QueueManager(address=(self.server_addr, 9111), authkey=b'dihuge')
                manager.connect()
                self.show_sender = manager.show()
                self.connectedShow = True
            except Exception as e:
                print('show_ConnectRefuseRec', e)
                time.sleep(1)

    def connectRet(self):
        while self.connectedRet == False:
            try:
                QueueManager.register('result')
                manager = QueueManager(address=(self.server_addr, 9113), authkey=b'dihuge')
                manager.connect()
                self.ret_sender = manager.result()
                self.connectedRet = True
            except Exception as e:
                print('Ret_ConnectRefuseRec', e)
                time.sleep(1)

    def connectObj(self):
        while self.connectedObj == False:
            try:
                # color result queue
                QueueManager.register('obj_%d' % self.camId)
                manager = QueueManager(address=(self.server_addr, 9112), authkey=b'dihuge')
                manager.connect()
                # camNum = config['cameras']['camNum']
                # for i in range(camNum):
                #     if self.camId == i:
                #         self.obj_sender = eval("manager.obj_%s"%(i)())
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

    def run(self):
        while True:
            if self.obj_sender.qsize() > 0:
                print("detect rec")
                obj_dict = self.obj_sender.get()
                ret_dict = self.defect_worker.detect(obj_dict, self.model_type)
                shape_img = np.shape(ret_dict['image'])
                idx = ret_dict['idx']
                result = ret_dict['result']
                defect = ret_dict['defect']
                trig_count = ret_dict['trig_count']
                # side = ret_dict['side']
                ret_dict['type'] = 'image_defect'
                ret_dict['camId'] = self.camId
                batch_count = ret_dict['batch_count']
                # print('result', ret_dict['row_idx'], ret_dict['side'], ret_dict['result'])

                # # 将所有obj小图存下来
                # cv2.imwrite(config['defect_dir'] + str(self.camId) + '_' + str(trig_count) + '_' + str(idx) + '.png', ret_dict['image'])
                while self.show_sender.qsize() > 15:
                    print('show sender full', self.show_sender.qsize())
                    self.show_sender.get()
                self.show_sender.put(ret_dict)

                while self.ret_sender.qsize() > 15:
                    print('ret sender full', self.ret_sender.qsize())
                    self.ret_sender.get()
                send_dict = {'camId': self.camId, 'trig_count': trig_count, 'batch_count': batch_count,
                             'result': result, 'idx': idx,
                             'defect': defect}
                # for key, val in ret_dict.items():
                #     if key == 'image':
                #         continue

                self.ret_sender.put(send_dict)
                # f = open('test.txt', 'w+')
                # f.write(str(send_dict['trig_count']))
                # f.close
                print('ret_sender_qsize', self.ret_sender.qsize())
            else:
                time.sleep(0.05)


if __name__ == '__main__':
    # f = open('test.txt', 'w+')
    # f.write("hello\n")
    # f.close
    camId = int(sys.argv[1])
    model_types = ['624']
    logger = logging_info.set_logger(config['log_dir'], os.path.basename(__file__) + '_%d' % camId)
    mesh_settings = utils.load_mesh_settings(model_types)
    liner_settings = utils.load_liner_settings(model_types)
    detector = Detector(camId, model_types, mesh_settings, liner_settings, logger)
    detector.run()
