'''
    view
    只有view进行界面的读写和控件的直接操作
    并与controller之间传递数据
'''
import ctypes
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QListWidgetItem
from Ui_horizontal2 import Ui_Form

from logger import logger

class SerialView(QWidget):
    MAX_LOG_ITEMS = 100  # 设定最大日志项数

    def __init__(self, title, myappid, icon_path):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle(title)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.setWindowIcon(QIcon(icon_path))
        self.init_panel()
        self.update_date = True # 用于控制是否更新数据，True时button显示暂停图片，False时button显示继续运行图片

    def init_panel(self):
        '''
            初始化
        '''
        # 初始化界面控件
        for i in range(1,7):
            self.set_led(i, False)

        # 连接信号和槽
        self.ui.pushButton.clicked.connect(self.switch_stop_button)

    def set_led(self, index, status):
        try:
            led_name = f'ledLabel{index}'
            led = self.findChild(QLabel, led_name)
            led.setStyleSheet(self.return_led_qss(status))
        except:
            logger.debug(f'ledLabel{index}不存在')
    
    def set_line_data(self, qline_name, index, value):
        '''
            向界面的QLineEdit中写值（电压，电流，功率）
            qline_name: 控件名称 
            index: 控件序号
            value: 行值

            示例: 向powEdit1中写值12
            self.set_line_data('powEdit', 1, 12)
        '''
        if self.update_date:
            try:
                line_name = f'{qline_name}{index}'
                line = self.findChild(QLineEdit, line_name)
                line.setText(str(value))
            except:
                logger.debug(f'{qline_name}{index}不存在，写值{value}失败')

    def switch_stop_button(self):
        '''
            切换停止按钮的状态
            on -> off : self.update_date=False, 停止更新数据
            off -> on : self.update_date=True, 开始更新数据
        '''
        # 切换图标路径
        if self.update_date:
            button_icon_path = ':imgs/24gf-play (1).png'
            log_message = '暂停'
        else:
            button_icon_path = ':/imgs/24gf-pause2.png'
            log_message = '继续'
        # 更新图标
        icon = QIcon()
        icon.addPixmap(QPixmap(button_icon_path), QIcon.Normal, QIcon.Off)
        self.ui.pushButton.setIcon(icon)
        self.log_message(log_message)

        self.update_date = not self.update_date

    def return_led_qss(self, status):
        if status:
            return 'background-color: lime;border: 3px ridge darkgreen;'
        else:
            return 'background-color: red;border: 3px ridge darkred;'

    
    def log_message(self, message, is_error=False):
        '''
        向界面的 listwidget 末尾添加日志信息，并滚动到最下方。
        当列表项数量超过 MAX_LOG_ITEMS 时，删除最早的项。

        :param message: 要添加的日志信息
        :param is_error: 是否为错误消息，默认为 False
        '''
        # 假设 listwidget 的对象名为 logListWidget，根据实际情况修改
        log_list_widget = self.ui.listWidget
        if message:
            if log_list_widget.count() >= self.MAX_LOG_ITEMS:
                # 删除最早的项
                item = log_list_widget.takeItem(0)
                del item
            item = QListWidgetItem(str(message))
            if is_error:
                item.setForeground(QColor('red'))
            log_list_widget.addItem(item)
            log_list_widget.scrollToBottom()
            logger.debug(f'log_list: {message}')