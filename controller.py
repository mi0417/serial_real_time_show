'''
    controller
    业务逻辑处理
'''
import time
import re
import queue

from PyQt5.QtCore import QThread, QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QComboBox

from model import SerialModel
from view import SerialView

from logger import logger

class ReceiveThread(QThread):
    '''
    自定义线程类，用于接收串口数据并处理
    '''
    data_received = pyqtSignal(int, str, str, str)

    def __init__(self, model: SerialModel, index, data_queue):
        super().__init__()
        logger.debug('创建传输数据子线程 %s', self)
        self.model = model
        self.index = index
        self._running = True
        self.data_queue = data_queue

    def run(self):
        while self._running and self.model.is_serial_open(self.index):
            try:
                data = self.model.receive_data(self.index)
                if data:
                    self.model.last_receive_time[self.index - 1] = time.time()
                    vol = ''
                    cur = ''
                    pow = ''
                    pattern = r'(vol|cur|pow)=(\d+\.?\d*)'
                    matches = re.findall(pattern, data.decode())
                    for key, value in matches:
                        if key == 'vol':
                            vol = value
                        elif key == 'cur':
                            cur = value
                        elif key == 'pow':
                            pow = value
                    self.data_queue.put((self.index, vol, cur, pow))
            except Exception as e:
                logger.error('Error receiving data from serial %d: %s', self.index, e)
            time.sleep(0.1)

    def stop(self):
        self._running = False

    def __del__(self):
        logger.debug('传输串口子线程%s被销毁', self)

class OpenSerialThread(QThread):
    '''
    自定义线程类，用于打开串口
    '''
    result_signal = pyqtSignal(int, bool, str)  # 自定义信号，用于传递结果给主线程

    def __init__(self, model: SerialModel, index, port_name, baudrate, timeout):
        super().__init__()
        logger.debug('创建打开串口子线程%s', self)
        self.model = model
        self.index = index
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout

    def run(self):
        result = self.model.open_serial_port(self.index, self.port_name, self.baudrate, self.timeout)
        self.result_signal.emit(self.index, result, self.port_name)

    def __del__(self):
        logger.debug('打开串口子线程%s被销毁', self)


