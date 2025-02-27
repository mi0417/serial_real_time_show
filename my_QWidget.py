from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QFontMetrics
#导入串口模块
from serial_handle import SerialOperator
from logger import logger

class MyComboBoxControl(QComboBox):

    def __init__(self, parent = None):
        super(MyComboBoxControl,self).__init__(parent) #调用父类初始化方法

    # 重写showPopup函数
    def showPopup(self):  
        # 获取原选项
        index = self.currentIndex()
        logger.info('当前索引:%d', index)
        font_metrics = QFontMetrics(self.font())
        # 先清空原有的选项
        self.clear()
        # 初始化串口列表
        available_ports = SerialOperator().list_available_ports()
        logger.info('可用串口:%s', available_ports)
        # 添加关闭串口选项
        self.addItem('close')
        for port in available_ports:
            self.addItem(port)

            width = font_metrics.width(port) + 10
            previous_width = self.width()
            if previous_width < width:
                self.view().setFixedWidth(width)

        if self.count() >= index:
            self.setCurrentIndex(index)
            logger.info('重置串口数据，设置索引:%d', index)
        QComboBox.showPopup(self)   # 弹出选项框  