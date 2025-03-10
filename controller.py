'''
    controller
    业务逻辑处理
'''
import time

from PyQt5.QtCore import QThread, QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QPushButton

from model import SerialModel
from view import SerialView

from logger import logger

class SerialThread(QThread):
    '''
    自定义线程类，用于打开串口并接收解析数据
    '''
    result_signal = pyqtSignal(str, bool, str)  # 自定义信号，用于传递打开串口结果给主线程
    DATA_10_SERIAL = 'CYPD7291'      # 用于log输出时区分串口
    DATA_10_BYTES = 10
    DATA_6_SERIAL = 'CYPD7299'       # 用于log输出时区分串口
    DATA_6_BYTES = 6
    data_received_10_bytes = pyqtSignal(str, str, str, str, str, str, str, str, str, str, str, str, str, str)
    data_received_6_bytes = pyqtSignal(str, str, str, str, str, str, str, str)
    serial_closed_signal = pyqtSignal(str, str)  # 自定义信号，用于通知界面串口已关闭
    serial_message_signal = pyqtSignal(str)  # 自定义信号，用于传递串口消息给主线程

    def __init__(self, model: SerialModel, data_length, port_name):
        super().__init__()
        self.model = model
        self.data_length = data_length
        self.port_name = port_name
        self._running = True
        self.name = ''
        self.set_serial_name()
        logger.debug('创建打开串口%s并接收解析数据子线程%d', self.name, id(self))

    def run(self):
        result = self.model.open_serial_port(self.port_name)
        self.result_signal.emit(self.name, result, self.port_name)

        while self._running and self.model.is_serial_open():
            try:
                data, message = self.model.receive_data_with_message(self.data_length)
                if data and len(data) == self.data_length:
                    if self.data_length == self.DATA_10_BYTES:
                        usb_c1_pow = f'{data[0]}'
                        usb_c1_vbus_vol = f'{round(data[1] / 10, 1)}'
                        usb_c1_vbus_cur = f'{round(data[2] / 10, 1)}'
                        usb_c1_cur_pow = f'{round(data[1] * data[2] / 100, 2)}'
                        usb_c2_pow = f'{data[3]}'
                        usb_c2_vbus_vol = f'{round(data[4] / 10, 1)}'
                        usb_c2_vbus_cur = f'{round(data[5] / 10, 1)}'
                        usb_c2_cur_pow = f'{round(data[4] * data[5] / 100, 2)}'
                        usb1_vbus_vol = f'{round(data[6] / 10, 1)}'
                        usb1_vbus_cur = f'{round(data[7] / 10, 1)}'
                        usb1_cur_pow = f'{round(data[8] * data[9] / 100, 2)}'
                        usb2_vbus_vol = f'{round(data[8] / 10, 1)}'
                        usb2_vbus_cur = f'{round(data[9] / 10, 1)}'
                        usb2_cur_pow = f'{round(data[8] * data[9] / 100, 2)}'

                        # 触发 10 字节数据接收信号
                        self.data_received_10_bytes.emit(
                            usb_c1_pow, usb_c1_vbus_vol, usb_c1_vbus_cur, usb_c1_cur_pow, 
                            usb_c2_pow, usb_c2_vbus_vol, usb_c2_vbus_cur, usb_c2_cur_pow,
                            usb1_vbus_vol, usb1_vbus_cur, usb1_cur_pow, 
                            usb2_vbus_vol, usb2_vbus_cur, usb2_cur_pow
                        )
                    elif self.data_length == self.DATA_6_BYTES:
                        # 假设这里处理 6 字节数据
                        usb4_c1_pow = f'{data[0]}'
                        usb4_c1_vbus_vol = f'{round(data[1] / 10, 1)}'
                        usb4_c1_vbus_cur = f'{round(data[2] / 10, 1)}'
                        usb4_c1_cur_pow = f'{round(data[1] * data[2] / 100, 2)}'
                        usb4_c2_pow = f'{data[3]}'
                        usb4_c2_vbus_vol = f'{round(data[4] / 10, 1)}'
                        usb4_c2_vbus_cur = f'{round(data[5] / 10, 1)}'
                        usb4_c2_cur_pow = f'{round(data[4] * data[5] / 100, 2)}'

                        # 触发 6 字节数据接收信号
                        self.data_received_6_bytes.emit(
                            usb4_c1_pow, usb4_c1_vbus_vol, usb4_c1_vbus_cur, usb4_c1_cur_pow, 
                            usb4_c2_pow, usb4_c2_vbus_vol, usb4_c2_vbus_cur, usb4_c2_cur_pow
                        )
                if message:
                    self.serial_message_signal.emit(f'{self.name} {message}')
            except Exception as e:
                logger.error('Error receiving data from serial %s: %s', self.name, e)
            time.sleep(0.1)
        self.stop()


    def restart(self, port_name, data_length):
        '''
        重启线程
        '''
        if self.isRunning():
            self.stop()
            self.wait()  # 等待线程结束

        self._running = True
        self.port_name = port_name
        self.data_length = data_length
        self.set_serial_name()
        self.start()
        logger.debug('%s串口子线程restart %d', self.name, id(self))

    def set_serial_name(self):
        '''
        根据串口长度设置串口名称
        '''
        if self.data_length == self.DATA_10_BYTES:
            self.name = self.DATA_10_SERIAL
        elif self.data_length == self.DATA_6_BYTES:
            self.name = self.DATA_6_SERIAL

    def stop(self):
        logger.debug('串口子线程%d stop', id(self))
        self._running = False
        self.model.close_serial_port()  # 关闭串口
        self.serial_closed_signal.emit(self.name, self.port_name)  # 发送串口关闭信号

    def __del__(self):
        logger.debug('串口子线程%d被销毁', id(self))

