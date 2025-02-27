'''
    model.py
'''
import time
import random
from serial_handle import SerialOperator
from logger import logger


class SerialModel:
    def __init__(self):
        logger.debug("Serial ID in SerialModel: %s", id(self))
        self.last_receive_time = [time.time()] * 6  # 为每个串口初始化时间戳
        self.serials = [SerialOperator() for _ in range(6)]
        # self.data_callbacks = [None] * 6

    def get_all_serials(self):
        return SerialOperator().list_available_ports()

    def open_serial_port(self, index, port_name, baudrate, timeout):
        self.last_receive_time[index - 1] = time.time()  # 更新时间戳
        return self.serials[index - 1].open_serial_port(port_name, baudrate, timeout)

    def close_serial_port(self, index):
        self.serials[index - 1].close_serial_port()

    def is_serial_open(self, index):
        return self.serials[index - 1].is_open

    def receive_data(self, index):
        
        # TODO 这里是模拟数据
        # data = self.generate_mock_data()
        data = self.serials[index - 1].receive_data()
        if data:
            self.last_receive_time[index - 1] = time.time()  # 更新时间戳
        return data

    # def register_data_callback(self, index, callback):
    #     '''
    #     注册数据接收回调函数。

    #     :param index: 串口索引，范围从 1 到 6。
    #     :param callback: 回调函数，接收两个参数：index 和 data。
    #     '''
    #     self.data_callbacks[index - 1] = callback

    # def process_received_data(self, index):
    #     '''
    #     处理接收到的数据，调用注册的回调函数。

    #     :param index: 串口索引，范围从 1 到 6。
    #     '''
    #     # 处理接收到的数据
        
    #     if self.data_callbacks[index - 1]:
    #         data = self.receive_data(index)
    #         if data:
    #             self.last_receive_time[index - 1] = time.time()  # 更新时间戳
    #             self.data_callbacks[index - 1](index, data)


    def generate_mock_data(self):
        try:
            keys = ['vol', 'cur', 'pow']
            # 随机选择 1 到 3 个指标
            selected_keys = random.sample(keys, random.randint(1, 3))
            data_parts = []
            for key in selected_keys:
                # 生成随机值
                value = round(random.uniform(4, 15), 2)
                data_parts.append(f"{key}={value}")
            return " ".join(data_parts).encode()
        except Exception as e:
            logger.error("生成模拟数据时出错: %s", e)
            return None