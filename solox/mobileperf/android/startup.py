#encoding:utf-8
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import re
import time,datetime
import os
import sys
import queue
import base64
import json
import subprocess
from shutil import copyfile,rmtree
# import objgraph
from configparser import ConfigParser

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))

from mobileperf.common.log import logger
from mobileperf.android.tools.androiddevice import AndroidDevice
from mobileperf.common.utils import TimeUtils,FileUtils,ZipUtils
from mobileperf.android.cpu_top import CpuMonitor
from mobileperf.android.meminfos import MemMonitor
from mobileperf.android.trafficstats import TrafficMonitor
from mobileperf.android.fps import FPSMonitor
from mobileperf.android.powerconsumption import PowerMonitor
from mobileperf.android.thread_num import ThreadNumMonitor
from mobileperf.android.fd import FdMonitor
from mobileperf.android.logcat import LogcatMonitor
from mobileperf.android.devicemonitor import DeviceMonitor
from mobileperf.android.monkey import Monkey
from mobileperf.android.globaldata import RuntimeData
from mobileperf.android.report import Report

class StartUp(object):

    def __init__(self, device_id=None, package=None,interval=None):
        RuntimeData.top_dir = os.getcwd()
        if "android" in RuntimeData.top_dir:
            RuntimeData.top_dir  = FileUtils.get_top_dir()
        logger.debug("RuntimeData.top_dir:"+RuntimeData.top_dir)
        self.config_dic = self.parse_data_from_config()
        RuntimeData.config_dic = self.config_dic
        self.serialnum = device_id if device_id != None else self.config_dic['serialnum']#代码中重新传入device_id 则会覆盖原来配置文件config.conf的值，主要为了debug方便
        self.packages = package if package != None else self.config_dic['package']#代码中重新传入package 则会覆盖原来配置文件config.conf的值，为了debug方便
        self.frequency = interval if interval != None else self.config_dic['frequency']#代码中重新传入interval 则会覆盖原来配置文件config.conf的值，为了debug方便
        self.timeout = self.config_dic['timeout']
        self.exceptionlog_list = self.config_dic["exceptionlog"]
        self.device = AndroidDevice(self.serialnum)
        # 如果config文件中 packagename为空，就获取前台进程，匹配图兰朵，测的app太多，支持配置文件不传package
        if not self.packages:
            # 进程名不会有#，转化为list
            self.packages = self.device.adb.get_foreground_process().split("#")
        RuntimeData.packages = self.packages

        #与终端交互有关
        self.keycode = ''
        self.pid = 0

        self._init_queue()
        self.monitors = []
        self.logcat_monitor = None

    def _init_queue(self):
        self.cpu_queue = queue.Queue()
        self.mem_queue = queue.Queue()
        self.power_queue = queue.Queue()
        self.traffic_queue = queue.Queue()
        self.fps_queue = queue.Queue()
        self.activity_queue = queue.Queue()
        self.fd_queue = queue.Queue()
        self.thread_queue = queue.Queue()

    def get_queue_dic(self):
        queue_dic = {}
        queue_dic['cpu_queue'] = self.cpu_queue
        queue_dic['mem_queue'] = self.mem_queue
        queue_dic['power_queue'] = self.power_queue
        queue_dic['traffic_queue'] = self.traffic_queue
        queue_dic['fps_queue'] = self.fps_queue
        queue_dic['fd_queue'] = self.fd_queue
        queue_dic['thread_queue'] = self.thread_queue
        queue_dic['activity_queue'] = self.activity_queue
        return queue_dic

    def add_monitor(self, monitor):
        self.monitors.append(monitor)

    def remove_monitor(self, monitor):
        self.monitors.remove(monitor)

    def parse_data_from_config(self):
        '''
        从配置文件中解析出需要的信息，包名，时间间隔，设备的序列号等
        :return:配置文件中读出来的数值的字典
        '''
        config_dic = {}
        configpath = os.path.join(RuntimeData.top_dir, "config.conf")
        logger.debug("configpath:%s" % configpath)
        if not os.path.isfile(configpath):
            logger.error("the config file didn't exist: " + configpath)
            raise RuntimeError("the config file didn't exist: " + configpath)
        # 避免windows会用系统默认的gbk打开
        with open(configpath, encoding="utf-8") as f:
            content = f.read()
            # Window下用记事本打开配置文件并修改保存后，编码为UNICODE或UTF-8的文件的文件头
            # 会被相应的加上\xff\xfe（\xff\xfe）或\xef\xbb\xbf，然后再传递给ConfigParser解析的时候会出错
            # ，因此解析之前，先替换掉
            content = re.sub(r"\xfe\xff", "", content)
            content = re.sub(r"\xff\xfe", "", content)
            content = re.sub(r"\xef\xbb\xbf", "", content)
            open(configpath, 'w', encoding="utf-8").write(content)
        paser = ConfigParser()
        paser.read(configpath, encoding="utf-8")
        config_dic = self.check_config_option(config_dic, paser, "Common", "package")
        config_dic = self.check_config_option(config_dic, paser, "Common", "pid_change_focus_package")
        config_dic = self.check_config_option(config_dic, paser, "Common","frequency")
        config_dic = self.check_config_option(config_dic, paser, "Common", "dumpheap_freq")
        config_dic = self.check_config_option(config_dic, paser, "Common", "timeout")
        config_dic = self.check_config_option(config_dic, paser, "Common", "serialnum")
        config_dic = self.check_config_option(config_dic, paser, "Common", "mailbox")
        config_dic = self.check_config_option(config_dic, paser, "Common", "exceptionlog")
        config_dic = self.check_config_option(config_dic, paser, "Common", "save_path")
        config_dic = self.check_config_option(config_dic,paser,"Common","phone_log_path")

        # 读取monkey配置
        config_dic = self.check_config_option(config_dic, paser, "Common", "monkey")
        config_dic = self.check_config_option(config_dic, paser, "Common", "main_activity")
        config_dic = self.check_config_option(config_dic, paser, "Common", "activity_list")

        logger.debug(config_dic)
        return config_dic

    def check_config_option(self, config_dic, parse, section, option):
        if parse.has_option(section, option):

            try:
                config_dic[option] = parse.get(section, option)
                if option == 'frequency':
                    config_dic[option] = (int)(parse.get(section, option))
                if option == 'dumpheap_freq':#dumpheap 的单位是分钟
                    config_dic[option] = (int)(parse.get(section, option))*60
                if option == 'timeout':#timeout 的单位是分钟
                    config_dic[option] = (int)(parse.get(section, option))*60
                if option in ["exceptionlog" ,"phone_log_path","space_size_check_path","package","pid_change_focus_package",
                              "watcher_users","main_activity","activity_list"]:
                    if option == "activity_list" or option == "main_activity":
                        config_dic[option] = parse.get(section, option).strip().replace("\n","").split(";")
                    else:
                        config_dic[option] = parse.get(section, option).split(";")
            except:#配置项中数值发生错误
                if option != 'serialnum':
                    logger.debug("config option error:"+option)
                    self._config_error()
                else:
                    config_dic[option] = ''
        else:#配置项没有配置
            if option not in ['serialnum',"main_activity","activity_list","pid_change_focus_package","shell_file"]:
                logger.debug("config option error:" + option)
                self._config_error()
            else:
                config_dic[option] = ''
        return config_dic

    def _config_error(self):
        logger.error("config error, please config it correctly")
        sys.exit(1)

    # @profile
    def run(self, time_out=None):
        self.clear_heapdump()
        # objgraph.show_growth()
