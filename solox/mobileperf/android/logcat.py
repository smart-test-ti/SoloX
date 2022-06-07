# -*- coding: utf-8 -*-
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
'''logcat监控器 
'''
import os,sys,csv
import re
import time

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))

from mobileperf.android.tools.androiddevice import AndroidDevice
from mobileperf.common.basemonitor import Monitor
from mobileperf.common.utils import TimeUtils,FileUtils
from mobileperf.common.utils import ms2s
from mobileperf.common.log import logger
from mobileperf.android.globaldata import RuntimeData

class LogcatMonitor(Monitor):
    '''logcat监控器
    '''
    def __init__(self, device_id, package=None, **regx_config):
        '''构造器
        
        :param str device_id: 设备id
        :param list package : 监控的进程列表，列表为空时，监控所有进程
        :param dict regx_config : 日志匹配配置项{conf_id = regx}，如：AutoMonitor=ur'AutoMonitor.*:(.*), cost=(\d+)'
        '''
        super(LogcatMonitor, self).__init__(**regx_config)
        self.package = package    # 监控的进程列表
        self.device_id = device_id
        self.device = AndroidDevice(device_id)  # 设备
        self.running = False    # logcat监控器的启动状态(启动/结束)
        self.launchtime = LaunchTime(self.device_id, self.package)
        self.exception_log_list = []
        self.start_time = None

        self.append_log_line_num = 0
        self.file_log_line_num = 0
        self.log_file_create_time = None
    
    def start(self,start_time):
        '''启动logcat日志监控器 
        '''
        self.start_time = start_time
        # 注册启动日志处理回调函数为handle_lauchtime
        self.add_log_handle(self.launchtime.handle_launchtime)
        logger.debug("logcatmonitor start...")
        # 捕获所有进程日志
        # https://developer.android.com/studio/command-line/logcat #alternativeBuffers
        # 默认缓冲区 main system crash,输出全部缓冲区
        if not self.running:
            self.device.adb.start_logcat(RuntimeData.package_save_path, [], ' -b all')
            time.sleep(1)
            self.running = True
    
    def stop(self):
        '''结束logcat日志监控器
        '''
        logger.debug("logcat monitor: stop...")
        self.remove_log_handle(self.launchtime.handle_launchtime)  # 删除回调
        logger.debug("logcat monitor: stopped")
        if self.exception_log_list:
            self.remove_log_handle(self.handle_exception)
        self.device.adb.stop_logcat()
        self.running = False

    def parse(self, file_path):
        pass

    def set_exception_list(self,exception_log_list):
        self.exception_log_list = exception_log_list

    def add_log_handle(self, handle):
        '''添加实时日志处理器，每产生一条日志，就调用一次handle
        '''
        self.device.adb._logcat_handle.append(handle)
        
    def remove_log_handle(self, handle):
        '''删除实时日志处理器
        '''
        self.device.adb._logcat_handle.remove(handle)

    def handle_exception(self, log_line):
        '''
        这个方法在每次有log时回调
        :param log_line:最近一条的log 内容
        异常日志写一个文件
        :return:void
        '''

        for tag in self.exception_log_list:
            if tag in log_line:
                logger.debug("exception Info: " + log_line)
                tmp_file = os.path.join(RuntimeData.package_save_path, 'exception.log')
                with open(tmp_file, 'a+',encoding="utf-8") as f:
                    f.write(log_line + '\n')
                #     这个路径 空格会有影响
                process_stack_log_file = os.path.join(RuntimeData.package_save_path, 'process_stack_%s_%s.log' % (
                self.package, TimeUtils.getCurrentTimeUnderline()))
                # 如果进程挂了，pid会变 ，抓变后进程pid的堆栈没有意义
                # self.logmonitor.device.adb.get_process_stack(self.package,process_stack_log_file)
                if RuntimeData.old_pid:
                    self.device.adb.get_process_stack_from_pid(RuntimeData.old_pid, process_stack_log_file)


