# encoding:utf-8
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import csv
import os
import re
import sys
import threading
import time
import random
import traceback

BaseDir = os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir, '../..'))

from mobileperf.android.tools.androiddevice import AndroidDevice
from mobileperf.common.utils import TimeUtils,FileUtils
from mobileperf.common.log import logger
from mobileperf.android.globaldata import RuntimeData


class Monkey(object):
    '''
    monkey执行器
    '''

    def __init__(self, device_id, package=None,timeout=1200000000):
        '''构造器

        :param str device_id: 设备id
        :param str process : monkey测试的包名
        :param timeout : monkey时长 单位 分钟 默认无穷大
        '''
        self.package = package
        self.device = AndroidDevice(device_id)  # 设备
        self.running = False  # monkey监控器的启动状态(启动/结束)
        self.timeout = timeout
        self._stop_event = threading.Event()

    def start(self,start_time):
        '''启动monkey
        '''
        self.start_time = start_time
        if not self.running:
            self.running = True
            # time.sleep(1)
            self.start_monkey(self.package,self.timeout)

    def stop(self):
        '''结束monkey
        '''
        self.stop_monkey()

    def start_monkey(self, package,timeout):
        '''运行monkey进程
        '''
        if hasattr(self, '_monkey_running') and self.running == True:
            logger.warn(u'monkey process have started,not need start')
            return
        self.monkey_cmd = 'monkey -p %s -v -v -v -s 1000 ' \
                          '--ignore-crashes --ignore-timeouts --ignore-security-exceptions ' \
                          '--kill-process-after-error --pct-appswitch 20 --pct-touch 40 ' \
                          '--pct-motion 10 --pct-trackball 0 --pct-anyevent 10 --pct-flip 0 --pct-pinchzoom 0 ' \
                          '--throttle 1000 %s' % (package, str(timeout))
        self._log_pipe = self.device.adb.run_shell_cmd(self.monkey_cmd, sync=False)
        self._monkey_thread = threading.Thread(target=self._monkey_thread_func, args=[RuntimeData.package_save_path])
        # self._monkey_thread.setDaemon(True)
        self._monkey_thread.start()


    def stop_monkey(self):
        self.running = False
        logger.debug("stop monkey")
        if hasattr(self, '_log_pipe'):
            if self._log_pipe.poll() == None: #判断logcat进程是否存在
                self._log_pipe.terminate()

    def _monkey_thread_func(self,save_dir):
        '''获取monkey线程，保存monkey日志，monkey Crash日志暂不处理，后续有需要再处理
        '''
        self.append_log_line_num = 0
        self.file_log_line_num = 0
        self.log_file_create_time = None
        log_is_none = 0
        logs = []
        logger.debug("monkey_thread_func")
        if RuntimeData.start_time is None:
            RuntimeData.start_time = TimeUtils.getCurrentTime()
        while self.running:
            try:
                log = self._log_pipe.stdout.readline().strip()
                if not isinstance(log, str):
                    # 先编码为unicode
                    try:
                        log = str(log, "utf8")
                    except Exception as e:
                        log = repr(log)
                        logger.error('str error:' + log)
                        logger.error(e)
                if log:
                    logs.append(log)
                    self.append_log_line_num = self.append_log_line_num + 1
                    self.file_log_line_num = self.file_log_line_num + 1
                    # if self.append_log_line_num > 1000:
                    if self.append_log_line_num > 100:
                        if not self.log_file_create_time:
                            self.log_file_create_time = TimeUtils.getCurrentTimeUnderline()
                        log_file = os.path.join(save_dir,
                                                'monkey_%s.log' % self.log_file_create_time)
                        self.append_log_line_num = 0
                        # 降低音量，避免音量过大，导致语音指令失败
                        self.device.adb.run_shell_cmd("input keyevent 25")
                        self.save(log_file, logs)
                        logs = []
                    # 新建文件
                    if self.file_log_line_num > 600000:
                        # if self.file_log_line_num > 200:
                        self.file_log_line_num = 0
                        self.log_file_create_time = TimeUtils.getCurrentTimeUnderline()
                        log_file = os.path.join(save_dir, 'monkey_%s.log' % self.log_file_create_time)
                        self.save(log_file, logs)
                        logs = []
                else:
                    log_is_none = log_is_none + 1
                    if log_is_none % 1000 == 0:
                        logger.info("log is none")
                        if not self.device.adb.is_process_running("com.android.commands.monkey") and self.running:
                            self.device.adb.kill_process("com.android.commands.monkey")
                            self._log_pipe = self.device.adb.run_shell_cmd(self.monkey_cmd, sync=False)
            except:
                logger.error("an exception hanpend in monkey thread, reason unkown!")
                s = traceback.format_exc()
                logger.debug(s)

    def save(self, save_file_path, loglist):
        monkey_file = os.path.join(save_file_path)
        with open(monkey_file, 'a+', encoding="utf-8") as log_f:
            for log in loglist:
                log_f.write(log + "\n")


if __name__ == "__main__":
    test_pacakge_list = ["com.alibaba.ailabs.genie.musicplayer","com.alibaba.ailabs.genie.contacts","com.alibaba.ailabs.genie.launcher",
            "com.alibaba.ailabs.genie.shopping","com.youku.iot"]
    device = AndroidDevice()
    # device.adb.kill_process("monkey")
    # for i in range(0, 10):
    #     for package in test_pacakge_list:
    #         monkey = Monkey("",package,1200000000)
    #         monkey.start(TimeUtils.getCurrentTimeUnderline())
    #         time.sleep(60*60*2)
    #         monkey.stop()
    start_time = TimeUtils.getCurrentTimeUnderline()
    logger.debug(start_time)
    RuntimeData.top_dir = FileUtils.get_top_dir()
    RuntimeData.package_save_path = os.path.join(RuntimeData.top_dir, 'results', "com.alibaba.ailabs.genie.contacts", start_time)
    main_activity = ["com.alibaba.ailabs.genie.contacts.MainActivity"]
    activity_list = ["com.alibaba.ailabs.genie.contacts.MainActivity",
                     "com.alibaba.ailabs.genie.contacts.cmd.CmdDispatchActivity",
                     "com.alibaba.ailabs.genie.contacts.cmd.transform.VoipToPstnActivity",
                     "com.alibaba.ailabs.genie.contacts.add.AddContactsActivity"]
    monkey = Monkey("WST4DYVWKBFEV8Q4","com.alibaba.ailabs.genie.smartapp")
    monkey.start(start_time)
