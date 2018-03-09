# -*- coding: utf-8 -*-

import datetime
import multiprocessing
import re
import sys
import time
from threading import Timer

import matplotlib

from adbTool import Adb

matplotlib.use('Agg', warn=True)
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import logUtils

DATA_TITLE = "时间,应用占用CPU,总占用CPU,总内存(MB),NativeHeap(MB),DalvikHeap(MB),流量(Kb/s)\n"
HEAP_PROFILE = True


class CpuProfiler():
    def __init__(self, pid, adb, loghd):
        self.appPid = pid
        self.adb = adb
        self.loghd = loghd
        self.processcpuRatioList = []
        self.cpuRatioList = []
        self.lastRecord = {}
        self.lastTime = 0
        self.titile = ["应用占用CPU(%)", "总占用CPU(%)"]

    def init(self):
        processCpu = self.getprocessCpuStat()
        idleCpu, totalCpu = self.getTotalCpuStat()
        self.lastRecord["processCpu"] = processCpu
        self.lastRecord["idleCpu"] = idleCpu
        self.lastRecord["totalCpu"] = totalCpu
        self.lastTime = datetime.datetime.now()

    def getprocessCpuStat(self):
        stringBuffer = self.adb.cmd("shell", "cat", "/proc/" + self.appPid + "/stat").communicate()[0].decode(
            "utf-8").strip()
        r = re.compile("\\s+")
        toks = r.split(stringBuffer)
        processCpu = float(long(toks[13]) + long(toks[14]));
        return processCpu

    def getTotalCpuStat(self):
        child_out = self.adb.cmd("shell", "cat", "/proc/stat", "|grep ^cpu\ ").communicate()[0].decode("utf-8").strip()
        # print child_out
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(child_out)
        idleCpu = float(toks[3])
        totalCpu = float(reduce(lambda x, y: long(x) + long(y), toks));
        return idleCpu, totalCpu

    def profile(self):
        processCpu = self.getprocessCpuStat()
        idleCpu, totalCpu = self.getTotalCpuStat()
        currentTime = datetime.datetime.now()
        diffTime = currentTime - self.lastTime

        retry = False
        processcpuRatio = 100 * (processCpu - self.lastRecord["processCpu"]) / (totalCpu - self.lastRecord["totalCpu"]);
        cpuRatio = 100 * ((totalCpu - idleCpu) - (self.lastRecord["totalCpu"] - self.lastRecord["idleCpu"])) / (
            totalCpu - self.lastRecord["totalCpu"]);
        if (diffTime.seconds * 1000 + diffTime.microseconds / 1000) < abs(totalCpu - self.lastRecord["totalCpu"]):
            self.loghd.info("cpu data abnormal, do again!")
            retry = True

        self.lastTime = currentTime
        self.lastRecord["processCpu"] = processCpu
        self.lastRecord["idleCpu"] = idleCpu
        self.lastRecord["totalCpu"] = totalCpu

        # 保存画图数据
        self.processcpuRatioList.append(round(float(processcpuRatio), 2))
        self.cpuRatioList.append(round(float(cpuRatio), 2))

        return round(float(processcpuRatio), 2), round(float(cpuRatio), 2), retry


class MemProfiler():
    def __init__(self, pid, adb, loghd):
        self.appPid = pid
        self.adb = adb
        self.loghd = loghd
        self.PSSList = []
        self.NativeHeapList = []
        self.DalvikHeapList = []
        self.lastRecord = {}
        self.titile = ["总内存(MB)", "NativeHeap(MB)", "DalvikHeap(MB)"]

    def timeout(self, p):
        if p.poll() is None:
            self.loghd.info('appmonitor Error: process taking too long to complete--terminating')
            p.kill()

    def getProcessMem(self):
        if HEAP_PROFILE == False:
            return 0, 0, 0

        cmdProcess = self.adb.cmd("shell", "dumpsys", "meminfo", self.appPid)
        output = ""
        my_timer = Timer(30, self.timeout, [cmdProcess])
        try:
            my_timer.start()
            output = cmdProcess.communicate()[0].decode("utf-8").strip()
        except ValueError as err:
            self.loghd.info(err.args)
        finally:
            my_timer.cancel()

        m = re.search(r'TOTAL\s*(\d+)', output)
        m1 = re.search(r'Native Heap\s*(\d+)', output)
        m2 = re.search(r'Dalvik Heap\s*(\d+)', output)
        PSS = float(m.group(1))
        NativeHeap = float(m1.group(1))
        DalvikHeap = float(m2.group(1))
        return PSS, NativeHeap, DalvikHeap

    def profile(self):
        PSS, NativeHeap, DalvikHeap = self.getProcessMem()

        self.PSSList.append(round(PSS / 1024, 2))
        self.NativeHeapList.append(round(NativeHeap / 1024, 2))
        self.DalvikHeapList.append(round(DalvikHeap / 1024, 2))

        return round(PSS / 1024, 2), round(NativeHeap / 1024, 2), round(DalvikHeap / 1024, 2)