class SerialController(QObject):
    '''
        主线程
    '''
    def __init__(self, title, myappid, icon_path):
        super().__init__()  # 调用父类的构造函数
        logger.debug('程序开始运行')
        logger.debug('Controller ID in SerialController: %s', id(self))
        self.model = SerialModel()
        self.view = SerialView(title, myappid, icon_path)
        self.view.controller = self
        self.threads = []
        self.receive_threads = [None] * 6
        self.receive_data_flag = [False] * 6  # 数据接收是否超时发送超时信息的标志
        self.data_queue = queue.Queue()
        self.initUI()
        self.connect_serial_msg()

        # 启动定时器，每隔一定时间检查一次队列
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_queue_data)
        self.timer.start(100)  # 每 100 毫秒检查一次队列

        # 启动定时器，每隔一定时间检查一次串口数据
        self.serial_timer = QTimer(self)
        self.serial_timer.timeout.connect(self.check_serial_data)
        self.serial_timer.start(1000)  # 每秒检查一次

    def initUI(self):
        # 初始化串口列表
        available_ports = self.model.get_all_serials()
        logger.debug('可用串口: %s', available_ports)
        for i in range(1, 7):
            combo_box_name = f'comboBox{i}'
            combo_box = self.view.findChild(QComboBox, combo_box_name)
            if combo_box is not None:
                combo_box.clear()
                combo_box.addItem('close')
                for port in available_ports:
                    combo_box.addItem(port)
                # combo_box.setCurrentIndex(-1)

    def connect_serial_msg(self):
        for i in range(1, 7):
            combo_box_name = f'comboBox{i}'
            combo_box = self.view.findChild(QComboBox, combo_box_name)
            if combo_box is not None:
                logger.debug('绑定事件 combo_box_name=%s', combo_box_name)
                combo_box.currentIndexChanged.connect(
                    lambda _, box=combo_box, current_i=i: self.handle_combobox_change(current_i, box.currentText()))

    def handle_combobox_change(self, combobox_index, port_name):
        '''
        处理组合框选择变化的事件。

        :param combobox_index: 组合框的索引。
        :param port_name: 当前选择的串口名称。
        '''
        baudrate = 9600
        timeout = 1
        logger.info('下拉框 %d 当前选择的串口: %s', combobox_index, port_name)

        # 关闭之前的数据接收线程
        if self.receive_threads[combobox_index - 1]:
            self.receive_threads[combobox_index - 1].stop()
            self.receive_threads[combobox_index - 1].wait()
            self.receive_threads[combobox_index - 1] = None

        if port_name not in ('', 'close'):
            # 创建打开串口的线程
            open_serial_thread = OpenSerialThread(self.model, combobox_index, port_name, baudrate, timeout)
            open_serial_thread.result_signal.connect(self.handle_open_serial_result)    # 将 open_serial_thread 的 result_signal 信号连接到 handle_open_serial_result 方法，当串口打开操作完成后，会触发该方法进行后续处理。
            open_serial_thread.start()
            self.threads.append(open_serial_thread)
        else:
            if self.model.is_serial_open(combobox_index):
                self.view.log_message(f'Port{combobox_index}关闭串口')
                self.model.close_serial_port(combobox_index)
                self.view.change_portlabel_color(combobox_index, False)
                self.view.set_led(combobox_index, False)
                if self.receive_threads[combobox_index - 1]:
                    self.receive_threads[combobox_index - 1].stop()
                    self.receive_threads[combobox_index - 1].wait()
                    self.receive_threads[combobox_index - 1] = None

    def handle_open_serial_result(self, index, result, port_name):
        self.view.change_portlabel_color(index, result)
        if result:
            self.receive_data_flag[index - 1] = True
            self.view.set_led(index, True)
            self.view.log_message(f'Port{index}打开串口{port_name}成功')
            # 启动接收线程
            receive_thread = ReceiveThread(self.model, index, self.data_queue)
            receive_thread.start()
            self.receive_threads[index - 1] = receive_thread
            # 关闭打开串口的线程
            for thread in self.threads:
                if isinstance(thread, OpenSerialThread) and thread.index == index:
                    thread.quit()
                    thread.wait()
                    self.threads.remove(thread)
                    break
        else:
            self.view.log_message(f'Port{index}打开串口{port_name}失败，请检查连接是否被占用', True)

    def process_queue_data(self):
        while not self.data_queue.empty():
            index, vol, cur, pow = self.data_queue.get()
            if vol:
                self.view.set_line_data('volEdit', index, vol)
            if cur:
                self.view.set_line_data('curEdit', index, cur)
            if pow:
                self.view.set_line_data('powEdit', index, pow)

    def check_serial_data(self):
        '''
        检查串口数据的事件。
        '''
        timeout_threshold = 10  # 超时阈值，单位为秒
        for i in range(1, 7):
            if self.model.is_serial_open(i):
                last_time = self.model.last_receive_time[i - 1]
                current_time = time.time()
                if current_time - last_time < timeout_threshold:  # 如果在 10 秒内接收到数据
                    self.receive_data_flag[i - 1] = True
                    self.view.set_led(i, True)
                else:
                    if self.receive_data_flag[i - 1]:
                        self.view.log_message(f'Port{i}未在{timeout_threshold}s内接收到数据，请检查连接', True)
                        self.receive_data_flag[i - 1] = False
                        logger.debug('串口 %d last_time: %s, current_time: %s, %ds 内未接收到数据', i, last_time,
                                     current_time, timeout_threshold)
                    self.view.set_led(i, False)
            else:
                self.view.set_led(i, False)

    def cleanup(self):
        for thread in self.threads:
            thread.quit()
            thread.wait()
        for receive_thread in self.receive_threads:
            if receive_thread:
                receive_thread.stop()
                receive_thread.wait()
        for i in range(1, 7):
            self.model.close_serial_port(i)

    def show(self):
        self.view.show()