class LaunchTime(object):

    def __init__(self,deviceid, packagename = ""):
        # 列表的容积应该不用担心，与系统有一定关系，一般存几十万条数据没问题的
        self.launch_list = [("datetime","packagenme/activity","this_time(s)","total_time(s)","launchtype")]
        self.packagename = packagename

    def handle_launchtime(self, log_line):
        '''
        这个方法在每次一个启动时间的log产生时回调
        :param log_line:最近一条的log 内容
        :param tag:启动的方式，是normal的启动，还是自定义方式的启动：fullydrawnlaunch
        #如果监控到到fully drawn这样的log，则优先统计这种log，它表示了到起始界面自定义界面的启动时间
        :return:void
        '''
        # logger.debug(log_line)
        # 08-28 10:57:30.229 18882 19137 D IC5: CLogProducer == > code = 0, uuid = 4FE71E350379C64611CCD905938C10CA, eventType = performance, eventName = am_activity_launch_timeme, \
        #    log_time = 2019-08-28 10:57:30.229, contextInfo = {"tag": "am_activity_launch_time", "start_time": "2019-08-28 10:57:16",
        #                              "activity_name_original": "com.android.settings\/.FallbackHome",
        #                              "activity_name": "com.android.settings#com.android.settings.FallbackHome",
        #                              "this_time": "916", "total_time": "916", "start_type": "code_start",
        #                              "gmt_create": "2019-08-28 10:57:16.742", "uploadtime": "2019-08-28 10:57:30.173",
        #                              "boottime": "2019-08-28 10:57:18.502", "firstupload": "2019-08-28 10:57:25.733"}
        ltag = ""
        if ("am_activity_launch_time" in log_line or "am_activity_fully_drawn_time" in log_line):
            # 最近增加的一条如果是启动时间相关的log，那么回调所有注册的_handle
            if "am_activity_launch_time" in log_line:
                ltag = "normal launch"
            elif "am_activity_fully_drawn_time" in log_line:
                ltag = "fullydrawn launch"
            logger.debug("launchtime log:"+log_line)
        if ltag:
            content = []
            timestamp = time.time()
            content.append(TimeUtils.formatTimeStamp(timestamp))
            temp_list = log_line.split()[-1].replace("[", "").replace("]", "").split(',')[2:5]
            for i in range(len(temp_list)):
                content.append(temp_list[i])
            content.append(ltag)
            logger.debug("Launch Info: "+str(content))
            if len(content) == 5:
                content = self.trim_value(content)
                if content:
                    self.update_launch_list(content,timestamp)

    def trim_value(self, content):
        try:
            content[2] = ms2s(float(content[2]))#将this_time转化单位转化为s
            content[3] = ms2s(float(content[3]))#将total_time 转化为s
        except Exception as e:
            logger.error(e)
            return []
        return content

    def update_launch_list(self, content,timestamp):
        # if self.packagename in content[1]:
        self.launch_list.append(content)
        tmp_file = os.path.join(RuntimeData.package_save_path, 'launch_logcat.csv')
        perf_data = {"task_id":"",'launch_time':[],'cpu':[],"mem":[],
                         'traffic':[], "fluency":[],'power':[],}
        dic = {"time": timestamp,
                 "act_name": content[1],
                 "this_time": content[2],
                 "total_time": content[3],
                 "launch_type": content[4]}
        perf_data['launch_time'].append(dic)
        # perf_queue.put(perf_data)

        with open(tmp_file,"a+",encoding="utf-8") as f:
            csvwriter = csv.writer(f, lineterminator='\n')#这种方式可以去除csv的空行
            logger.debug("save launchtime data to csv: " + str(self.launch_list))
            csvwriter.writerows(self.launch_list)
            del self.launch_list[:]

if __name__ == '__main__':
    logcat_monitor = LogcatMonitor("85I7UO4PFQCINJL7", "com.yunos.tv.alitvasr")
    # 如果有异常日志标志，才启动这个模块
    exceptionlog_list=["fatal exception","has died"]
    if exceptionlog_list:
        logcat_monitor.set_exception_list(exceptionlog_list)
        logcat_monitor.add_log_handle(logcat_monitor.handle_exception)
    start_time = TimeUtils.getCurrentTimeUnderline()
    RuntimeData.package_save_path = os.path.join(FileUtils.get_top_dir(), 'results', "com.yunos.tv.alitvasr", start_time)
    logcat_monitor.start(start_time)
