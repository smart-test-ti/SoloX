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
import sys
import threading
import time
import traceback
import base64
from shutil import copyfile,rmtree

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))

from mobileperf.android.tools.androiddevice import AndroidDevice
from mobileperf.common.utils import TimeUtils,FileUtils,ZipUtils
from mobileperf.common.log import logger
from mobileperf.android.globaldata import RuntimeData

class MemInfoPackage(object):
    RE_PROCESS = re.compile(r'\*\* MEMINFO in pid (\d+) \[(\S+)] \*\*')
    RE_TOTAL_PSS = re.compile(r'TOTAL\s+(\d+)')
    RE_JAVA_HEAP = re.compile(r"Java Heap:\s+(\d+)")
    RE_Native_HEAP = re.compile(r"Native Heap:\s+(\d+)")
    RE_System = re.compile(r"System:\s+(\d+)")

    pid = 0
    processName = ''
    datetime = ''
    totalPSS = 0
    totalAllocHeap = 0
    javaHeap = 0
    nativeHeap = 0
    system = 0

    def __init__(self,  dump):
        self.dump = dump
        self._parse()


    def _parse(self):
        '''
        dumpsys meminfo package 中解析出需要的数据，由于版本变迁，这个数据的结构变化较多，比较了不同版本发现这两列数据total pss和Heap Alloc是都有的，而且这两个指标对于展示
        应用性能指标还是比较有代表性的。
        :return:
        '''
        match = self.RE_PROCESS.search(self.dump)
        if match:
            self.pid = match.group(1)
            self.processName = match.group(2)
        match = self.RE_TOTAL_PSS.search(self.dump)
        if match:
            self.totalPSS = round(float(match.group(1))/1024,2)

        match = self.RE_JAVA_HEAP.search(self.dump)
        if match:
            self.javaHeap = round(float(match.group(1)) / 1024, 2)

        match = self.RE_Native_HEAP.search(self.dump)
        if match:
            self.nativeHeap = round(float(match.group(1)) / 1024, 2)

        match = self.RE_System.search(self.dump)
        if match:
            self.system = round(float(match.group(1)) / 1024, 2)

        result = self.dump.split('\n')#需要将其转为列表

        for line in result:
            if "TOTAL" in line and ":" not in line:
                tmp = line.split()
                self.totalAllocHeap = round(float(tmp[-2])/1024,2)

class MemInfoDevice:
    '''
    暂时dumpsys的方案实现，这个方案性能有问题，采集的间隔不能太密，查看源码：/frameworks/base/core/jni/android_os_Debug.cpp
    '''
    RE_TOTAL_MEMORY = re.compile(r'Total RAM:\s+([\d,]+)')
    RE_FREE_MEMORY = re.compile(r' Free RAM:\s+([\d,]+)')
    RE_USED_MEMORY = re.compile(r" Used RAM:\s+([\d,]+)")

    def __init__(self,dump,packages=[]):
        self.totalmem = 0
        self.freemem = 0
        self.usedmem = 0
        self.datetime = ''
        self.dump = dump
        self.packages = packages
        self.package_pid_pss_list=[]
        self.total_pss = 0
        self._parse()


    def _parse(self):
        '''
        从dumpsys meminfo中解析出Total RAM，Free RAM, 和Used RAM这几个值并保存在相关实例变量中
        :return: NONE
        '''
        # logger.debug(self.dump)
        match = self.RE_TOTAL_MEMORY.search(self.dump)
        if match:
            self.totalmem = round(float(match.group(1).replace(",",""))/1024,2)
        match = self.RE_FREE_MEMORY.search(self.dump)
        if match:
            self.freemem = round(float(match.group(1).replace(",",""))/1024,2)
        match = self.RE_USED_MEMORY.search(self.dump)
        if match:
            self.usedmem = round(float(match.group(1).replace(",",""))/1024,2)

        logger.debug(" device general mem，total mem: "+str(self.totalmem) + ", \n used mem: " + str(self.usedmem) + ", free mem: " + str(self.freemem))
        for package in self.packages:
            # 可能子进程没有启动，默认填空值 方便格式上统一处理
            mem_dic = {"package": package, "pid": "", "pss": ""}
            RE_PROCESS_MEMORY = re.compile(r"([\d,]+)\s*(K|kB):\s+" + package + "\s+\(pid\s+(\d+)")
            # 252,370K: com.alibaba.ailabs.tg (pid 26620 / activities)
            # 111920 kB: com.alibaba.ailabs.tg (pid 16036 / activities)
            RE_PROCESS_MEMORY_2 = re.compile(r"([\d,]+)\s+kB:\s+\d+\s+kB:\s+" + package + "\s+\(pid\s+(\d+)")
            # 243786 kB:       0 kB: com.alibaba.ailabs.tg (pid 16993 / activities)
            for line in self.dump.splitlines():
                match = RE_PROCESS_MEMORY.search(line)
                match2 = RE_PROCESS_MEMORY_2.search(line)
                if match:
                    pss = round(float(match.group(1).replace(",", "")) / 1024, 2)
                    mem_dic = {"package": package, "pid": match.group(3), "pss": str(pss)}
                    # self.package_pid_pss_list.append(mem_dic)
                    # logger.debug("line:"+line +" package:"+package+" pid:"+match.group(3)+" pss:"+str(pss))
                    self.total_pss = self.total_pss + pss
                    break
                elif match2:
                    pss = round(float(match2.group(1).replace(",", "")) / 1024, 2)
                    mem_dic = {"package": package, "pid": match2.group(2), "pss": str(pss)}
                    # self.package_pid_pss_list.append(mem_dic)
                    # logger.debug("line:"+line +" package:"+package+" pid:"+match2.group(2)+" pss:"+str(pss))
                    self.total_pss = self.total_pss + pss
                    break
            self.package_pid_pss_list.append(mem_dic)
            logger.debug(mem_dic)

