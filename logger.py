'''
    日志模块
'''
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import datetime

# 创建一个模块级别的日志记录器
logger = logging.getLogger(__name__)

# 配置日志记录器
logger.setLevel(logging.DEBUG)

# 当前日期
current_date = datetime.date.today()
formatted_date = current_date.strftime('%Y%m%d')

path = './save_data'
if not os.path.exists(path):
    os.makedirs(path)

# 创建一个按天切割的文件处理器
file_handler = TimedRotatingFileHandler(
    filename=f"{path}/app.log",
    when="D",  # 按天切割
    interval=1,  # 每天切割一次
    backupCount=7  # 保留最近 7 天的日志文件
)
file_handler.setLevel(logging.DEBUG)

# 创建一个格式化器，用于设置日志消息的格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 将处理程序添加到日志记录器
logger.addHandler(file_handler)

logging.basicConfig(format = '%(asctime)s.%(msecs)03d [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                    datefmt = '%m-%d %H:%M:%S')