#       对设备连接情况的检查
        if not self.serialnum:
#           androiddevice 没传  serialnum，默认执行adb shell
            logger.info("serialnum in config file is null,default get connected phone")
        is_device_connect = False
        for i in range(0,5):
            if self.device.adb.is_connected(self.serialnum):
                is_device_connect = True
                break
            else:
                logger.error("device not found:"+self.serialnum)
                time.sleep(2)
        if not is_device_connect:
            logger.error("after 5 times check,device not found:" + self.serialnum)
            return
  # 对是否安装被测app的检查 只在最开始检查一次
        if not self.device.adb.is_app_installed(self.packages[0]):
            logger.error("test app not installed:" + self.packages[0])
            return
        try:
            #初始化数据处理的类,将没有消息队列传递过去，以便获取数据，并处理
            # datahandle = DataWorker(self.get_queue_dic())
            # 将queue传进去，与datahandle那个线程交互
            self.add_monitor(CpuMonitor(self.serialnum, self.packages, self.frequency, self.timeout))
            self.add_monitor(MemMonitor(self.serialnum, self.packages, self.frequency, self.timeout))
            self.add_monitor(TrafficMonitor(self.serialnum, self.packages, self.frequency, self.timeout))
            # 软件方式 获取电量不准，已用硬件方案测试功耗
            # self.add_monitor(PowerMonitor(self.serialnum, self.frequency,self.timeout))
            self.add_monitor(FPSMonitor(self.serialnum,self.packages[0],self.frequency,self.timeout))
            # 6.0以下能采集到fd数据，7.0以上没权限
            if self.device.adb.get_sdk_version() <= 23:
                self.add_monitor(FdMonitor(self.serialnum, self.packages[0], self.frequency,self.timeout))
            self.add_monitor(ThreadNumMonitor(self.serialnum,self.packages[0],self.frequency,self.timeout))
            if self.config_dic["monkey"] == "true":
                self.add_monitor(Monkey(self.serialnum, self.packages[0]))
            if self.config_dic["main_activity"] and self.config_dic["activity_list"]:
                self.add_monitor(DeviceMonitor(self.serialnum, self.packages[0], self.frequency,self.config_dic["main_activity"],
                                               self.config_dic["activity_list"],RuntimeData.exit_event))

            if len(self.monitors):
                start_time = TimeUtils.getCurrentTimeUnderline()
                RuntimeData.start_time = start_time
                if self.config_dic["save_path"]:
                    RuntimeData.package_save_path = os.path.join(self.config_dic["save_path"], self.packages[0], start_time)
                else:
                    RuntimeData.package_save_path = os.path.join(RuntimeData.top_dir, 'results', self.packages[0], start_time)
                FileUtils.makedir(RuntimeData.package_save_path)
                self.save_device_info()
                for monitor in self.monitors:
                    #启动所有的monitors
                    try:
                        monitor.start(start_time)
                    except Exception as e:
                        logger.error(e)
                # logcat的代码可能会引起死锁，拎出来单独处理logcat
                try:
                    self.logcat_monitor = LogcatMonitor(self.serialnum, self.packages[0])
                    # 如果有异常日志标志，才启动这个模块
                    if self.exceptionlog_list:
                        self.logcat_monitor.set_exception_list(self.exceptionlog_list)
                        self.logcat_monitor.add_log_handle(self.logcat_monitor.handle_exception)
                    time.sleep(1)
                    self.logcat_monitor.start(start_time)
                except Exception as e:
                    logger.error(e)

                timeout = time_out if time_out != None else self.config_dic['timeout']
                endtime = time.time() + timeout
                while (time.time() < endtime):#吊着主线程防止线程中断
                    # 时间到或测试过程中检测到异常
                    if self.check_exit_signal_quit():
                        logger.error("app " + str(self.packages[0]) + " exit signal, quit!")
                        break
                    time.sleep(self.frequency)
                logger.debug("time is up,finish!!!")
                self.stop()

                # try:
                #     datahandle.stop()
                #     time.sleep(self.frequency*2)
                #     #               延迟一点时间结束上报，已让数据上报完
                #     # report.stop()
                # except:
                #     logger.debug("report or datahandle stop exception")
                # finally:
                #     logger.info("time is up, end")
                #     os._exit(0)

        except KeyboardInterrupt:#捕获键盘异常的事件，例如ctrl c
            logger.debug(" catch keyboardInterrupt, goodbye!!!")
            # 收尾工作
            self.stop()
            os._exit(0)
        except Exception as e:
            logger.error("Exception in run")
            logger.error(e)

    #     测试前清空 tmp 目录下dump文件 清理超过一周的文件，避免同时测试会有冲突
    def clear_heapdump(self):
        filelist = self.device.adb.list_dir("/data/local/tmp")
        if filelist:
            for file in filelist:
                if self.packages[0] in file and self.device.adb.is_overtime_days("/data/local/tmp/"+file,3):
                    self.device.adb.delete_file("/data/local/tmp/%s" % file)

    def stop(self):
        for monitor in self.monitors:
            try:
                monitor.stop()
            except Exception as e:  # 捕获所有的异常，防止其中一个monitor的stop操作发生异常退出时，影响其他的monitor的stop操作
                logger.error(e)

        try:
            if self.logcat_monitor:
                self.logcat_monitor.stop()
        except Exception as e:
            logger.error("stop exception for logcat monitor")
            logger.error(e)
        if self.config_dic["monkey"] =="true":
            self.device.adb.kill_process("com.android.commands.monkey")
        # 统计测试时长
        cost_time =round((float) (time.time() - TimeUtils.getTimeStamp(RuntimeData.start_time,TimeUtils.UnderLineFormatter))/3600,2)
        self.add_device_info("test cost time:",str(cost_time)+"h")
        # 根据csv生成excel汇总文件
        Report(RuntimeData.package_save_path,self.packages)
        self.pull_heapdump()
        self.pull_log_files()
        # self.memory_analyse()
        # self.device.adb.bugreport(RuntimeData.package_save_path)
        os._exit(0)

    # windows可能没装 自测用
    def memory_analyse(self):
        pass
        # 增加内存分析
        # logger.debug("show_growth")
        # objgraph.show_growth()
        # objgraph.show_most_common_types(limit=10)
        # logger.debug("gc.garbage")
        # logger.debug(gc.garbage)
        # logger.debug("collect()")
        # logger.debug(gc.collect())
        # logger.debug("gc.garbage")
        # logger.debug(gc.garbage)



    def pull_heapdump(self):
        # 把dumpheap文件拷贝出来
        filelist = self.device.adb.list_dir("/data/local/tmp")
        if filelist:
            for file in filelist:
                if self.packages[0] in file:
                    self.device.adb.pull_file("/data/local/tmp/%s" % file, RuntimeData.package_save_path)

    def pull_log_files(self):
        if self.config_dic["phone_log_path"]:
            for src_path in self.config_dic["phone_log_path"]:
                self.device.adb.pull_file(src_path, RuntimeData.package_save_path)
                # self.device.adb.pull_file_between_time(src_path,RuntimeData.package_save_path,
                #             TimeUtils.getTimeStamp(RuntimeData.start_time,TimeUtils.UnderLineFormatter),time.time())
        #         release系统pull  /sdcard/mtklog/可以  没有权限/sdcard/mtklog/mobilelog


    def save_device_info(self):
        device_file = os.path.join(RuntimeData.package_save_path,"device_test_info.txt")
        with open(device_file,"w+",encoding="utf-8") as writer:
            writer.write("device serialnum:"+self.serialnum+"\n")
            writer.write("device model:"+self.device.adb.get_phone_brand()+" "+self.device.adb.get_phone_model()+"\n")
            writer.write("test package:" + self.packages[0] + "\n")
            writer.write("system version:"+self.device.adb.get_system_version()+"\n")
            writer.write("test package ver:" + self.device.adb.get_package_ver(self.packages[0]) + "\n")

    def add_device_info(self,key,value):
        device_file = os.path.join(RuntimeData.package_save_path,"device_test_info.txt")
        with open(device_file,"a+",encoding="utf-8") as writer:
            writer.write(key+":"+value+"\n")

    def check_exit_signal_quit(self):
        if(RuntimeData.exit_event.is_set()):
            return True
        else:
            return False


class App():
    def __init__(self,package,name="",version=""):
        self.package = package
        self.name = name
        self.version = version

if __name__ == "__main__":
    # 来自于pyintaller的官网，多进程在windows系统下需要添加这句，否则会创建多个重复的进程，在mac和linux下不会有影响
    # multiprocessing.freeze_support()
    #startup = StartUp("351BBJN3DJC8","com.taobao.taobao",2)
    startup = StartUp()
    startup.run()
    # RuntimeData.start_time = "2019_03_07_10_57_58"
    # RuntimeData.package_save_path = "/Users/look/Desktop/project/mobileperf-mac/results/com.alibaba.ailabs.genie.contacts/2019_03_07_10_57_58"
    # RuntimeData.start_time = "2019_03_07_10_54_59"
    # RuntimeData.package_save_path = "/Users/look/Desktop/project/mobileperf-mac/results/com.alibaba.ailabs.ar.fireeye2/2019_03_07_10_54_59"
    # startup.deal_error()
