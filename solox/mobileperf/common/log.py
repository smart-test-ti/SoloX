# -*- coding: utf-8 -*-
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import os,time
import sys
import re
import logging
import logging.handlers
from logging.handlers import TimedRotatingFileHandler

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))

from mobileperf.common.utils import FileUtils
logger = logging.getLogger('mobileperf')
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter('[%(asctime)s]%(levelname)s:%(name)s:%(module)s:%(message)s')
streamhandler=logging.StreamHandler(sys.stdout)
streamhandler.setFormatter(fmt)
# 调试时改为DEBUG 发布改为 INFO
streamhandler.setLevel(logging.DEBUG)
dir = os.path.join(FileUtils.get_top_dir(), 'logs')
FileUtils.makedir(dir)
log_file = os.path.join(dir,"mobileperf_log")
log_file_handler = TimedRotatingFileHandler(filename=log_file, when="D", interval=1, backupCount=3)
log_file_handler.suffix = "%Y-%m-%d_%H-%M-%S.log"
log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}.log$")
log_file_handler.setFormatter(fmt)
log_file_handler.setLevel(logging.DEBUG)

logger.addHandler(streamhandler)
logger.addHandler(log_file_handler)

if __name__=="__main__":
	logger.debug("测试3！")