class MemInfoPackageCollector(object):
    def __init__(self, device, pacakges, interval=1.0, timeout =24 * 60 * 60, mem_queue = None):
        self.device = device
        self.packages = pacakges
        self._interval = interval
        self._timeout = timeout
        self._stop_event = threading.Event()
        self.mem_queue = mem_queue
        self.start_time = 0
        self.num = 0


    def start(self,start_time):
        self.start_time = start_time
        logger.debug("INFO: MemInfoPackageCollector start... ")
        self.collect_mem_thread = threading.Thread(target=self._collect_memory_thread,args=(start_time,))
        self.collect_mem_thread.start()

    def stop(self):
        logger.debug("INFO: MemInfoPackageCollector stop... ")
        if (self.collect_mem_thread.isAlive()):
            self._stop_event.set()
            self.collect_mem_thread.join(timeout=1)
            self.collect_mem_thread = None
            #结束的时候，发送一个任务完成的信号，以结束队列
            if self.mem_queue:
                self.mem_queue.task_done()

    def _dumpsys_meminfo(self):
        '''
        总内存 各进程内存都从dumpsys meminfo中获取
        这个方法挺耗时 约6 7秒才能完成
        :return:
        '''
        time_old = time.time()
        out = self.device.adb.run_shell_cmd('dumpsys meminfo')
        meminfo_file = os.path.join(RuntimeData.package_save_path, 'dumpsys_meminfo.txt')
        with open(meminfo_file, "a+",encoding="utf-8") as writer:
            writer.write(TimeUtils.getCurrentTime()+" dumpsys meminfo info:\n")
            writer.write(out+"\n\n")
            # self.num = 0

        passedtime = time.time() - time_old#测试meminfo这个命令的耗时，执行的时长在400多ms
        logger.debug("dumpsys meminfo time consume:" + str(passedtime))
        out.replace('\r', '')
        return MemInfoDevice(dump=out,packages=self.packages)

    def _dumpsys_process_meminfo(self,process):
        '''
        dump 进程详细内存 耗时 1s以内
        :param process:
        :return:
        '''
        time_old = time.time()
        out = self.device.adb.run_shell_cmd('dumpsys meminfo %s' % process)
        # self.num = self.num + 1
        # if self.num % 10 == 0:
        #避免：在windows 无法创建文件名，不能有冒号:
        process_rename = process.replace(":","_")
        meminfo_file = os.path.join(RuntimeData.package_save_path, 'dumpsys_meminfo_%s.txt'%process_rename)
        with open(meminfo_file, "a+",encoding="utf-8") as writer:
            writer.write(TimeUtils.getCurrentTime()+" dumpsys meminfo package info:\n")
            if out:
                writer.write(out+"\n\n")
            # self.num = 0

        passedtime = time.time() - time_old#测试meminfo这个命令的耗时，执行的时长在400多ms
        logger.debug("dumpsys meminfo package time consume:" + str(passedtime))
        out.replace('\r', '')
        return MemInfoPackage(dump=out)

    # @profile
    def _collect_memory_thread(self, start_time):
        end_time = time.time() + self._timeout
        mem_list_titile = ["datatime", "total_ram(MB)", "free_ram(MB)"]
        pid_list_titile = ["datatime"]
        pss_detail_titile = ["datatime","package","pid","pss","java_heap","native_heap","system"]
        for i in range(0,len(self.packages)):
            mem_list_titile.extend(["package", "pid", "pid_pss(MB)"])
            pid_list_titile.extend(["package", "pid"])
        if len(self.packages)>1:
            mem_list_titile.append("total_pss(MB)")
        mem_file = os.path.join(RuntimeData.package_save_path, 'meminfo.csv')
        pid_file = os.path.join(RuntimeData.package_save_path, 'pid_change.csv')
        for package in self.packages:
            pss_detail_file = os.path.join(RuntimeData.package_save_path, 'pss_%s.csv'%package.split(".")[-1].replace(":","_"))
            with open(pss_detail_file, 'a+',encoding="utf-8") as df:
                csv.writer(df, lineterminator='\n').writerow(pss_detail_titile)
        try:
            with open(mem_file, 'a+',encoding="utf-8") as df:
                csv.writer(df, lineterminator='\n').writerow(mem_list_titile)
                if self.mem_queue:
                    mem_file_dic = {'mem_file': mem_file}
                    self.mem_queue.put(mem_file_dic)

            with open(pid_file, 'a+',encoding="utf-8") as df:
                csv.writer(df, lineterminator='\n').writerow(pid_list_titile)
        except RuntimeError as e:
            logger.error(e)
        starttime_stamp = TimeUtils.getTimeStamp(start_time,"%Y_%m_%d_%H_%M_%S")
        old_package_pid_pss_list = []
        dumpsys_mem_times = 0
        # D系统上会报错 System server has no access to file context
        # hprof_path = "/sdcard/hprof"
        hprof_path = "/data/local/tmp"
        self.device.adb.run_shell_cmd("mkdir "+hprof_path)
        # sdcard 卡目录下dump需要打开这个开关
        self.device.adb.run_shell_cmd("setenforce 0")
        first_dump = True
        while not self._stop_event.is_set() and time.time() < end_time:
            try:
                before = time.time()
                logger.debug("-----------into _collect_mem_thread loop, thread is : " + str(threading.current_thread().name))
                collection_time = time.time()
                # # 获取主进程的详细信息
                for package in self.packages:
                    mem_pck_snapshot = self._dumpsys_process_meminfo(package)
                    if 0 == mem_pck_snapshot.totalPSS:
                        logger.error("package total pss is 0:%s"%package)
                        continue
                    pss_detail_file = os.path.join(RuntimeData.package_save_path,'pss_%s.csv' % package.split(".")[-1].replace(":","_"))
                    pss_detail_list= [TimeUtils.formatTimeStamp(collection_time),package,mem_pck_snapshot.pid,mem_pck_snapshot.totalPSS,
                                      mem_pck_snapshot.javaHeap,mem_pck_snapshot.nativeHeap,mem_pck_snapshot.system]
                    with open(pss_detail_file, 'a+',encoding="utf-8") as pss_writer:
                        writer_p = csv.writer(pss_writer, lineterminator='\n')
                        writer_p.writerow(pss_detail_list)
                #         写到pss_detail表格中

                # 每隔dumpheap_freq分钟， dumpheap一次
                if (before - starttime_stamp) > RuntimeData.config_dic["dumpheap_freq"] or first_dump:
                #     先清理hprof文件
                    filelist = self.device.adb.list_dir(hprof_path)
                    if filelist:
                        for file in filelist:
                            for package in self.packages:
                                if package in file:
                                    self.device.adb.delete_file(hprof_path+"/" + file)
                # if (before - starttime_stamp) % 60 < self._interval and "D" in self.device.adb.get_system_version():
                    for package in self.packages:
                        self.device.adb.dumpheap(package,RuntimeData.package_save_path)
                    starttime_stamp = before
                    # self.device.adb.run_shell_cmd("kill -10 %s"%str(mem_pck_snapshot.pid))
                # dumpsys meminfo 耗时长，可能会导致system server cpu占用变高，降低采集频率
                dumpsys_mem_times = dumpsys_mem_times + 1
                # 10倍率frequency dumpsys meminfo一次
                if dumpsys_mem_times%10==0 or first_dump:
                    mem_device_snapshot = self._dumpsys_meminfo()
                    # 如果没有采集到dumpsys meminfo的信息，正常情况totalmem不可能为0
                    if mem_device_snapshot == None or not mem_device_snapshot.package_pid_pss_list or mem_device_snapshot.totalmem == 0:
                        logger.error("mem_device_snapshot is none")
                        # 如果获取不到结果，继续延长采集间隔
                        dumpsys_mem_times = dumpsys_mem_times-1
                        continue
                    first_dump = False
                    logger.debug("current time: " + TimeUtils.getCurrentTime() + ", processname: " + ",total pss:" + str(mem_device_snapshot.total_pss))
                    logger.debug("collection time in meminfo is : " + TimeUtils.getCurrentTime())
                    gather_list = [TimeUtils.formatTimeStamp(collection_time), mem_device_snapshot.totalmem, mem_device_snapshot.freemem]
                    pid_list = [TimeUtils.formatTimeStamp(collection_time)]
                    pid_change = False
                    for i in range(0,len(self.packages)):
                        if len(mem_device_snapshot.package_pid_pss_list) == len(self.packages):
                            gather_list.extend([mem_device_snapshot.package_pid_pss_list[i]["package"],mem_device_snapshot.package_pid_pss_list[i]["pid"],
                                           mem_device_snapshot.package_pid_pss_list[i]["pss"]])
                    if not old_package_pid_pss_list:
                        old_package_pid_pss_list = mem_device_snapshot.package_pid_pss_list
                        pid_change = True
                    else:
                        for i in range(0, len(self.packages)):
                            package = mem_device_snapshot.package_pid_pss_list[i]["package"]
                            if mem_device_snapshot.package_pid_pss_list[i]["pid"] and \
                                    old_package_pid_pss_list[i]["pid"]!=mem_device_snapshot.package_pid_pss_list[i]["pid"]:
                                pid_change = True
                                # 确保上次pid也有
                                if old_package_pid_pss_list[i]["pid"]:
                                    if package and package in RuntimeData.config_dic["pid_change_focus_package"]:
                                        # 确保有tombstones文件才提单
                                        self.device.adb.pull_file("/data/vendor/tombstones",
                                                                  RuntimeData.package_save_path)
                    if pid_change:
                        old_package_pid_pss_list = mem_device_snapshot.package_pid_pss_list
                        for i in range(0, len(self.packages)):
                            if len(old_package_pid_pss_list) == len(self.packages):
                                pid_list.extend([old_package_pid_pss_list[i]["package"],old_package_pid_pss_list[i]["pid"]])
                        try:
                            with open(pid_file, 'a+',encoding="utf-8") as pid_writer:
                                writer_p = csv.writer(pid_writer, lineterminator='\n')
                                writer_p.writerow(pid_list)
                                logger.debug("write to file:" + pid_file)
                                logger.debug(pid_list)
                        except RuntimeError as e:
                            logger.error(e)
                    if len(self.packages)>1:
                        gather_list.append(mem_device_snapshot.total_pss)
                    if self.mem_queue:
                        gather_list[0] = collection_time
                        self.mem_queue.put(gather_list)
                    if not self.mem_queue:#为了本地单个文件运行
                        try:
                            with open(mem_file, 'a+',encoding="utf-8") as mem_writer:
                                writer_p = csv.writer(mem_writer, lineterminator='\n')
                                writer_p.writerow(gather_list)
                                logger.debug("write to file:" + mem_file)
                                logger.debug(gather_list)
                        except RuntimeError as e:
                            logger.error(e)

                after = time.time()
                time_consume = after - before
                delta_inter = self._interval - time_consume
                logger.info("time consume for meminfos: " + str(time_consume))
                if delta_inter > 0:
                    time.sleep(delta_inter)
            except:
                logger.error("an exception hanpend in meminfo thread, reason unkown!")
                s = traceback.format_exc()
                logger.debug(s)
                if self.mem_queue:
                    self.mem_queue.task_done()

        logger.debug("stop event is set or timeout")


