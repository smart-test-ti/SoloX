#encoding:utf-8
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import os
import re

import sys,csv
import threading
import random
import time
import traceback

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))
from mobileperf.common.log import logger
from mobileperf.android.tools.androiddevice import AndroidDevice
from mobileperf.android.globaldata import RuntimeData
from mobileperf.common.utils import TimeUtils

class DeviceMonitor(object):
    '''
    一个监控类，监控手机中的一些状态变化，目前监控应用是否卸载，获取前台正在活动的activity
    '''
    def __init__(self, device_id, packagename, interval = 1.0,main_activity=[],activity_list=[],event=None,activity_queue = None):
        ''''
        :param list main_activity 指定模块的主入口
        :param list activity_list : 限制默认范围的activity列表，默认为空，则不限制
        '''
        self.uninstall_flag = event
        self.device = AndroidDevice(device_id)
        self.packagename = packagename
        self.interval = interval
        self.main_activity = main_activity
        self.activity_list = activity_list
        self.stop_event = threading.Event()
        self.activity_queue = activity_queue
        self.current_activity = None


    def start(self, starttime):
        self.activity_monitor_thread = threading.Thread(target=self._activity_monitor_thread)
        self.activity_monitor_thread.start()
        logger.debug("DeviceMonitor activitymonitor has started...")

        # self.uninstaller_checker_thread = threading.Thread(target=self._uninstaller_checker_thread)
        # self.uninstaller_checker_thread.start()
        # logger.debug("DeviceMonitor uninstaller checker has started...")

    def stop(self):
        if self.activity_monitor_thread.isAlive():
            self.stop_event.set()
            self.activity_monitor_thread.join(timeout=1)
            self.activity_monitor_thread = None
            if self.activity_queue:
                self.activity_queue.task_done()
        logger.debug("DeviceMonitor stopped!")


    def _activity_monitor_thread(self):
        activity_title = ("datetime", "current_activity")
        self.activity_file = os.path.join(RuntimeData.package_save_path, 'current_activity.csv')
        try:
            with open(self.activity_file, 'a+') as af:
                csv.writer(af, lineterminator='\n').writerow(activity_title)
        except Exception as e:
            logger.error("file not found: " + str(self.activity_file))

        while not self.stop_event.is_set():
            try:
                before = time.time()
                self.current_activity = self.device.adb.get_current_activity()
                collection_time = time.time()
                activity_list = [collection_time, self.current_activity]
                if self.activity_queue:
                    logger.debug("activity monitor thread activity_list: " + str(activity_list))
                    self.activity_queue.put(activity_list)
                if self.current_activity:
                    logger.debug("current activity: " + self.current_activity)
                    if self.main_activity and self.activity_list:
                        if self.current_activity not in self.activity_list:
                            start_activity = self.packagename + "/" + self.main_activity[
                                random.randint(0, len(self.main_activity) - 1)]
                            logger.debug("start_activity:" + start_activity)
                            self.device.adb.start_activity(start_activity)
                    activity_tuple=(TimeUtils.getCurrentTime(),self.current_activity)
                    # 写文件
                    try:
                        with open(self.activity_file, 'a+',encoding="utf-8") as writer:
                            writer_p = csv.writer(writer, lineterminator='\n')
                            writer_p.writerow(activity_tuple)
                    except RuntimeError as e:
                        logger.error(e)
                time_consume = time.time() - before
                delta_inter = self.interval - time_consume
                logger.debug("get app activity time consumed: " + str(time_consume))
                if delta_inter > 0 :
                    time.sleep(delta_inter)
            except Exception as e:
                s = traceback.format_exc()
                logger.debug(s)  # 将堆栈信息打印到log中
                if self.activity_queue:
                    self.activity_queue.task_done()

    # 这个检查频率不用那么高
    def _uninstaller_checker_thread(self):
        '''
        这个方法用轮询的方式查询指定的应用是否被卸载，一旦卸载会往主线程发送一个卸载的信号，终止程序
        :return:
        '''
        while not self.stop_event.is_set():
            before = time.time()
            is_installed = self.device.adb.is_app_installed(self.packagename)
            if not is_installed:
                if self.uninstall_flag and isinstance(self.uninstall_flag, threading._Event):
                    logger.debug("uninstall flag is set, as the app has checked uninstalled!")
                    self.uninstall_flag.set()
            time_consume = time.time() - before
            delta_inter = self.interval*10 - time_consume
            logger.debug("check installed app: " + self.packagename +", time consumed: " + str(time_consume) + ", is installed: " + str(is_installed))
            if delta_inter > 0:
                time.sleep(delta_inter)


if __name__ == '__main__':
    monitor = DeviceMonitor("NVGILZSO99999999", "com.taobao.taobao", 2)
    monitor.start(time.time())
    time.sleep(60)
    monitor.stop()
