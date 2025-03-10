'''
    日志模块
'''
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import datetime

# 删除过期日志文件
def delete_expired_logs(log_dir, backup_count=7):
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
    if len(log_files) > backup_count:
        for log_file in log_files[:-backup_count]:
            os.remove(os.path.join(log_dir, log_file))


# 创建一个模块级别的日志记录器
logger = logging.getLogger(__name__)

# 配置日志记录器
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

# 当前日期
current_date = datetime.date.today()
formatted_date = current_date.strftime('%Y%m%d')

path = './save_data'
if not os.path.exists(path):
    os.makedirs(path)

backup_day = 7


# 在程序开始时删除过期日志
delete_expired_logs(path, backup_day)            

# 创建一个按天切割的文件处理器
file_handler = TimedRotatingFileHandler(
    filename=f"{path}/app_{formatted_date}.log",
    when="D",  # 按天切割
    interval=1,  # 每天切割一次
    backupCount=backup_day,  # 保留最近 7 天的日志文件
    encoding='utf-8'  # 指定日志文件编码为 UTF-8
)
file_handler.setLevel(logging.DEBUG)

# 创建一个格式化器，用于设置日志消息的格式
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-5s - [%(filename)16s:%(lineno)-3d] - %(message)s')
file_handler.setFormatter(formatter)

# 将处理程序添加到日志记录器
logger.addHandler(file_handler)

logging.basicConfig(format = '%(asctime)s.%(msecs)03d [%(levelname)-5s] [%(filename)16s:%(lineno)-3d] %(message)s',
                    datefmt = '%m-%d %H:%M:%S')

