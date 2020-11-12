from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class showBig(QDialog):
    def __init__(self,img):
        super(showBig, self).__init__()
        self.initUI(img)

    def initUI(self,img):
        self.img = QLabel(self)
        self.img.setFixedSize(1024,576)
        qimg = QImage(img,1024,576,QImage.Format_RGB888)
        self.img.setPixmap(QPixmap.fromImage(qimg))