class SerialController(QObject):
    '''
        主线程
        串口1对应10字节数据
        串口2对应6字节数据
    '''
    def __init__(self, title, myappid, icon_path):
        super().__init__()  # 调用父类的构造函数
        logger.debug('程序开始运行')
        logger.debug('Controller ID in SerialController: %s', id(self))
        self.view = SerialView(title, myappid, icon_path)
        self.view.controller = self
        self.initUI()
        self.connect_serial_msg()

        self.model_10 = SerialModel()
        self.model_6 = SerialModel()
        # 线程池
        self.thread_10 = None
        self.thread_6 = None
        self.threads = [self.thread_10, self.thread_6]

        self.receive_thread_10_flag = False
        self.receive_thread_6_flag = False
        # 启动定时器，每隔一定时间检查一次串口数据是否超时
        self.serial_timer = QTimer(self)
        self.serial_timer.timeout.connect(self.check_serial_data)
        self.serial_timer.start(1000)  # 每100豪秒检查一次

    def initUI(self):
        # 初始化串口列表
        pass

    def connect_serial_msg(self):
        self.view.ui.connectButton1.clicked.connect(self.handle_serial1_connect)
        self.view.ui.connectButton2.clicked.connect(self.handle_serial2_connect)

    def handle_serial_connect(self, model:SerialModel, button:QPushButton, combobox:QComboBox, thread:QThread, data_length, serial_name):
        '''
        处理串口连接按钮的点击事件的通用方法。

        :param button: 连接按钮
        :param combobox: 串口选择下拉框
        :param thread: 串口线程
        :param data_length: 数据长度
        :param serial_name: 串口名称
        '''
        port_name = combobox.currentText()
        if not port_name:
            logger.error('%s未选择串口', serial_name)
            return

        if button.text() == SerialView.BTN_DISCONNECT:
            # 如果线程正在运行，关闭串口
            if thread and thread.isRunning():
                thread.stop()
                thread.wait()
                self.view.log_message(f'{serial_name}关闭串口{port_name}')
                logger.info('%s 已关闭串口 %s', serial_name, port_name)
            # 串口断开后，设置下拉框可编辑
            button.setText(SerialView.BTN_CONNECT)
            combobox.setEnabled(True)
        else:
            # 如果线程未运行，打开串口
            if thread is None:
                thread = SerialThread(model, data_length, port_name)
                thread.result_signal.connect(self.handle_serial_open_result)
                thread.serial_closed_signal.connect(self.handle_serial_closed)
                thread.serial_message_signal.connect(self.view.log_message)
                if data_length == SerialThread.DATA_10_BYTES:
                    thread.data_received_10_bytes.connect(self.handle_received_10_data)
                elif data_length == SerialThread.DATA_6_BYTES:
                    thread.data_received_6_bytes.connect(self.handle_received_6_data)
            thread.restart(port_name, data_length)
            # 串口连接后，设置下拉框不可编辑
            combobox.setEnabled(False)
        return thread

    def handle_serial1_connect(self):
        '''
        处理串口1连接按钮的点击事件。
        '''
        self.thread_10 = self.handle_serial_connect(
            self.model_10,
            self.view.ui.connectButton1,
            self.view.ui.serialBox1,
            self.thread_10,
            SerialThread.DATA_10_BYTES,
            SerialThread.DATA_10_SERIAL
        )

    def handle_serial2_connect(self):
        '''
        处理串口2连接按钮的点击事件。
        '''
        self.thread_6 = self.handle_serial_connect(
            self.model_6,
            self.view.ui.connectButton2,
            self.view.ui.serialBox2,
            self.thread_6,
            SerialThread.DATA_6_BYTES,
            SerialThread.DATA_6_SERIAL
        )

    def update_ui_and_log(self, button, combobox, serial_name, port_name, success):
        '''
        更新界面按钮文本、组合框状态，并记录日志信息。

        :param button: 要更新文本的按钮
        :param combobox: 要更新启用状态的组合框
        :param serial_name: 串口名称
        :param port_name: 端口名称
        :param success: 打开串口是否成功
        '''
        if success:
            button.setText(SerialView.BTN_DISCONNECT)
            combobox.setEnabled(False)
            self.view.log_message(f'{serial_name}打开串口{port_name}成功')
            logger.info('%s 已打开串口 %s', serial_name, port_name)
        else:
            if button.text() == SerialView.BTN_DISCONNECT:
                message = f'{serial_name}串口{port_name}断开连接'
                self.view.log_message(message)
            else:
                message = f'{serial_name}打开串口{port_name}失败，请检查连接是否被占用'
                self.view.log_message(message, True)

            button.setText(SerialView.BTN_CONNECT)
            combobox.setEnabled(True)
            logger.error(message)

    def handle_serial_closed(self, serial_name, port_name):
        '''
        处理串口关闭信号。

        :param port_name: 关闭的串口端口名称
        '''
        if self.thread_10.name == serial_name:
            if self.view.ui.connectButton1.text() == SerialView.BTN_DISCONNECT:
                self.update_ui_and_log(self.view.ui.connectButton1, self.view.ui.serialBox1,
                    SerialThread.DATA_10_SERIAL, port_name, False)
        elif self.view.ui.connectButton2.text() == SerialView.BTN_DISCONNECT:
            if self.thread_6.isRunning():
                self.update_ui_and_log(self.view.ui.connectButton2, self.view.ui.serialBox2,
                    SerialThread.DATA_6_SERIAL, port_name, False)
            
    def handle_serial_open_result(self, serial_name, result, port_name):
        '''
        处理打开串口的结果，根据结果更新界面和记录日志。

        :param serial_name: 串口名称
        :param result: 打开串口的结果，True 表示成功，False 表示失败
        :param port_name: 端口名称
        '''
        if serial_name == SerialThread.DATA_10_SERIAL:
            self.update_ui_and_log(self.view.ui.connectButton1, self.view.ui.serialBox1,
                serial_name, port_name, result)
        elif serial_name == SerialThread.DATA_6_SERIAL:
            self.update_ui_and_log(self.view.ui.connectButton2, self.view.ui.serialBox2,
                serial_name, port_name, result)

    def handle_received_10_data(self, 
                            usb_c1_pow, usb_c1_vbus_vol, usb_c1_vbus_cur, usb_c1_cur_pow, 
                            usb_c2_pow, usb_c2_vbus_vol, usb_c2_vbus_cur, usb_c2_cur_pow,
                            usb1_vbus_vol, usb1_vbus_cur, usb1_cur_pow, 
                            usb2_vbus_vol, usb2_vbus_cur, usb2_cur_pow):
        '''
        处理接收到的 10 字节数据。

        :param usb_c1_pow: USB-C1 电源          对应Port1_Type C1
        :param usb_c1_vbus_vol: USB-C1 电压
        :param usb_c1_vbus_cur: USB-C1 电流
        :param usb1_cur_pow: USB1 当前功率       
        :param usb_c2_pow: USB-C2 电源          对应Port2_Type C2
        :param usb_c2_vbus_vol: USB-C2 电压
        :param usb_c2_vbus_cur: USB-C2 电流
        :param usb2_cur_pow: USB2 当前功率       
        :param usb1_vbus_vol: USB1 电压         对应Port5_WPC1
        :param usb1_vbus_cur: USB1 电流
        :param usb1_cur_pow: USB1 当前功率
        :param usb2_vbus_vol: USB2 电压         对应Port6_WPC2
        :param usb2_vbus_cur: USB2 电流
        :param usb2_cur_pow: USB2 当前功率       
        '''
        self.view.set_line_data(self.view.ui.powEdit1, usb_c1_pow)
        self.view.set_line_data(self.view.ui.volEdit1, usb_c1_vbus_vol)
        self.view.set_line_data(self.view.ui.curEdit1, usb_c1_vbus_cur)
        self.view.set_line_data(self.view.ui.curPowEdit1, usb_c1_cur_pow)

        self.view.set_line_data(self.view.ui.powEdit2, usb_c2_pow)
        self.view.set_line_data(self.view.ui.volEdit2, usb_c2_vbus_vol)
        self.view.set_line_data(self.view.ui.curEdit2, usb_c2_vbus_cur)
        self.view.set_line_data(self.view.ui.curPowEdit2, usb_c2_cur_pow)

        self.view.set_line_data(self.view.ui.volEdit5, usb1_vbus_vol)
        self.view.set_line_data(self.view.ui.curEdit5, usb1_vbus_cur)
        self.view.set_line_data(self.view.ui.curPowEdit5, usb1_cur_pow)

        self.view.set_line_data(self.view.ui.volEdit6, usb2_vbus_vol)
        self.view.set_line_data(self.view.ui.curEdit6, usb2_vbus_cur)
        self.view.set_line_data(self.view.ui.curPowEdit6, usb2_cur_pow)

    def handle_received_6_data(self, 
                            usb4_c1_pow, usb4_c1_vbus_vol, usb4_c1_vbus_cur, usb4_c1_cur_pow, 
                            usb4_c2_pow, usb4_c2_vbus_vol, usb4_c2_vbus_cur, usb4_c2_cur_pow):
        '''
        处理接收到的 6 字节数据。
        :param usb4_c1_pow: USB4-C1 电源         对应Port3_Type C3
        :param usb4_c1_vbus_vol: USB4-C1 电压
        :param usb4_c1_vbus_cur: USB4-C1 电流
        :param usb4_c2_pow: USB4-C2 电源         对应Port4_Type C4
        :param usb4_c2_vbus_vol: USB4-C2 电压
        :param usb4_c2_vbus_cur: USB4-C2 电流
        '''
        self.view.set_line_data(self.view.ui.powEdit3, usb4_c1_pow)
        self.view.set_line_data(self.view.ui.volEdit3, usb4_c1_vbus_vol)
        self.view.set_line_data(self.view.ui.curEdit3, usb4_c1_vbus_cur)
        self.view.set_line_data(self.view.ui.curPowEdit3, usb4_c1_cur_pow)

        self.view.set_line_data(self.view.ui.powEdit4, usb4_c2_pow)
        self.view.set_line_data(self.view.ui.volEdit4, usb4_c2_vbus_vol)
        self.view.set_line_data(self.view.ui.curEdit4, usb4_c2_vbus_cur)
        self.view.set_line_data(self.view.ui.curPowEdit4, usb4_c2_cur_pow)

    def check_serial_data(self):
        '''
        检查串口数据的事件。
        '''
        timeout_threshold = 10  # 超时阈值，单位为秒
        # 定义一个辅助函数来检查单个线程的数据接收情况
        def check_thread(thread:SerialThread, flags, led_indices):
            if thread and thread.isRunning():
                last_time = thread.model.last_receive_time
                current_time = time.time()
                if current_time - last_time < timeout_threshold:
                    flags[0] = True
                    for index in led_indices:
                        self.view.set_led(index, True)
                else:
                    if flags[0]:
                        self.view.log_message(f'{thread.name}未在{timeout_threshold}s内接收到数据，请检查连接', True)
                        flags[0] = False
                        logger.debug('串口 %s last_time: %s, current_time: %s, %ds 内未接收到数据', thread.name, last_time,
                                     current_time, timeout_threshold)
                    for index in led_indices:
                        self.view.set_led(index, False)
            else:
                for index in led_indices:
                    self.view.set_led(index, False)

        # 检查 10 字节数据的线程
        check_thread(self.thread_10, [self.receive_thread_10_flag], [1, 2, 5, 6])
        # 检查 6 字节数据的线程
        check_thread(self.thread_6, [self.receive_thread_6_flag], [3, 4])

    def cleanup(self):
        logger.debug('Controller %d clean up', id(self))
        for thread in self.threads:
            if thread:
                thread.stop()
                thread.quit()
                thread.wait()
                

    def show(self):
        self.view.show()
