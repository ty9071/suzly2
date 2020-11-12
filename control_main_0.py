import os
from utils import QueueManager
import time
import logging_info
import pdb
import numpy as np
import cv2
from config import config
from threading import Thread
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import serial


class Controller(object):
    def __init__(self, logger):
        self.logger = logger
        self.logger.info('Start')
        self.buf_qsize = -1
        self.first_capture = True 
        
        self.trig_count = 0

        # counter
        self.robot_gap_to_above = 15
        self.robot_gap_to_mid = None
        self.left_list = [-1 for i in range(0,self.robot_gap_to_above)]
        self.right_list = [-1 for i in range(0,self.robot_gap_to_above)]
        self.robot_index = self.robot_gap_to_above - 1

        # buffer
        # 根据料带特点和相机排布初始化参数，后续放到config中去
        self.dis_1 = 12 # 分拣工位到第0个相机（最远）的排数（参考文档）
        self.dis_2 = 9 # 第1个相机到第0个相机（最远）的排数（参考文档）
        self.line_belt = 2 # 料带每排列数
        self.cam_num = 2 # 相机的个数，每一个相机要有一个放结果的位置

        # 初始化要更新的参数
        self.index_cam0 = 0 # 以左边一个位置为基准，右边一个位置隔一行所以要加2
        self.index_cam1 = self.dis_2 # 以左边一个位置为基准，右边一个位置隔一行所以要加2
        self.index_pick = self.dis_1 - 2 # 以左边一个位置为基准，右边一个位置隔一行所以要加2

        self.buffer_size = self.dis_1 + 1
        self.ret_buffer = []
        for i in range(self.buffer_size):
            #            self.ret_buffer.append([0, 0])
            #            self.ret_buffer.append([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            tmp_none = []
            for j in range(self.cam_num * self.line_belt):
                tmp_none.append(None)
            self.ret_buffer.append(tmp_none)
        print(self.ret_buffer)

        self.result_dict = {
            'DEFECTS.LIANGPIN':0,
        }
        self.server_addr = '0.0.0.0'
        # capture flag queue
        self.connectedCapture = False
        self.connectCapture()
        # result queue
        self.connectedRet = False
        self.connectRet()

        # plc
        if config['LOCAL_IMAGE'] == False:
            self.connectPlc()

        # capture thraeth
        th = Thread(target=self.capture_control, args=())
        th.setDaemon(True)
        th.start()

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
            self.plc_client = master
            # client = ModbusClient(method="rtu",
            #                       port=config['plc_modbus']['port'],
            #                       stopbits=config['plc_modbus']['stopbits'],
            #                       bytesize=config['plc_modbus']['bytesize'],
            #                       parity=config['plc_modbus']['parity'],
            #                       baudrate=config['plc_modbus']['baudrate'])
            # cli_connection = client.connect()
            # self.plc_client = client
        except Exception as exc:
            print(str(exc))

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


    # # {'camId':self.camId,'trig_count':trig_count, 'result':result,'idx':idx,}
    # def buffer_update(self):
    #     # 不用等够8个结果，来一个结果存一个结果
    #     while True:
    #         if self.ret_sender.qsize() >= 0:  # 来一个结果存一个结果
    #             self.index_str = (self.index_str - self.step_next) % self.dis_1
    #             self.index_end = (self.index_end - self.step_next) % self.dis_1
    #             step_next_updata_count = 0
    #             # f = open('test.txt', 'w+')
    #             # f.write(self.ret_sender.qsize())
    #             # f.close
    #             aaa = aaa + 1
    #             while self.ret_sender.qsize() > 0:
    #                 cam_ret = self.ret_sender.get()
    #                 if step_next_updata_count == 0:
    #                     if (cam_ret['trig_count'] % 2) == 1:
    #                         self.step_next = 1
    #                     else:
    #                         self.step_next = 3
    #                     step_next_updata_count = 1
    #                 camId = cam_ret['camId']
    #                 idx = cam_ret['idx']
    #                 result = cam_ret['result'].value # 要在config中把result的赋值范围设置成0,1,2
    #                 if camId == 0:
    #                     self.ret_buffer[self.index_str + (idx // 2 * 2)][idx % 2] = max(result,
    #                                                                                     self.ret_buffer[
    #                                                                                         self.index_str + (
    #                                                                                                 idx // 2 * 2)][
    #                                                                                         idx % 2])
    #                 elif camId == 1:
    #                     self.ret_buffer[self.index_str + dis_2 + (idx // 2 * 2)][idx % 2] = max(result,
    #                                                                                             self.ret_buffer[
    #                                                                                                 self.index_str + dis_2 + (
    #                                                                                                         idx // 2 * 2)][
    #                                                                                                 idx % 2])
    #             # 先把当前的下一步要分拣的结果发给PLC，再更新下下一步要分拣的结果,那样更好一些
    #             step_throw = 18 # 前面多少步全部丢弃，设置成18步的话就是从最左边视觉工位中心开始真正赋值起作用
    #             if cam_ret['trig_count'] > step_throw:
    #                 ret_trans = []
    #                 ret_trans[0] = self.ret_buffer[self.index_end - self.step_next - 1][0]
    #                 ret_trans[1] = self.ret_buffer[self.index_end - self.step_next - 1][1]
    #                 ret_trans[2] = self.ret_buffer[self.index_end - self.step_next + 1][0]
    #                 ret_trans[3] = self.ret_buffer[self.index_end - self.step_next + 1][0]
    #                 ret_trans[4] = 1
    #                 ret_trans[5] = 1
    #             else:
    #                 ret_trans = []
    #                 ret_trans[0] = 1
    #                 ret_trans[1] = 1
    #                 ret_trans[2] = 1
    #                 ret_trans[3] = 1
    #                 ret_trans[4] = 1
    #                 ret_trans[5] = 1
    #             self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 570, output_value=[1, 1, 1, 1, 1, 1])
    #             red = self.plc_client.execute(1, cst.READ_HOLDING_REGISTERS, 570, 6)  # 这里可以修改需要读取的功能码
    #
    #             print(red)
    #
    #         time.sleep(0.05)


                    # 下列代码为上述buffer更新计算的清晰逻辑
                    # if camId == 0:
                    #     if idx == 0:
                    #         ret_buffer[index_str + 0][0] = max(result.value, ret_buffer[index_str + 0][0])
                    #     elif idx == 1:
                    #         ret_buffer[index_str + 0][1] = max(result.value, ret_buffer[index_str + 0][1])
                    #     elif idx == 2:
                    #         ret_buffer[index_str + 2][0] = max(result.value, ret_buffer[index_str + 2][0])
                    #     elif idx == 3:
                    #         ret_buffer[index_str + 2][1] = max(result.value, ret_buffer[index_str + 2][1])
                    # elif camId == 1:
                    #     if idx == 0:
                    #         ret_buffer[index_str + dis_2 + 0][0] = max(result.value, ret_buffer[index_str + dis_2 + 0][0])
                    #     elif idx == 1:
                    #         ret_buffer[index_str + dis_2 + 0][1] = max(result.value, ret_buffer[index_str + dis_2 + 0][1])
                    #     elif idx == 2:
                    #         ret_buffer[index_str + dis_2 + 2][0] = max(result.value, ret_buffer[index_str + dis_2 + 2][0])
                    #     elif idx == 3:
                    #         ret_buffer[index_str + dis_2 + 2][1] = max(result.value, ret_buffer[index_str + dis_2 + 2][1])

    # {'camId':self.camId, 'trig_count': self.N})
    def capture_control(self):
        self.capture_done = False
        while True:
            # print("qsize",self.capture_sender.qsize())
            if self.capture_sender.qsize() >= 2:
                while self.capture_sender.qsize() > 0:
                    cam_cap = self.capture_sender.get()
                self.capture_done = True
                # 更新相机在循环buffer中的位置
                trig_count = cam_cap['trig_count']
                print(trig_count)
                self.trig_count = trig_count # 要把这个触发数写到类变量里面去，因为run进程中取值发送给PLC的时候还要用，但是那边已经不能通过在queue里取值来获取了
                step_num = (trig_count - 1) // 2 * 4 + (trig_count - 1) % 2
                # 相机0对应的两排在循环buffer中的位置
                index_cam0_1 = (self.index_cam0 - step_num) % (self.dis_1 + 1)
                index_cam0_2 = (self.index_cam0 - step_num + 2) % (self.dis_1 + 1)
                # 相机1对应的两排在循环buffer中的位置
                index_cam1_1 = (self.index_cam1 - step_num) % (self.dis_1 + 1)
                index_cam1_2 = (self.index_cam1 - step_num + 2) % (self.dis_1 + 1)
                print(index_cam0_1, index_cam0_2, index_cam1_1, index_cam1_2)
                # 更新相机0对应的两排的buffer内容
                self.ret_buffer[index_cam0_1] = [-1 for i in range(4)]
                self.ret_buffer[index_cam0_2] = [-1 for i in range(4)]
                # 更新相机1对应的两排的buffer内容
                self.ret_buffer[index_cam1_1] = [-1 for i in range(4)]
                self.ret_buffer[index_cam1_2] = [-1 for i in range(4)]
            time.sleep(0.05)
    
    def check_camID(self,model_num,capture_list):
        if model_num == 2:
            if '3' in capture_list and '4' in capture_list:
                pass
        elif model_num == 5:
            pass

    def count_v2(self, obj, gap_number=None):
        camId = obj['camId']
        ori_row_idx = obj['row_idx']
        result = obj['result']
        side = obj['side']
        row_idx = 0

        if gap_number is not None:
            # 侧面相机
            row_idx = self.robot_gap_to_above - (ori_row_idx % self.robot_gap_to_above) - 1
        else:
            # 正面相机
            row_idx = self.robot_gap_to_above - (ori_row_idx % self.robot_gap_to_above) - 1

        # 至此, row_idx 就是list里面的最终索引了
        
        robot = False
        #print(ori_row_idx)
        if ori_row_idx >= self.robot_gap_to_above - 1:
            # 标志着 第二轮结果即将来了
            # 机械手 要开始消除第一轮的结果
            robot = True

        if side == 0:
            self.left_list[row_idx] = int(self.result_dict[str(result)])
        elif side == 1:
            self.right_list[row_idx] = int(self.result_dict[str(result)])

        # 当 要发送机械手结果时，要保证当前检测结果左右都已经在list里面
        if robot == True:
            #print("row_idx",row_idx,"robot_index",self.robot_index)
            #print("left",self.left_list)
            #print("right",self.right_list)
            if self.left_list[self.robot_index] != -1 and self.right_list[self.robot_index] != -1:
                # 当左右两个list, 都已经有结果，才可以发
                send_robot_left = self.left_list[self.robot_index]
                send_robot_right = self.right_list[self.robot_index]
                if self.left_list[row_idx] != -1 and self.right_list[row_idx] != -1:
                    self.plc_client.write_multiple_registers(600, [0])
                    self.plc_client.write_multiple_registers(610, [0])
                    self.left_list[self.robot_index] = -1
                    self.right_list[self.robot_index] = -1
                    print("row_idx",row_idx,"robot_idx",self.robot_index)
                    print("left",self.left_list)
                    print("right",self.right_list)
                    self.robot_index -= 1

                    #time.sleep(0.1)

        if self.robot_index == -1:
            self.robot_index = self.robot_gap_to_above - 1

    # ret_sender:{'camId':self.camId,'trig_count':trig_count, 'result':result,'idx':idx,}
    def run(self):
        while True:
            if self.ret_sender.qsize() > 0:
                while self.ret_sender.qsize() > 0:
                    cam_ret = self.ret_sender.get()
                    # 更新最新得到的结果在循环buffer中的位置
                    trig_count = cam_ret['trig_count']
                    step_num = (trig_count - 1) // 2 * 4 + (trig_count - 1) % 2
                    # 最新得到的结果更新到循环buffer中,良品的value是0，缺陷的value是1
                    camID = cam_ret['camId']
                    idx = cam_ret['idx']
                    if camID == 0:
                        if idx == 0 or idx == 1:
                            index_ret = index_cam0_1 = (self.index_cam0 - step_num) % (self.dis_1 + 1)
                            self.ret_buffer[index_ret][2 * idx] = cam_ret['result'].value
                        elif idx == 2 or idx == 3:
                            index_ret = index_cam0_2 = (self.index_cam0 - step_num + 2) % (self.dis_1 + 1)
                            self.ret_buffer[index_ret][2 * idx - 4] = cam_ret['result'].value

                    elif camID == 1:
                        if idx == 0 or idx == 1:
                            index_ret = index_cam1_1 = (self.index_cam1 - step_num) % (self.dis_1 + 1)
                            self.ret_buffer[index_ret][2 * idx + 1] = cam_ret['result'].value
                        elif idx == 2 or idx == 3:
                            index_ret = index_cam1_2 = (self.index_cam1 - step_num + 2) % (self.dis_1 + 1)
                            self.ret_buffer[index_ret][2 * idx - 3] = cam_ret['result'].value
            if self.capture_done == True:
                # # test
                # #                if self.laliaodai_count >= self.cam_distance + 1:
                # #                    pdb.set_trace()
                # # enough images
                # # 更新分拣在循环buffer中的位置
                # trig_count = self.trig_count
                # step_num = (trig_count - 1) // 2 * 4 + (trig_count - 1) % 2
                # # 分拣对应的两排在循环buffer中的位置
                # index_pick_1 = (self.index_pick - step_num) % (self.dis_1 + 1)
                # index_pick_2 = (self.index_pick - step_num + 2) % (self.dis_1 + 1)
                #
                # result_det = []
                # # 整合分拣对应的2排(4个位置)的buffer内容，因为良品是0，缺陷是1，所以可以用max（）进行整合（前提是没有None和-1）
                # result_line0 = self.ret_buffer[index_pick_1]
                # result_line1 = self.ret_buffer[index_pick_2]
                # print("result_line0:", result_line0)
                # print("result_line1:", result_line1)
                # if (None in result_line0) or (None in result_line1):
                #     result_det = [1, 1, 1, 1]
                #     self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 570, output_value= result_det)
                #     self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 574, output_value= [1, 1])
                #     self.capture_done = False
                # elif (-1 in result_line0) or (-1 in result_line1):
                #     time.sleep(0.1)
                #     continue
                # else:
                #     result_det = [0, 0, 0, 0]
                #     result_det[0] = max(result_line0[0], result_line0[1])
                #     result_det[1] = max(result_line0[2], result_line0[3])
                #     result_det[2] = max(result_line1[0], result_line1[1])
                #     result_det[3] = max(result_line1[2], result_line1[3])
                #     self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 570, output_value=result_det)
                #     self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 574, output_value=[1, 1])
                #     self.capture_done = False
                # time.sleep(0.6)
                # result_det = [0, 0, 0, 0]
                result_det = [1, 1, 1, 1]  # 良品是0，缺陷是1，
                self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 570, output_value=result_det)
                self.plc_client.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 574, output_value=[1, 1])
                self.capture_done = False
            time.sleep(0.1)

if __name__ == '__main__':
    logger = logging_info.set_logger(config['log_dir'], os.path.basename(__file__))
    controller = Controller(logger)
    controller.run()


