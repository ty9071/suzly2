from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import sys

class testLink(QDialog):
    def __init__(self):
        super(testLink, self).__init__()
        self.initUI() 
        self.button_test.clicked.connect(lambda:self.test())

    def initUI(self):
        self.img = QLabel(self)
        self.img.setFixedSize(300,160)
        # qimg = QImage(img,200,100,QImage.Format_RGB888)
        # self.img.setPixmap(QPixmap.fromImage(qimg))

        self.onside_cam = QLabel(self)
        self.onside_cam.setFixedSize(100,50)
        self.onside_cam.move(10,10)
        self.onside_cam.setText("正面相机")
        self.onside_cam.setFont(QFont('Times',14))

        self.onside_sure = QFrame(self)
        self.onside_sure.setFixedSize(30,30)
        self.onside_sure.move(110,20)
        self.onside_sure.setStyleSheet("background-color:green;")

        self.leftside_cam = QLabel(self)
        self.leftside_cam.setFixedSize(100,50)
        self.leftside_cam.move(10,60)
        self.leftside_cam.setText("左面相机")
        self.leftside_cam.setFont(QFont('Times',14))

        self.leftside_sure = QFrame(self)
        self.leftside_sure.setFixedSize(30,30)
        self.leftside_sure.move(110,70)
        self.leftside_sure.setStyleSheet("background-color:green;")

        self.rightside_cam = QLabel(self)
        self.rightside_cam.setFixedSize(100,50)
        self.rightside_cam.move(150,10)
        self.rightside_cam.setText("右面相机")
        self.rightside_cam.setFont(QFont('Times',14))

        self.rightside_sure = QFrame(self)
        self.rightside_sure.setFixedSize(30,30)
        self.rightside_sure.move(250,20)
        self.rightside_sure.setStyleSheet("background-color:green;")

        self.plc = QLabel(self)
        self.plc.setFixedSize(100,50)
        self.plc.move(150,60)
        self.plc.setText("PLC控制器")
        self.plc.setFont(QFont('Times',14))

        self.plc_sure = QFrame(self)
        self.plc_sure.setFixedSize(30,30)
        self.plc_sure.move(250,70)
        self.plc_sure.setStyleSheet("background-color:green;")

        self.button_test = QPushButton(self)
        self.button_test.setText("测试连接性")
        self.button_test.setFont(QFont("Times", 12))
        self.button_test.setFixedSize(100, 30)
        self.button_test.move(110, 120)
    def test(self):
        print("111test")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    work = showBig()
    work.show()
    # work.showFullScreen()
    sys.exit(app.exec_())