class FlowProfiler():
    def __init__(self, pid, adb, loghd):
        self.appPid = pid
        self.adb = adb
        self.loghd = loghd
        self.flowList = []
        self.lastRecord = {}
        self.lastTime = 0
        self.titile = ["流量(Kb/s)"]

    def init(self):
        sendNum, recNum = self.getFlow()
        self.lastRecord["sendNum"] = sendNum
        self.lastRecord["recNum"] = recNum
        self.lastTime = datetime.datetime.now()

    def getFlow(self):
        output = self.adb.cmd("shell", "cat", "/proc/" + self.appPid + "/net/dev", "|grep wlan0").communicate()[
            0].decode("utf-8").strip()
        m = re.search(r'wlan0:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)', output)
        if m:
            recNum = float(m.group(1))
            sendNum = float(m.group(2))
        else:
            self.loghd.info("Couldn't get rx and tx data from: %s!" % output)
            recNum = 0.0;
            sendNum = 0.0;
        return recNum, sendNum

    def profile(self):
        sendNum, recNum = self.getFlow()
        currentTime = datetime.datetime.now()
        diffTime = currentTime - self.lastTime

        seconds = diffTime.seconds + float(diffTime.microseconds) / 1000000
        flow = (((sendNum - self.lastRecord["sendNum"]) + (recNum - self.lastRecord["recNum"])) / 1024) / seconds
        flow = round(flow, 2)

        self.lastTime = currentTime
        self.lastRecord["sendNum"] = sendNum
        self.lastRecord["recNum"] = recNum

        if flow > 0:
            self.flowList.append(flow)
        return flow


