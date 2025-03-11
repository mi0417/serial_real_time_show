'''
    main.py
    主程序入口
'''

import sys
from PyQt5.QtWidgets import QApplication
from controller import SerialController

from common_helper import CommonHelper

if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = SerialController('Multi-interface monitor', 'serial', ':/imgs/功率 (1).png')
    qssStyle = CommonHelper.readQss(CommonHelper.resource_path('MacOS.qss'))
    controller.view.setStyleSheet(qssStyle)
    controller.show()
    sys.exit(app.exec_())
