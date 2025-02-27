'''
    controller
    业务逻辑处理
'''
import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QComboBox

from model import SerialModel
from view import SerialView

from logger import logger

class ReceiveThread(QThread):
    data_received = pyqtSignal(int, bytes)

    def __init__(self, model, index):
        super().__init__()
        self.model = model
        self.index = index
        self._running = True

    def run(self):
        while self._running and self.model.is_serial_open(self.index):
            try:
                self.model.process_received_data(self.index)
            except Exception as e:
                logger.error(f'Error receiving data from serial {self.index}: {e}')
            time.sleep(0.1)

    def stop(self):
        self._running = False

class OpenSerialThread(QThread):
# 自定义线程类，用于打开串口
    result_signal = pyqtSignal(int, bool, str)  # 自定义信号，用于传递结果给主线程

    def __init__(self, model:SerialModel, index, port_name, baudrate, timeout):
        super().__init__()
        logger.debug(f'创建打开串口子线程{self}')
        self.model = model
        self.index = index
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout

    def run(self):
        result = self.model.open_serial_port(self.index, self.port_name, self.baudrate, self.timeout)
        self.result_signal.emit(self.index, result, self.port_name)
    
    def __del__(self):
        logger.debug(f'打开串口子线程{self}被销毁')
    

class SerialController:
    '''
        主线程
    '''
    def __init__(self, title, myappid, icon_path):
        self.model = SerialModel()
        self.view = SerialView(title, myappid, icon_path)
        self.threads = []
        self.receive_threads = [None] * 6
        self.initUI()
        self.connect_serial_msg()

    def initUI(self):
        # 初始化串口列表
        available_ports = self.model.get_all_serials()
        logger.debug(f'可用串口:{available_ports}')
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
                logger.debug(f'绑定事件combo_box_name={combo_box_name}')
                combo_box.currentIndexChanged.connect(lambda _, box=combo_box, current_i=i: self.handle_combobox_change(current_i, box.currentText()))

    def handle_combobox_change(self, combobox_index, port_name):
        '''
        处理组合框选择变化的事件。

        :param combobox_index: 组合框的索引。
        :param port_name: 当前选择的串口名称。
        '''
        baudrate = 9600
        timeout = 1
        logger.info(f'下拉框{combobox_index}当前选择的串口:{port_name}')
        if port_name != '' and port_name != 'close':
            # 创建打开串口的线程
            open_serial_thread = OpenSerialThread(self.model, combobox_index, port_name, baudrate, timeout)
            open_serial_thread.result_signal.connect(self.handle_open_serial_result)    # 将 open_serial_thread 的 result_signal 信号连接到 handle_open_serial_result 方法，当串口打开操作完成后，会触发该方法进行后续处理。
            open_serial_thread.start()
            self.threads.append(open_serial_thread)
        else:
            if port_name == 'close' and self.model.is_serial_open(combobox_index):
                self.view.log_message(f'Port{combobox_index}关闭串口')
            self.model.close_serial_port(combobox_index)
            self.view.set_led(combobox_index, False)
            if self.receive_threads[combobox_index - 1]:
                self.receive_threads[combobox_index - 1].stop()
                self.receive_threads[combobox_index - 1].wait()
                self.receive_threads[combobox_index - 1] = None

    def handle_open_serial_result(self, index, result, port_name):
        self.view.set_led(index, result)
        if result:
            self.view.log_message(f'Port{index}打开串口{port_name}成功')
            # 注册数据接收回调函数
            self.model.register_data_callback(index, self.handle_serial_data_received)
            # 启动接收线程
            receive_thread = ReceiveThread(self.model, index)
            receive_thread.data_received.connect(self.handle_serial_data_received)
            receive_thread.start()
            self.receive_threads[index - 1] = receive_thread
        else:
            self.view.log_message(f'Port{index}打开串口{port_name}失败，请检查连接是否被占用', True)
    
    def handle_serial_data_received(self, index, data):
        '''
        处理接收到的串口数据的事件。

        :param index: 串口索引。
        :param data: 接收到的串口数据。
        '''
        logger.debug(f'Received data from serial {index}: {data}')
        # self.view.log_message(f'Received data from serial {index}: {data}')
    
    def closeEvent(self, event):
        for thread in self.threads:
            thread.quit()
            thread.wait()
        for receive_thread in self.receive_threads:
            if receive_thread:
                receive_thread.stop()
                receive_thread.wait()
        for i in range(1, 7):
            self.model.close_serial_port(i)
        event.accept()

    def show(self):
        self.view.show()
