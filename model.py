from serial_handle import SerialOperator
from logger import logger


class SerialModel:
    def __init__(self):
        self.serials = [SerialOperator() for _ in range(6)]
        self.data_callbacks = [None] * 6

    def get_all_serials(self):
        return SerialOperator().list_available_ports()

    def open_serial_port(self, index, port_name, baudrate, timeout):
        return self.serials[index - 1].open_serial_port(port_name, baudrate, timeout)

    def close_serial_port(self, index):
        self.serials[index - 1].close_serial_port()

    def is_serial_open(self, index):
        return self.serials[index - 1].is_open

    def receive_data(self, index):
        return self.serials[index - 1].receive_data()

    def register_data_callback(self, index, callback):
        '''
        注册数据接收回调函数。

        :param index: 串口索引，范围从 1 到 6。
        :param callback: 回调函数，接收两个参数：index 和 data。
        '''
        self.data_callbacks[index - 1] = callback

    def process_received_data(self, index):
        '''
        处理接收到的数据，调用注册的回调函数。

        :param index: 串口索引，范围从 1 到 6。
        '''
        if self.data_callbacks[index - 1]:
            data = self.receive_data(index)
            if data:
                self.data_callbacks[index - 1](index, data)