class MemMonitor(object):
    def __init__(self, device_id, packages, interval = 1.0, timeout=24 * 60 * 60, mem_queue = None):
        self.device = AndroidDevice(device_id, )
        if not packages:
            packages = self.device.adb.get_foreground_process().split("#")
        self.packages = packages
        # self.meminfo_collector = MemInfoCollector(self.device, interval)
        self.meminfo_package_collector = MemInfoPackageCollector(self.device, self.packages, interval, timeout, mem_queue)

    def start(self,start_time):
        if not RuntimeData.package_save_path:
            RuntimeData.package_save_path = os.path.join(os.path.abspath(os.path.join(os.getcwd(), "../..")),'results', self.packages[0], start_time)
            if not os.path.exists(RuntimeData.package_save_path):
                os.makedirs(RuntimeData.package_save_path)
        self.start_time = start_time
        # self.meminfo_collector.start(start_time)
        self.meminfo_package_collector.start(start_time)

    def stop(self):
        # self.meminfo_collector.stop()
        self.meminfo_package_collector.stop()

    def get_meminfo_collector(self):
        return self.meminfo_collector

    def get_meminfo_package_collector(self):
        return self.meminfo_package_collector

    def save(self):
        pass

if __name__ == "__main__":
    # RuntimeData.package_save_path = "/Users/look/Desktop/project/mobileperf-mac/results/com.yunos.tv.alitvasr/2019_03_25_22_07_57"
    monitor = MemMonitor("85I7UO4PFQCINJL7",["com.yunos.tv.alitvasr"],5)
    monitor.start(TimeUtils.getCurrentTimeUnderline())
    time.sleep(300)
    monitor.stop()
#     monitor.save()