class app_monitor(multiprocessing.Process):
    timeout_in_seconds = 60

    def __init__(self, period, fileName, appName, loghd, serial=None):
        # threading.Thread.__init__(self);
        multiprocessing.Process.__init__(self)
        self.adb = Adb(serial=serial)

        self.appPid = 0
        self.appName = appName
        self.period = period
        self.fileName = fileName + ".csv"
        self.pigName = fileName + ".jpg"
        self.loghd = loghd
        # self.getappPid()
        self.running = True
        self.lastRecord = {}
        # self.is_alive = False      

    def stop(self):
        # self.running = False
        try:
            while self.running and self.getAppPid() == self.appPid and self.getAppPid() != 0:
                self.loghd.info("appmonitor process still alive, wait ...")
                time.sleep(1)
        except:
            pass

    def getAppPid(self):
        # self.appPid = self.adb.cmd("shell", "set", "`ps|grep com.duowan.mobile$`;", "echo", "$2").communicate()[0].decode("utf-8").strip()
        outputs = self.adb.cmd("shell", "top", "-m", "10", "-n", "1").communicate()[0].decode("utf-8").strip()
        r = "(\\d+).*\\s+%s[^:]" % self.appName
        m = re.search(r, outputs)
        # print outputs
        if m:
            return m.group(1)
        else:
            self.loghd.info("app still not get up")
            return 0

    def waitForAppReady(self):
        start_time = long(time.time())
        while self.appPid == 0:
            elapsed = long(time.time()) - start_time
            # 做完一部分任务后,判断是否超时
            if elapsed >= app_monitor.timeout_in_seconds:
                self.loghd.info("获取app pid超时，退出")
                self.running = False
                break

            self.loghd.info("appPid == 0")
            self.appPid = self.getAppPid()

        self.loghd.info(str(self.appPid))

    def pic(self, processcpuRatioList, cpuRatioList, PSSList, NativeHeapList, DalvikHeapList, flowList):
        # matplotlib.use('Agg')
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        # 设置右侧Y轴显示百分数
        fmt = '%.2f%%'
        yticks = mtick.FormatStrFormatter(fmt)

        def minY(listData):
            return round(min(listData) * 0.8, 2)

        def maxY(listData):
            return round(max(listData) * 1.2, 2)

        def drawSubplot(pos, x, y, xlabels, ylabels):
            plt.subplot(pos)
            plt.plot(x, y, label=ylabels)
            plt.xlabel(xlabels)
            plt.ylabel(ylabels)
            plt.ylim(minY(y), maxY(y))
            # plt.title(u'应用CPU')
            plt.legend()

        plt.figure(figsize=(20, 10))

        timeList = [x * 2 for x in range(len(processcpuRatioList))]
        drawSubplot(321, timeList, processcpuRatioList, u'时间(秒)', u'应用CPU(%)')
        plt.gca().yaxis.set_major_formatter(yticks)

        timeList = [x * 2 for x in range(len(cpuRatioList))]
        drawSubplot(322, timeList, cpuRatioList, u'时间(秒)', u"总cpu(%)")
        plt.gca().yaxis.set_major_formatter(yticks)

        timeList = [x * 2 for x in range(len(PSSList))]
        drawSubplot(323, timeList, PSSList, u'时间(秒)', u"总内存(MB)")

        timeList = [x * 2 for x in range(len(NativeHeapList))]
        drawSubplot(324, timeList, NativeHeapList, u'时间(秒)', u"Native内存(MB)")

        timeList = [x * 2 for x in range(len(DalvikHeapList))]
        drawSubplot(325, timeList, DalvikHeapList, u'时间(秒)', u"Dalvik内存(MB)")

        timeList = [x * 2 for x in range(len(flowList))]
        drawSubplot(326, timeList, flowList, u'时间(秒)', u"流量(kb/s)")

        # plt.gca().yaxis.set_minor_formatter(yticks)
        plt.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.95, hspace=0.55,
                            wspace=0.25)

        # plt.show()
        print self.pigName
        plt.savefig(self.pigName)

    def run(self):
        # 根据应用的包名称 获取CPU以及内存占用
        self.loghd.info("app_monitor run \n")
        # self.is_alive = True

        # 等待获取到被监控app的pid后才开始采集数据
        print "waitForAppReady begin"
        self.waitForAppReady()
        print "waitForAppReady end"

        flowProfile = FlowProfiler(self.appPid, self.adb, self.loghd)
        cpuProfile = CpuProfiler(self.appPid, self.adb, self.loghd)
        memProfile = MemProfiler(self.appPid, self.adb, self.loghd)

        flowProfile.init()
        cpuProfile.init()

        f = open(self.fileName, "w+")
        f.write('\xEF\xBB\xBF');
        f.write(DATA_TITLE)

        firstRun = True
        errorTimes = 0

        while self.running:
            try:
                str_now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                processcpuRatio, cpuRatio, retry = cpuProfile.profile()
                if retry:
                    time.sleep(float(self.period))
                    continue
                PSS, NativeHeap, DalvikHeap = memProfile.profile()
                flow = flowProfile.profile()

                write_str = "%s,%s,%s,%s,%s,%s,%s\n" % (str(str_now_time), \
                                                        str(processcpuRatio), str(cpuRatio), \
                                                        str(PSS), str(NativeHeap), \
                                                        str(DalvikHeap), str(flow));

                # self.loghd.info(write_str.replace(",", "     "))
                print write_str.replace(",", "     ")
                # 将数据写入文件
                f.write(write_str)
                f.flush()

            except Exception, e:
                errorTimes += 1
                if (errorTimes > 5):  # 本来想尝试通过看app是否还在来判断，但是发现用例结束后，app仍然在后台运行
                    self.loghd.info("monitor app end or process exception: %s" % e)
                    break
                else:
                    self.loghd.info("monitor app get data failed: %s" % e)
                    self.waitForAppReady()
                    continue

            time.sleep(float(self.period))

        f.close()

        print u"开始绘图了"
        self.pic(cpuProfile.processcpuRatioList, cpuProfile.cpuRatioList, memProfile.PSSList, \
                 memProfile.NativeHeapList, memProfile.DalvikHeapList, flowProfile.flowList)
        print u"绘图结束了"

        self.running = False


def help_notice():
    print u"用法 python getAndroidCpu.py 2 d:\ com.yy.me 23423442"
    print u"参数：时间间隔 结果存放目录 包名 设备ID(只连一台手机不需要此参数)"
    print u"参数不足, 或某些参数为空"
    sys.exit(0)


if __name__ == "__main__":
    # if (len(sys.argv) < 4) or ("" in sys.argv):
    #     print u"用法 python getAndroidCpu.py 2 d:\ com.yy.me 23423442"
    #     print u"参数：时间间隔 结果存放目录 包名 设备ID(只连一台手机不需要此参数)"
    #     print u"参数不足, 或某些参数为空"
    #     sys.exit(0)     

    if len(sys.argv) == 5:
        appMonitor = app_monitor(sys.argv[1], sys.argv[2], sys.argv[3], logUtils.log_init("device"), sys.argv[4])
    elif len(sys.argv) == 2:
        appMonitor = app_monitor(2, sys.argv[1], "com.duowan.mobile", logUtils.log_init("device"))
        print u"默认app为安卓手y, 间隔时间为2秒"
        print u"用法 python appMonitor.py filepath+filename"
    else:
        appMonitor = app_monitor(sys.argv[1], sys.argv[2], sys.argv[3], logUtils.log_init("device"))

    appMonitor.start()

    # print u"休眠60"
    # time.sleep(60)

    # print "stop"
    # appMonitor.terminate()
