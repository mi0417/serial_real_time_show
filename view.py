'''
    view
    只有view进行界面的读写和控件的直接操作
    并与controller之间传递数据
'''
import ctypes
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QListWidgetItem, QPushButton, QComboBox
from Ui_horizontal2 import Ui_Form

from logger import logger

class SerialView(QWidget):
    MAX_LOG_ITEMS = 100  # 设定最大日志项数
    BTN_CONNECT = 'connect'
    BTN_DISCONNECT = 'disconnect'

    def __init__(self, title, myappid, icon_path):
        super().__init__()
        self.controller = None
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

        self.ui.connectButton1.setText(self.BTN_CONNECT)
        self.ui.connectButton2.setText(self.BTN_CONNECT)

        # 连接信号和槽
        self.ui.pushButton.clicked.connect(self.switch_stop_button)
        self.ui.clearButton.clicked.connect(self.clean_data_edits)
        
        self.ui.serialBox1.currentIndexChanged.connect(lambda: self.show_selected_combobox(self.ui.serialBox1))
        self.ui.serialBox2.currentIndexChanged.connect(lambda: self.show_selected_combobox(self.ui.serialBox2))

    def clean_data_edits(self):
        '''清空数据框'''
        for i in range(1, 7):
            self.set_line_data(self.findChild(QLineEdit, f'volEdit{i}'), '')
            self.set_line_data(self.findChild(QLineEdit, f'curEdit{i}'), '')
            self.set_line_data(self.findChild(QLineEdit, f'powEdit{i}'), '')
            self.set_line_data(self.findChild(QLineEdit, f'curPowEdit{i}'), '')
        self.log_message('清空数据')

    def change_portlabel_color(self, index, status):
        '''
        更改实现方式，弃用
            改变portlabel的颜色
            index: 控件序号
            status: 状态，True为绿色，False为黑色
            改变portlabel的颜色
            index: 控件序号
            status: 状态，True为绿色，False为黑色
        '''
        try:
            line_name = f'portLabel{index}'
            line = self.findChild(QLabel, line_name)
            if status:
                line.setStyleSheet('color: #006633;')
            else:
                line.setStyleSheet('color: #272727;')
        except:
            logger.debug('portLabel%d不存在', index)

    def set_led(self, index, status):
        '''
            改变led的颜色
            index: 控件序号
            status: 状态，True为绿色，False为红色
        '''
        try:
            led_name = f'ledLabel{index}'
            led = self.findChild(QLabel, led_name)
            led.setStyleSheet(self.return_led_qss(status))
        except:
            logger.debug('ledLabel%d不存在', index)
    
    def set_line_data(self, line_edit: QLineEdit, value):
        '''
            向界面的QLineEdit中写值（电压，电流，功率）
            line_edit: QLineEdit 控件
            value: 行值

            示例: 向 powEdit1 中写值 12
            pow_edit_1 = self.findChild(QLineEdit, 'powEdit1')
            self.set_line_data(pow_edit_1, 12)
        '''
        # update_date 为True时，才更新数据
        if self.update_date or value == '':
            try:
                line_edit.setText(str(value))
            except:
                logger.debug('向控件写值 %s 失败', value)

    def show_selected_combobox(self, combobox:QComboBox):
        '''
        显示选择的combobox的内容
        '''
        selected_index = combobox.currentIndex()
        selected_input = combobox.currentText()
        if selected_input:
            logger.debug('Selected %s: %d - %s', combobox.objectName(), selected_index, selected_input)

    def change_button_text(self, button:QPushButton, text):
        '''
        改变按钮的文本
        '''
        button.setText(text)

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
            logger.debug('log_list: %s', message)
    
    def closeEvent(self, event):
        try:
            self.controller.cleanup()
            # logger.debug("Controller ID in SerialView: %s", id(self.controller))
            logger.debug('程序退出')
        except Exception as e:
            logger.error('关闭事件处理时发生错误: %s', e)
        event.accept()