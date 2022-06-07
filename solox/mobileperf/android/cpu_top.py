#encoding:utf-8
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import csv
import os
import re
import os,sys
import threading
import time
import traceback

from datetime import datetime

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))

from mobileperf.android.tools.androiddevice import AndroidDevice
from mobileperf.common.utils import TimeUtils,FileUtils
from mobileperf.common.log import logger
from mobileperf.android.globaldata import RuntimeData

class DeviceCpuinfo(object):
    pass

class PckCpuinfo(object):
    '''
    存储某个包cpu的相关信息，计划存储的信息有：包名，pid，uid，给定包的jiffies(从开机开始算)来自/proc/pid/stats
    该进程的cpu占有率，现在可以通过top获取还是自己通过前后的jiffies计算，
    初步确定使用top 直接进行统计.注意top中的数值基本上是瞬时值，采样的数据也是来自于/proc/pid/stat(具体进程的cpu%)
    '''
    #  1:cpu   2:user   3:nice  4:sys  5:idle     6:iow  7:irq    8:sirq   9:host
    #400%cpu  56%user   1%nice  46%sys 285%idle   0%iow  10%irq   2%sirq   0%host
    #User 0%, System 0%, IOW 0%, IRQ 0%


    RE_CPU = re.compile(r'User (\d+)\%\, System (\d+)\%\, IOW (\d+)\%\, IRQ (\d+)\%')
    RE_CPU_O = re.compile(r'(\d+)\%cpu\s+(\d+)\%user\s+(\d+)\%nice\s+(\d+)\%sys\s+(\d+)\%idle\s+(\d+)\%iow\s+(\d+)\%irq\s+(\d+)\%sirq\s+(\d+)\%host')

    def __init__(self, packages, source, sdkversion):
        '''
        :param packages: 应用的包名
        :param source: 数据源，来自于adb shell top.
        '''
        self.source = source
        self.sdkversion = sdkversion
        self.datetime = ''
        self.packages = packages
        self.pid = 0
        self.uid = ''
        self.pck_cpu_rate = ''
        self.pck_pyc = ''
        self.uid_cpu_rate = ''
        #同一个应用有时候有多个进程,每个进程都会出现cpu占比较大的情况，为了统计准确，针对多进程的情况，同一条top命令最好返回多条记录，以便查看详情
        #顺序是；[datetime, packagename, pid, uid, pid cpu, uid cpu, pcy,uid cpu]
        self.package_list = []

        self.device_cpu_rate = ''#整机的cpu使用率
        self.system_rate = ""
        self.user_rate = ''
        self.nice_rate = ''
        self.idle_rate = ''
        self.iow_rate = ''
        self.irq_rate = ''
        self.total_pid_cpu = 0
        self._parse_cpu_usage()
        self._parse_package()
        # self.sum_procs_cpurate()


    def _parse_package(self):
        '''
        解析top命令中的包的cpu信息
        :return:
        '''
        if self.packages == None or self.packages == "":
            logger.error("no process name input, please input")

        for package in self.packages:
            package_dic = {"package":package,
                           "pid":"",
                           "pid_cpu":""}
            sp_lines = self.source.split('\n')
            for line in sp_lines:
            # logger.debug(line)
                if package in line:#解析进程cpu信息
                    tmp = line.split()
                    self.pid = tmp[0]
                    target_pck = tmp[-1]#从中解析出的最后一个值是包名
                    self.datetime = TimeUtils.getCurrentTime()
                    logger.debug("cpuinfos, _parse top target_pck is : " + str(target_pck) + " , self.pacakgename : " + package)
                    if package == target_pck:#只统计包名完全相同的进程
                        if int(self.pid) > 0:
                            logger.debug("cpuinfos, into _parse_pck packege is target package, pid is :" +str(self.pid))
                            # logger.debug("into _parse_pck packege is target package, pid is :" + str(self.pid))
                            cpu_index = self.get_cpucol_index()
                            uid_index = self.get_uidcol_index()
                            if (len(tmp) > cpu_index):
                                self.pck_cpu_rate = tmp[cpu_index]
                                # CPU% 9% 有的格式会有%
                                self.pck_cpu_rate = self.pck_cpu_rate.replace("%","")
                            if(len(tmp) > uid_index) :
                                self.uid = tmp[uid_index]
                            package_dic={"package":package,
                            "pid":self.pid,
                            "pid_cpu":str(self.pck_cpu_rate),
                            "uid":self.uid}
                            # self.package_list.append(package_dic)
                            # 将top中解析出来的信息保存在一个列表中，作为一条记录添加在package_list中
                            logger.debug("package: " + package + ", cpu_rate: " + str(self.pck_cpu_rate))
                            self.total_pid_cpu = self.total_pid_cpu+float(self.pck_cpu_rate)
                        break
            self.package_list.append(package_dic)
            logger.debug(package_dic)

    def _parse_cpu_usage(self):
        '''
        从top中解析出cpu的信息
        :return:
        '''
        if self.sdkversion < 26:#android 8.0之前的版本
            match = self.RE_CPU.search(self.source)
            if (match):
                self.user_rate = match.group(1)
                self.system_rate = match.group(2)
                self.iow_rate = match.group(3)
                self.irq_rate = match.group(4)
                self.device_cpu_rate = int(self.user_rate) + int(self.system_rate)
                logger.debug("  cpuinfos,device system_rate: %s" % self.system_rate)
                logger.debug("  cpuinfos, device user_rate: %s" % self.user_rate)
                logger.debug("  cpuinfos, device device_cpu_rate: %s" % self.device_cpu_rate)
        else:#8.0及其以上的版本 turandot 27
            #  1:cpu   2:user   3:nice  4:sys  5:idle     6:iow  7:irq    8:sirq   9:host
            match = self.RE_CPU_O.search(self.source)
            if (match):
                self.user_rate = match.group(2)
                self.nice_rate = match.group(3)
                self.system_rate = match.group(4)
                self.idle_rate = match.group(5)
                self.iow_rate = match.group(6)
                self.irq_rate = match.group(7)
                self.device_cpu_rate = int(self.user_rate) + int(self.system_rate)
                logger.debug("8.0 or higher, user_rate: " + str(self.user_rate) + ", sys: " + str(self.system_rate) + ",device cpu: " +str(self.device_cpu_rate))
                logger.debug("idle_rate: %s" % self.idle_rate)


    def sum_procs_cpurate(self):
        '''
        有时候我们需要知道整个应用的cpu占比情况，由于每个应用中可能会包含多个进程，所以需要将这些值累加,
        累加属于同一个UID的所有进程的cpu使用率
        :return: 所有这些进程cpu%的和
        '''
        summ = 0
        if self.source:
            sp_lines = self.source.split("\n")
            for line in sp_lines:
                if self.uid != "" and self.uid in line:#先过滤出有相同uid的行
                    tmp = line.split()
                    cpu_index = self.get_cpucol_index()
                    summ  =summ + int(tmp[cpu_index].replace("%",""))
            self.uid_cpu_rate = str(summ) + "%"
            for i in range(len(self.package_list)):
                self.package_list[i].append(self.uid_cpu_rate)
                logger.debug("cpuinfos, sum_procs_cpurate , afer append uid cpu rate, the package list is : "+str(self.package_list))

    def get_cpucol_index(self):
        '''
        实际测试中发现不同的机型top命令中的cpu使用率不一定在第三列，所以需要获取到这个值在第几列。
        :return: cpu%所在的列标
        '''

        # return self.get_col_index(self.source, "CPU%", 2)
        return self.get_col_index(self.source, ["CPU]","CPU%"], 2)

    def get_pcycol_index(self):
        '''
        :return: top中pyc的列标
        '''
        return self.get_col_index(self.source, ["PCY"], -1)

    def get_packagenamecol_index(self):
        '''
        :return: top中的packagename的列标
        '''
        # return self.get_col_index(self.source,"Name",-1)
        return self.get_col_index(self.source,["ARGS"],-1)

    def get_vsscol_index(self):
        return self.get_col_index(self.source, ["VSS"], -1)

    def get_rss_col_index(self):
        return self.get_col_index(self.source, ["RSS"], -1)

    def get_uidcol_index(self):
        '''
        由于uid的列名在不同机器上会有差别，这里单独区分
        :return: adb shell top中uid列的列标
        '''
        if self.source:
            sp_lines = self.source.split("\n")
            for line in sp_lines:
                if 'UID' in line:
                    line_sp = line.split()
                    for key, item in enumerate(line_sp):
                        if item == "UID":
                            return key
                elif 'USER' in line:
                    line_sp = line.split()
                    for key, item in enumerate(line_sp):
                        if item == "USER":
                            return key
        return 8

    def get_col_index(self, s, col_name_list, default):
        '''
        返回top中列标的通用的方法
        :param s: 一条top命令的值
        :param col_name: 列名列表 可能会有不同格式
        :param default:默认返回的列标
        :return:
        '''
        s = s.split("\n")
        if s:
            for line in s:
                line = line.strip()
                for col_name in col_name_list:
                    if col_name in line:
                        line_sp = re.split(r"\[%|\s+", line)
                        for key, item in enumerate(line_sp):
                            if item == col_name:
                                logger.debug('=========== item == col_name: ' + col_name + " index : " + str(key))
                                return key
        return default
    
