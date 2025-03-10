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
        self.last_receive_time = time.time()  # 为每个串口初始化时间戳
        self.serial = SerialOperator()
        # self.data_callbacks = [None] * 6

    def get_all_serials(self):
        return SerialOperator().list_available_ports()

    def open_serial_port(self, port_name):
        self.last_receive_time = time.time()  # 更新时间戳
        return self.serial.open_serial_port(port_name)

    def close_serial_port(self):
        self.serial.close_serial_port()

    def is_serial_open(self):
        return self.serial.is_open

    def receive_data(self):
        '''
        接收数据。
        '''
        # TODO 这里是模拟数据
        # data = self.generate_mock_data()
        data = self.serial.receive_data()
        if data:
            self.last_receive_time = time.time()  # 更新时间戳
        return data
        
    def receive_data_with_message(self, data_size):
        '''
        接收数据。
        '''
        def update_timestamp():
            # 封装更新时间戳的逻辑
            self.last_receive_time = time.time()

        def check_data_length(data, expected_size):
            # 检查数据长度并记录日志
            if len(data) == expected_size or data == b'':
                return None
            elif len(data) > expected_size:
                logger.warning("接收到的数据长度超过预期，预期长度: %d，实际长度: %d", expected_size, len(data))
                return 'receive data length is too long, please check your serial port'
            else:
                logger.warning("接收到的数据长度不足，预期长度: %d，实际长度: %d", expected_size, len(data))
                return 'receive data length is too short, please check your serial port'

        # 第一次接收数据
        data = self.serial.receive_data()
        message = None
        if data:
            update_timestamp()
            message = check_data_length(data, data_size)
            if message:
                return None, message

            # 如果第一次接收的数据长度不够，再接收一次
            remaining_size = data_size - len(data)
            if remaining_size > 0:
                second_data = self.serial.receive_data(remaining_size)
                if second_data:
                    update_timestamp()
                    data += second_data
                    message = check_data_length(data, data_size)
                    if message:
                        return None, message

        return data, message

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