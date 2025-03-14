'''
    view
    只有view进行界面的读写和控件的直接操作
    并与controller之间传递数据
'''
import ctypes
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFontMetrics, QFont
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QListWidgetItem, QPushButton, QComboBox
from PyQt5.QtCore import Qt, QSize
from Ui_horizontal import Ui_Form

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
        # self.addItem('close')
        max_width = 0
        for port in available_ports:
            self.addItem(port)

            width = font_metrics.width(port) + 20
            if max_width < width:
                max_width = width
        if max_width > self.maximumWidth():
            self.view().setFixedWidth(width)

        # if self.count() >= index:
        #     self.setCurrentIndex(index)
        #     logger.info('重置串口数据，设置索引:%d', index)
        QComboBox.showPopup(self)   # 弹出选项框  

class SerialView(QWidget):
    MAX_LOG_ITEMS = 100  # 设定最大日志项数
    BTN_CONNECT = 'connect'
    BTN_DISCONNECT = 'disconnect'

    def __init__(self, title, myappid, icon_path):
        super().__init__()
        # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling) # 适应windows缩放
        # QtGui.QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough) # 设置支持小数放大比例（适应如125%的缩放比）
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
        self.change_font_size()

        # 初始化界面控件
        for i in range(1,7):
            self.set_led(i, False)

        self.ui.connectButton1.setText(self.BTN_CONNECT)
        self.ui.connectButton2.setText(self.BTN_CONNECT)

        # 重写QComboBox
        self.ui.serialBox1 = self.replace_combo_box(self.ui.serialBox1, self)
        self.ui.serialBox2 = self.replace_combo_box(self.ui.serialBox2, self)

        # 连接信号和槽
        self.ui.pushButton.clicked.connect(self.switch_stop_button)
        self.ui.clearButton.clicked.connect(self.clean_data_edits)
        
        self.ui.serialBox1.currentIndexChanged.connect(lambda: self.show_selected_combobox(self.ui.serialBox1))
        self.ui.serialBox2.currentIndexChanged.connect(lambda: self.show_selected_combobox(self.ui.serialBox2))

    # def changeEvent(self, a0):
    #     logger.info('changeEvent: %s', a0.type())
    #     # if a0.type() == QEvent.ScreenChanged:
    #     self.change_font_size()
    #     super().changeEvent(a0)

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        width = self.width()
        # 根据DPI调整
        screen = self.window().screen()
        dpi = screen.logicalDotsPerInchY()
        if dpi > 120:
            if width >= 1920:
                self.ui.powLabel.setText('Max Power(W)')
                self.ui.curPowLabel.setText('Current Power(W)')
            else:
                self.ui.powLabel.setText('Max\nPower(W)')
                self.ui.curPowLabel.setText('Current\nPower(W)')
        else:
            if width >= 1440:
                self.ui.powLabel.setText('Max Power(W)')
                self.ui.curPowLabel.setText('Current Power(W)')
            else:
                self.ui.powLabel.setText('Max\nPower(W)')
                self.ui.curPowLabel.setText('Current\nPower(W)')
        
        self.change_font_size()
        # 输出窗口改变后的宽高
        logger.info('当前DPI：%d，窗口改变后宽度: %d, 窗口改变后高度: %d', dpi, self.width(), self.height())
    
    def change_font_size(self):
        '''如果dpi>130，按130dpi计算'''
        screen = self.window().screen()
        dpi = screen.logicalDotsPerInchY()
        if dpi > 130:
            dpi = 130
        self.convert_fonts_to_pixel_size(dpi)

    def convert_fonts_to_pixel_size(self, dpi):
        # 遍历所有子控件
        for widget in self.findChildren((QLabel, QPushButton, QLineEdit)):
            font = widget.font()
            # 尝试从 widget 的属性中获取原始的 pointSize
            original_point_size = widget.property('original_point_size')
            if original_point_size is None:
                # 如果没有保存过，获取当前的 pointSize 并保存
                original_point_size = font.pointSize()
                widget.setProperty('original_point_size', original_point_size)
            point_size = original_point_size
            # point_size = font.pointSize()
            if point_size > 0:
                # logger.debug('%s: %d', widget.objectName(), point_size)
                # 将 pointSize 转换为像素大小
                pixel_size = int(point_size * dpi / 72)
                # 设置新的字体像素大小
                font.setPixelSize(pixel_size)
            widget.setFont(font)

    def replace_combo_box(self, original_combo:QComboBox, parent):
        if original_combo:
            combo = MyComboBoxControl(parent)
            combo.setGeometry(original_combo.geometry())
            combo.addItems([original_combo.itemText(i) for i in range(original_combo.count())])
            combo.setMinimumSize(original_combo.minimumSize())
            combo.setMaximumSize(original_combo.maximumSize())
            combo.setFont(original_combo.font())
            combo.setInputMethodHints(original_combo.inputMethodHints())
            combo.setObjectName(original_combo.objectName())
        else:
            combo = MyComboBoxControl(parent)
            combo.setMinimumSize(QSize(180, 25))
            combo.setMaximumSize(QSize(200, 16777215))
            font = QFont()
            font.setFamily('微软雅黑')
            font.setPointSize(20)
            combo.setFont(font)
            combo.setInputMethodHints(Qt.ImhEmailCharactersOnly | Qt.ImhNoAutoUppercase)
            combo.setObjectName('serialBox')

        # 替换原有的 QComboBox
        if original_combo.parent().layout():
            index = original_combo.parent().layout().indexOf(original_combo)
            original_combo.parent().layout().removeWidget(original_combo)
            # 释放原有的 QComboBox 资源
            original_combo.deleteLater()
            original_combo.parent().layout().insertWidget(index, combo)
        return combo
    
    def clean_data_edits(self):
        '''清空数据框'''
        for i in range(1, 7):
            vol_edit = self.findChild(QLineEdit, f'volEdit{i}')
            if vol_edit:
                vol_edit.setText('')
            cur_edit = self.findChild(QLineEdit, f'curEdit{i}')
            if cur_edit:
                cur_edit.setText('')
            pow_edit = self.findChild(QLineEdit, f'powEdit{i}')
            if pow_edit:
                pow_edit.setText('')
            cur_pow_edit = self.findChild(QLineEdit, f'curPowEdit{i}')
            if cur_pow_edit:
                cur_pow_edit.setText('')
        self.log_message('Data cleared') # ('清空数据')

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
        if self.update_date:
            try:
                # None 不写入
                if value is not None:
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
            log_message = 'Pause' # '暂停'
        else:
            button_icon_path = ':/imgs/24gf-pause2.png'
            log_message = 'Resume' # '继续'
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
            # logger.debug('Controller ID in SerialView: %s', id(self.controller))
            logger.debug('程序退出')
        except Exception as e:
            logger.error('关闭事件处理时发生错误: %s', e)
        event.accept()