class CpuCollector(object):
    '''
    通过top命令搜集cpu信息的一个类
    '''
    def __init__(self, device, packages, interval=1, timeout=24*60*60):
        '''

        :param device: 具体的设备实例
        :param packages: 应用的包名列表
        :param interval: 数据采集的频率
        :param timeout: 采集的超时，超过这个时间，任务会停止采集,默认是24个小时
        '''
        self.device = device
        self.packages = packages
        self._interval = interval
        self._timeout = timeout
        self._stop_event = threading.Event()
        self.cpu_list = []
        self.sdkversion = self.get_sdkversion()
        # top可能会有进程名显示不全的问题 加-b即可
        self.top_cmd = 'top -b -n 1 -d %d' % self._interval
        ret = self.device.adb.run_shell_cmd(self.top_cmd)
        if ret and 'Invalid argument "-b"' in ret:
            logger.debug("top -b not support")
            self.top_cmd = 'top -n 1 -d %d' % self._interval
        logger.debug("sdk version : " +str(self.sdkversion))

    def get_sdkversion(self):
        sdk = self.device.adb.get_sdk_version()
        if sdk == None:
            sdk = 25
        return sdk

    def start(self,start_time):
        '''
        启动一个搜集器来启动一个新的线程搜集cpu信息
        :return:
        '''
        self.collect_package_cpu_thread = threading.Thread(target=self._collect_package_cpu_thread,args=(start_time,))
        self.collect_package_cpu_thread.start()
        logger.debug("INFO: CpuCollector start...")

    def stop(self):
        '''
        停止cpu的搜集器
        :return:
        '''
        logger.debug("INFO: CpuCollector stop...")
        if (self.collect_package_cpu_thread.isAlive()):
            self._stop_event.set()
            self.collect_package_cpu_thread.join(timeout=2)
            self.collect_package_cpu_thread = None

        if hasattr(self, "_top_pipe"):
            if self._top_pipe.poll() == None:#查看top进程是否仍然存在，如果还存在，就结束掉
                self._top_pipe.terminate()

    def _top_cpuinfo(self):
        self._top_pipe = self.device.adb.run_shell_cmd(self.top_cmd, sync=False)
        out = self._top_pipe.stdout.read()
        error = self._top_pipe.stderr.read()
        if error:
            logger.error("into cpuinfos error : "+str(error))
            return
        out = str(out,"utf-8")
        out.replace('\r','')
        top_file = os.path.join(RuntimeData.package_save_path, 'top.txt')
        with open(top_file, "a+",encoding="utf-8") as writer:
            writer.write(TimeUtils.getCurrentTime() + " top info:\n")
            writer.write(out + "\n\n")
        #避免文件过大，超过100M清理
        if FileUtils.get_FileSize(top_file)>100:
            os.remove(top_file)
        return PckCpuinfo(self.packages, out, self.sdkversion)

    def get_max_freq(self):
        out = self.device.adb.run_shell_cmd("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
        out.replace('\r', '')
        max_freq_file = os.path.join(RuntimeData.package_save_path, 'scaling_max_freq.txt')
        with open(max_freq_file, "a+",encoding="utf-8") as writer:
            writer.write(TimeUtils.getCurrentTime() + " scaling_max_freq:\n")
            writer.write(out + "\n\n")

    def _collect_package_cpu_thread(self,start_time):
        '''
        按照指定频率，循环搜集cpu的信息
        :return:
        '''
        end_time = time.time() + self._timeout
        cpu_title = ["datetime", "device_cpu_rate%", "user%", "system%","idle%"]
        cpu_file = os.path.join(RuntimeData.package_save_path, 'cpuinfo.csv')
        for i in range(0, len(self.packages)):
            cpu_title.extend(["package", "pid", "pid_cpu%"])
        if len(self.packages) > 1:
            cpu_title.append("total_pid_cpu%")
        try:
            with open(cpu_file, 'a+') as df:
                csv.writer(df, lineterminator='\n').writerow(cpu_title)
        except RuntimeError as e:
            logger.error(e)
        while not self._stop_event.is_set() and time.time() < end_time:
            try:
                logger.debug("---------------cpuinfos, into _collect_package_cpu_thread loop thread is : " + str(threading.current_thread().name))
                before = time.time()
                #为了cpu值的准确性，将采集的时间间隔放在top命令中了
                cpu_info = self._top_cpuinfo()
                after = time.time()
                time_consume = after - before
                logger.debug("  ============== time consume for cpu info : "+str(time_consume))
                if cpu_info == None or cpu_info.source == '' or not cpu_info.package_list:
                    logger.debug("cpuinfos, can't get cpu info, continue")
                    continue
                self.cpu_list.extend([TimeUtils.getCurrentTime(), str(cpu_info.device_cpu_rate), cpu_info.user_rate, cpu_info.system_rate,cpu_info.idle_rate])
                for i in range(0, len(self.packages)):
                    if len(cpu_info.package_list)==len(self.packages):
                        self.cpu_list.extend([cpu_info.package_list[i]["package"],cpu_info.package_list[i]["pid"],cpu_info.package_list[i]["pid_cpu"]])
                if len(self.packages)>1:
                    self.cpu_list.append(cpu_info.total_pid_cpu)
                #校准时间，由于top执行需要耗时，需要将这个损耗加上去
                logger.debug("INFO: CpuMonitor save cpu_device_list: " + str(self.cpu_list))
                try:
                    with open(cpu_file, 'a+',encoding="utf-8") as df:
                        csv.writer(df, lineterminator='\n').writerow(self.cpu_list)
                        del self.cpu_list[:]
                except RuntimeError as e:
                    logger.error(e)

                # self.get_max_freq()
                delta_inter = self._interval - time_consume
                if delta_inter > 0:
                    time.sleep(delta_inter)
            except Exception as e:
                logger.error("an exception hanpend in cpu thread , reason unkown!, e:")
                logger.error(e)
                s = traceback.format_exc()
                logger.debug(s)#将堆栈信息打印到log中
                if self.cpu_queue:
                    self.cpu_queue.task_done()
        logger.debug("stop event is set or timeout")

class CpuMonitor(object):
    '''
    cpu 监控器
    '''
    def __init__(self, device_id, packages, interval=5,timeout=24 * 60 * 60):
        self.device = AndroidDevice(device_id)
        self.packages = packages
        self.cpu_collector = CpuCollector(self.device, packages, interval,timeout)

    def start(self,start_time):
        '''
        启动一个cpu监控器，监控cpu信息
        :return:
        '''
        if not RuntimeData.package_save_path:
            RuntimeData.package_save_path = os.path.join(os.path.abspath(os.path.join(os.getcwd(), "../..")),'results', self.packages[0], start_time)
            if not os.path.exists(RuntimeData.package_save_path):
                os.makedirs(RuntimeData.package_save_path)
        self.start_time = start_time
        self.cpu_collector.start(start_time)
        logger.debug("INFO: CpuMonitor has started...")

    def stop(self):
        self.cpu_collector.stop()
        logger.debug("INFO: CpuMonitor has stopped...")

    def _get_cpu_collector(self):
        return self.cpu_collector

    def save(self):
        pass


if __name__ == "__main__":
    # RuntimeData.package_save_path = "/Users/look/Desktop/project/mobileperf-mac/results/com.yunos.tv.alitvasr/2019_03_25_22_07_57/"
    # monitor = CpuMonitor("O77DFAWSSGV4Z5AU", ["com.yunos.tv.alitvasr", "com.alibaba.ailabs.genie.contacts"], 5)
    # monitor = CpuMonitor("O77DFAWSSGV4Z5AU", ["com.yunos.tv.alitvasr"], 5)
    monitor = CpuMonitor("85I7UO4PFQCINJL7",["com.yunos.tv.alitvasr"], 5)
    monitor.start(TimeUtils.getCurrentTimeUnderline())
    time.sleep(180)
    monitor.stop()
