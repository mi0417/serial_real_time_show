import serial_handle
import serial.tools.list_ports

class SerialOperator:
    def __init__(self):
        self.serials = {}  # 使用字典存储串口对象，键为串口号

    def list_available_ports(self):
        ports = serial_handle.tools.list_ports.comports()
        return [port.device for port in ports]

    def open_serial_port(self, port, baudrate=9600, timeout=1):
        """
        打开指定的串口。如果该串口已经打开，则先关闭它再重新打开。

        :param port: 要打开的串口号，例如 'COM3' 或 '/dev/ttyUSB0'
        :param baudrate: 串口通信的波特率，默认为 9600
        :param timeout: 串口操作的超时时间，单位为秒，默认为 1 秒
        :return: 若成功打开串口，返回 True；若打开失败，返回 False
        """
        # 检查该串口是否已经在打开状态
        if port in self.serials:
            try:
                # 若已打开，尝试关闭该串口
                self.serials[port].close()
            except serial_handle.SerialException:
                # 若关闭过程中出现异常，忽略该异常
                pass
            # 从已打开的串口字典中移除该串口
            del self.serials[port]
        try:
            # 尝试以指定的波特率和超时时间打开串口
            ser = serial_handle.Serial(port, baudrate, timeout=timeout)
            # 将打开的串口对象存储到字典中，键为串口号
            self.serials[port] = ser
            print(f"成功打开串口: {port}")
            return True
        except serial_handle.SerialException as e:
            # 若打开串口时出现异常，打印错误信息
            print(f"打开串口 {port} 失败: {e}")
            return False

    def close_serial_port(self, port):
        if port in self.serials:
            try:
                self.serials[port].close()
                print(f"串口 {port} 已关闭")
            except serial_handle.SerialException as e:
                print(f"关闭串口 {port} 时出错: {e}")
            del self.serials[port]
        else:
            print(f"串口 {port} 未打开")

    def send_data(self, port, data):
        if port in self.serials:
            ser = self.serials[port]
            if isinstance(data, str):
                data = data.encode()
            try:
                bytes_sent = ser.write(data)
                print(f"已向 {port} 发送 {bytes_sent} 字节数据: {data}")
                return bytes_sent
            except serial_handle.SerialException as e:
                print(f"向 {port} 发送数据时出错，尝试重新打开: {e}")
                self.open_serial_port(port)
        return 0

    def receive_data(self, port, size=None):
        if port in self.serials:
            ser = self.serials[port]
            try:
                if size is None:
                    data = ser.read(ser.in_waiting)
                else:
                    data = ser.read(size)
                if data:
                    print(f"从 {port} 接收到 {len(data)} 字节数据: {data}")
                return data
            except serial_handle.SerialException as e:
                print(f"从 {port} 接收数据时出错，尝试重新打开: {e}")
                self.open_serial_port(port)
        return b''
    def open_serial_port(self, port, baudrate=9600, timeout=1):
        """
        打开指定的串口。如果该串口已经打开，则先关闭它再重新打开。

        :param port: 要打开的串口号，例如 'COM3' 或 '/dev/ttyUSB0'
        :param baudrate: 串口通信的波特率，默认为 9600
        :param timeout: 串口操作的超时时间，单位为秒，默认为 1 秒
        :return: 若成功打开串口，返回 True；若打开失败，返回 False
        """
        # 检查该串口是否已经在打开状态
        if port in self.serials:
            try:
                # 若已打开，尝试关闭该串口
                self.serials[port].close()
            except serial_handle.SerialException:
                # 若关闭过程中出现异常，忽略该异常
                pass
            # 从已打开的串口字典中移除该串口
            del self.serials[port]
        try:
            # 尝试以指定的波特率和超时时间打开串口
            ser = serial_handle.Serial(port, baudrate, timeout=timeout)
            # 将打开的串口对象存储到字典中，键为串口号
            self.serials[port] = ser
            print(f"成功打开串口: {port}")
            return True
        except serial_handle.SerialException as e:
            # 若打开串口时出现异常，打印错误信息
            print(f"打开串口 {port} 失败: {e}")
            return False
