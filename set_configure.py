from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import sys

# model = 111

class setConfigure(QDialog):
    Signal = pyqtSignal(str)
    def __init__(self):
        super(setConfigure, self).__init__()
        # global model
        self.initUI()

        self.buttom_sure.clicked.connect(lambda:self.send_info())

    # @staticmethod

    def send_info(self):
        model = self.attribution_11_context.currentIndex()
        self.Signal.emit(str(model))
        self.close()

    def initUI(self):
        self.resize(640,550)

        self.attribution_1 = QLabel(self)
        self.attribution_1.setText("属性1: ")
        self.attribution_1.setFont(QFont("Times", 14))
        self.attribution_1.setFixedSize(150, 50)
        self.attribution_1.move(20, 50)

        self.attribution_1_context = QTextEdit(self)
        self.attribution_1_context.setFont(QFont("Times", 14))
        self.attribution_1_context.setFixedSize(150, 50)
        self.attribution_1_context.move(100, 50)

        self.attribution_2 = QLabel(self)
        self.attribution_2.setText("属性2: ")
        self.attribution_2.setFont(QFont("Times", 14))
        self.attribution_2.setFixedSize(150, 50)
        self.attribution_2.move(270, 50)

        self.attribution_2_context = QTextEdit(self)
        self.attribution_2_context.setFont(QFont("Times", 14))
        self.attribution_2_context.setFixedSize(150, 50)
        self.attribution_2_context.move(350, 50)

        self.attribution_3 = QLabel(self)
        self.attribution_3.setText("属性3: ")
        self.attribution_3.setFont(QFont("Times", 14))
        self.attribution_3.setFixedSize(150, 50)
        self.attribution_3.move(20, 120)

        self.attribution_3_context = QTextEdit(self)
        self.attribution_3_context.setFont(QFont("Times", 14))
        self.attribution_3_context.setFixedSize(150, 50)
        self.attribution_3_context.move(100, 120)

        self.attribution_4 = QLabel(self)
        self.attribution_4.setText("属性4: ")
        self.attribution_4.setFont(QFont("Times", 14))
        self.attribution_4.setFixedSize(150, 50)
        self.attribution_4.move(270, 120)

        self.attribution_4_context = QTextEdit(self)
        self.attribution_4_context.setFont(QFont("Times", 14))
        self.attribution_4_context.setFixedSize(150, 50)
        self.attribution_4_context.move(350, 120)

        self.attribution_5 = QLabel(self)
        self.attribution_5.setText("属性5: ")
        self.attribution_5.setFont(QFont("Times", 14))
        self.attribution_5.setFixedSize(150, 50)
        self.attribution_5.move(20, 190)

        self.attribution_5_context = QTextEdit(self)
        self.attribution_5_context.setFont(QFont("Times", 14))
        self.attribution_5_context.setFixedSize(150, 50)
        self.attribution_5_context.move(100, 190)

        self.attribution_6 = QLabel(self)
        self.attribution_6.setText("属性6: ")
        self.attribution_6.setFont(QFont("Times", 14))
        self.attribution_6.setFixedSize(150, 50)
        self.attribution_6.move(270, 190)

        self.attribution_6_context = QTextEdit(self)
        self.attribution_6_context.setFont(QFont("Times", 14))
        self.attribution_6_context.setFixedSize(150, 50)
        self.attribution_6_context.move(350, 190)

        self.attribution_7 = QLabel(self)
        self.attribution_7.setText("属性1: ")
        self.attribution_7.setFont(QFont("Times", 14))
        self.attribution_7.setFixedSize(150, 50)
        self.attribution_7.move(20, 260)

        self.attribution_7_context = QTextEdit(self)
        self.attribution_7_context.setFont(QFont("Times", 14))
        self.attribution_7_context.setFixedSize(150, 50)
        self.attribution_7_context.move(100, 260)

        self.attribution_8 = QLabel(self)
        self.attribution_8.setText("属性2: ")
        self.attribution_8.setFont(QFont("Times", 14))
        self.attribution_8.setFixedSize(150, 50)
        self.attribution_8.move(270, 260)

        self.attribution_8_context = QTextEdit(self)
        self.attribution_8_context.setFont(QFont("Times", 14))
        self.attribution_8_context.setFixedSize(150, 50)
        self.attribution_8_context.move(350, 260)

        self.attribution_9 = QLabel(self)
        self.attribution_9.setText("属性1: ")
        self.attribution_9.setFont(QFont("Times", 14))
        self.attribution_9.setFixedSize(150, 50)
        self.attribution_9.move(20, 330)

        self.attribution_9_context = QTextEdit(self)
        self.attribution_9_context.setFont(QFont("Times", 14))
        self.attribution_9_context.setFixedSize(150, 50)
        self.attribution_9_context.move(100, 330)

        self.attribution_10 = QLabel(self)
        self.attribution_10.setText("属性2: ")
        self.attribution_10.setFont(QFont("Times", 14))
        self.attribution_10.setFixedSize(150, 50)
        self.attribution_10.move(270, 330)

        self.attribution_10_context = QTextEdit(self)
        self.attribution_10_context.setFont(QFont("Times", 14))
        self.attribution_10_context.setFixedSize(150, 50)
        self.attribution_10_context.move(350, 330)

        self.attribution_11 = QLabel(self)
        self.attribution_11.setText("属性2: ")
        self.attribution_11.setFont(QFont("Times", 14))
        self.attribution_11.setFixedSize(150, 50)
        self.attribution_11.move(20, 400)

        self.attribution_11_context = QTextEdit(self)
        self.attribution_11_context.setFont(QFont("Times", 14))
        self.attribution_11_context.setFixedSize(150, 50)
        self.attribution_11_context.move(100, 400)

        self.attribution_11 = QLabel(self)
        self.attribution_11.setText("模式: ")
        self.attribution_11.setFont(QFont("Times", 14))
        self.attribution_11.setFixedSize(150, 50)
        self.attribution_11.move(270, 400)

        self.attribution_11_context = QComboBox(self)
        self.attribution_11_context.setFont(QFont("Times", 14))
        self.attribution_11_context.setFixedSize(150, 50)
        self.attribution_11_context.move(350, 400)
        self.attribution_11_context.addItem("七包模式",0)
        self.attribution_11_context.addItem("六包模式",1)
        self.attribution_11_context.setCurrentIndex(1)

        self.buttom_sure = QPushButton(self)
        self.buttom_sure.setText("Submit")
        self.buttom_sure.setFont(QFont("Times", 14))
        self.buttom_sure.setFixedSize(150, 50)
        self.buttom_sure.move(250, 470)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    work = setConfigure()
    work.show()
    sys.exit(app.exec_())