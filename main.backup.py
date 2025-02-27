import sys
import time
import ctypes

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QLabel

from Ui_horizontal2 import Ui_Form  # 导入生成的 UI 类
from serial_handle import SerialOperator

class CommonHelper:
    def __init__(self):
        pass
 
    @staticmethod
    def readQss(style):
        with open(style, 'r', encoding='utf-8') as f:
            return f.read()

class DataController:
    def __init__(self):
        self.data = None

    def set_data(self, value):
        self.data = value

# 自定义线程类，用于打开串口
class OpenSerialThread(QThread):
    # 定义信号，用于向主线程发送串口打开结果
    result_signal = pyqtSignal(int, bool)

    def __init__(self, serial, index, port_name, baudrate, timeout):
        super().__init__()
        self.serial = serial
        self.index = index
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout

    def run(self):
        result = self.serial.open_serial_port(self.port_name, self.baudrate, self.timeout)
        # 发送结果信号，包含 comboBox 序号和打开结果
        self.result_signal.emit(self.index, result)

# 自定义线程类，用于接收和处理串口数据
class ReceiveSerialDataThread(QThread):
    data_received = pyqtSignal(int, bytes)

    def __init__(self, serial, index):
        super().__init__()
        self.serial = serial
        self.index = index

    def run(self):
        while self.serial.is_open:
            try:
                data = self.serial.receive_data()
                if data:
                    self.data_received.emit(self.index, data)
            except Exception as e:
                print(f"Error receiving data from serial {self.index}: {e}")
            time.sleep(0.1)  # 适当延迟，避免 CPU 占用过高

# 自定义线程类，用于模拟耗时任务
class WorkerThread(QThread):
    # 定义信号，用于向主线程发送数据
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run(self):
        # 模拟一个耗时任务
        for i in range(101):
            time.sleep(0.1)  # 模拟耗时操作
            self.progress.emit(i)  # 发送进度信号
        self.finished.emit()  # 任务完成信号

class MainWindow(QWidget):
    serial_entities = []

    def __init__(self, title, myappid, icon_path):
        super().__init__()
        self.ui = Ui_Form()  # 创建 UI 类的实例
        self.ui.setupUi(self)  # 设置 UI

        # 初始化串口列表
        self.get_all_serials()
        # TODO 初始化灯


        self.threads = []  # 用于存储所有线程的列表
        self.initUI(title, myappid, icon_path)

        # 创建 SerialOperator 实例的列表
        self.serials = [SerialOperator() for _ in range(6)]
        self.receive_threads = [None] * 6  # 用于存储接收数据的线程
        MainWindow.serial_entities = self.serials

        # 连接信号和槽
        self.connect_serial_msg()

        # 一些变量

    def initUI(self, title, myappid, icon_path):
        # 设置窗口标题
        self.setWindowTitle(title)
        # 设置窗口图标，假设 logo 文件名为 logo.png，且与 main.py 在同一目录下
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.setWindowIcon(QIcon(icon_path))


    def get_all_serials(self):
        '''
        初始化串口列表
        '''
        available_ports = SerialOperator().list_available_ports()
        print("可用串口:", available_ports)

        # 循环操作 comboBox1 到 comboBox6
        for i in range(1, 7):
            # 动态获取 comboBox 控件的引用
            combo_box_name = f"comboBox{i}"
            combo_box = self.findChild(QComboBox, combo_box_name)
            if combo_box is not None:
                # 清空 comboBox 原有的选项
                combo_box.clear()
                # 为 comboBox 添加选项
                for port in available_ports:
                    combo_box.addItem(port)
                combo_box.setCurrentIndex(-1)
                # if len(available_ports) >= i:
                #     combo_box.setCurrentIndex(i - 1)

    def get_open_serials(self):
        '''
        获取当前打开的串口列表
        非本程序打开的串口不进行统计
        '''
        open_serials = []
        for serial in self.serials:
            if serial.is_open:
                open_serials.append(serial.opened_port)
        return open_serials


    def connect_serial_msg(self):
        for i in range(1, 7):
            combo_box_name = f"comboBox{i}"
            combo_box = self.findChild(QComboBox, combo_box_name)
            if combo_box is not None:
                # 绑定按钮点击信号到对应的操作方法
                combo_box.currentIndexChanged.connect(lambda index, box=combo_box: self.handle_combobox_change(i, box.currentText()))

    def handle_combobox_change(self, combobox_index, port_name):
        baudrate = 9600
        timeout = 1
        print("当前选择的串口:", port_name)
        if port_name != '':
            # 创建打开串口的线程
            open_serial_thread = OpenSerialThread(self.serials[combobox_index - 1], combobox_index, port_name, baudrate, timeout)
            open_serial_thread.result_signal.connect(self.handle_serial_open_result)
            open_serial_thread.daemon = True
            open_serial_thread.start()
            self.threads.append(open_serial_thread)
        else:
            self.serials[combobox_index - 1].close_serial_port()
            self.set_led(combobox_index, False)
            if self.receive_threads[combobox_index - 1]:
                self.receive_threads[combobox_index - 1].quit()
                self.receive_threads[combobox_index - 1].wait()
                self.receive_threads[combobox_index - 1] = None

    def handle_serial_open_result(self, index, result):
        # 根据串口打开结果设置 LED 状态
        self.set_led(index, result)
        if result:
            # 启动接收数据的线程
            receive_thread = ReceiveSerialDataThread(self.serials[index - 1], index)
            receive_thread.data_received.connect(self.handle_serial_data_received)
            receive_thread.start()
            self.receive_threads[index - 1] = receive_thread

    def handle_serial_data_received(self, index, data):
        print(f"Received data from serial {index}: {data}")
        # 在这里可以添加对数据的处理逻辑

    # 设置 LED 状态的方法
    def set_led(self, index, status):
        '''
            设置灯的状态
            index: ledLabel的序号
            status: True 绿灯，False 红灯
        '''
        try:
            led_name = f"ledLabel{index}"
            print(led_name)
            led = self.findChild(QLabel, led_name)
            led.setStyleSheet(self.return_led_qss(status))
        except:
            print(f"ledLabel{index}不存在")

    def return_led_qss(self, status):
        '''
            返回灯对应的qss
            status: True 绿灯，False 红灯
        '''
        if status:
            return "background-color: lime;border: 3px ridge darkgreen;"
        else:
            return "background-color: red;border: 3px ridge darkred;"

    # TODO 暂停继续按钮

    def closeEvent(self, event):
        # 关闭窗口时停止所有线程
        for thread in self.threads:
            thread.quit()
            thread.wait()
        for receive_thread in self.receive_threads:
            if receive_thread:
                receive_thread.quit()
                receive_thread.wait()
        for serial in self.serials:
            serial.close_serial_port()

    def add_new_thread(self):
        # 创建并启动新线程
        thread = WorkerThread()
        thread.progress.connect(self.update_progress)
        thread.finished.connect(self.task_finished)
        thread.start()
        self.threads.append(thread)  # 将新线程添加到列表中

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow("serial", "serial", ":/功率 (1).png")

    styleFile = './MacOS.qss'
    qssStyle = CommonHelper.readQss(styleFile)
    window.setStyleSheet(qssStyle)

    window.show()
    sys.exit(app.exec_())