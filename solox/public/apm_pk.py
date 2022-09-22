import datetime
import re
import time
from solox.public.adb import adb
from solox.public.common import Devices, file
from solox.public.fps import FPSMonitor, TimeUtils

d = Devices()
f = file()


class CPU_PK:

    def __init__(self, pkgNameList: list, deviceId1, deviceId2):
        self.pkgNameList = pkgNameList
        self.deviceId1 = deviceId1
        self.deviceId2 = deviceId2
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')


    def getprocessCpuStat(self, pkgName, deviceId):
        """get the cpu usage of a process at a certain time"""
        pid = d.getPid(pkgName=pkgName, deviceId=deviceId)
        cmd = f'cat /proc/{pid}/stat'
        result = adb.shell(cmd=cmd, deviceId=deviceId)
        r = re.compile("\\s+")
        toks = r.split(result)
        processCpu = float(int(toks[13]) + int(toks[14]) + int(toks[15]) + int(toks[16]))
        return processCpu


    def getTotalCpuStat(self, deviceId):
        """get the total cpu usage at a certain time"""
        cmd = f'cat /proc/stat |{d._filterType()} ^cpu'
        result = adb.shell(cmd=cmd, deviceId=deviceId)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        totalCpu = 0
        for i in range(1, 9):
            totalCpu += int(toks[i])
        return float(totalCpu)


    def getIdleCpuStat(self, deviceId):
        """get the idle cpu usage at a certain time"""
        cmd = f'cat /proc/stat |{d._filterType()} ^cpu'
        result = adb.shell(cmd=cmd, deviceId=deviceId)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        IdleCpu = float(int(toks[4]))
        return IdleCpu

    def getAndroidCpuRate(self):
        """get the Android cpu rate of a process"""
        processCpuTime1_first = self.getprocessCpuStat(pkgName=self.pkgNameList[0], deviceId=self.deviceId1)
        totalCpuTime1_first = self.getTotalCpuStat(deviceId=self.deviceId1)
        time.sleep(1)
        processCpuTime1_second = self.getprocessCpuStat(pkgName=self.pkgNameList[0], deviceId=self.deviceId1)
        totalCpuTime1_second = self.getTotalCpuStat(deviceId=self.deviceId1)

        if len(self.pkgNameList) == 1:
            processCpuTime2_first = self.getprocessCpuStat(pkgName=self.pkgNameList[0], deviceId=self.deviceId2)
            totalCpuTime2_first = self.getTotalCpuStat(deviceId=self.deviceId2)
            time.sleep(1)
            processCpuTime2_second = self.getprocessCpuStat(pkgName=self.pkgNameList[0], deviceId=self.deviceId2)
            totalCpuTime2_second = self.getTotalCpuStat(deviceId=self.deviceId2)
        else:
            processCpuTime2_first = self.getprocessCpuStat(pkgName=self.pkgNameList[1], deviceId=self.deviceId2)
            totalCpuTime2_first = self.getTotalCpuStat(deviceId=self.deviceId2)
            time.sleep(1)
            processCpuTime2_second = self.getprocessCpuStat(pkgName=self.pkgNameList[1], deviceId=self.deviceId2)
            totalCpuTime2_second = self.getTotalCpuStat(deviceId=self.deviceId2)

        appCpuRate1 = round(float((processCpuTime1_second - processCpuTime1_first) / (totalCpuTime1_second - totalCpuTime1_first) * 100), 2)
        appCpuRate2 = round(float((processCpuTime2_second - processCpuTime2_first) / (totalCpuTime2_second - totalCpuTime2_first) * 100), 2)

        f.add_log(f'{f.report_dir}/cpu_app1.log', self.apm_time, appCpuRate1)
        f.add_log(f'{f.report_dir}/cpu_app2.log', self.apm_time, appCpuRate2)


        return appCpuRate1, appCpuRate2


class MEM_PK:
    def __init__(self, pkgNameList: list, deviceId1, deviceId2):
        self.pkgNameList = pkgNameList
        self.deviceId1 = deviceId1
        self.deviceId2 = deviceId2
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')

    def getAndroidMem(self, pkgName, deviceId):
        """Get the Android memory ,unit:MB"""
        pid = d.getPid(pkgName=pkgName, deviceId=deviceId)
        cmd = f'dumpsys meminfo {pid}'
        output = adb.shell(cmd=cmd, deviceId=deviceId)
        m_total = re.search(r'TOTAL\s*(\d+)', output)
        totalPass = round(float(float(m_total.group(1))) / 1024, 2)
        return totalPass

    def getProcessMem(self):
        """Get the app memory"""
        if len(self.pkgNameList) == 1:
            totalPass1 = self.getAndroidMem(self.pkgNameList[0], self.deviceId1)
            totalPass2 = self.getAndroidMem(self.pkgNameList[0], self.deviceId2)
        else:
            totalPass1 = self.getAndroidMem(self.pkgNameList[0], self.deviceId1)
            totalPass2 = self.getAndroidMem(self.pkgNameList[1], self.deviceId2)

        f.add_log(f'{f.report_dir}/mem1.log', self.apm_time, totalPass1)
        f.add_log(f'{f.report_dir}/mem2.log', self.apm_time, totalPass2)

        return totalPass1, totalPass2


class Flow_PK:

    def __init__(self, pkgNameList: list, deviceId1, deviceId2):
        self.pkgNameList = pkgNameList
        self.deviceId1 = deviceId1
        self.deviceId2 = deviceId2
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')

    def getAndroidNet(self, pkgName, deviceId):
        """Get Android upflow and downflow data, unit:KB"""
        pid = d.getPid(pkgName=pkgName, deviceId=deviceId)
        cmd = f'cat /proc/{pid}/net/dev |{d._filterType()} wlan0'
        output_pre = adb.shell(cmd=cmd, deviceId=deviceId)
        m_pre = re.search(r'wlan0:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)', output_pre)
        sendNum_pre = round(float(float(m_pre.group(2)) / 1024), 2)
        recNum_pre = round(float(float(m_pre.group(1)) / 1024), 2)
        time.sleep(1)
        output_final = adb.shell(cmd=cmd, deviceId=deviceId)
        m_final = re.search(r'wlan0:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)', output_final)
        sendNum_final = round(float(float(m_final.group(2)) / 1024), 2)
        recNum_final = round(float(float(m_final.group(1)) / 1024), 2)
        sendNum = round(float(sendNum_final - sendNum_pre), 2)
        recNum = round(float(recNum_final - recNum_pre), 2)
        network = round(float(sendNum + recNum), 2)
        return network

    def getNetWorkData(self):
        """Get the upflow and downflow data, unit:KB"""
        if len(self.pkgNameList) == 1:
            network1 = self.getAndroidNet(self.pkgNameList[0], self.deviceId1)
            network2 = self.getAndroidNet(self.pkgNameList[0], self.deviceId2)
        else:
            network1 = self.getAndroidNet(self.pkgNameList[0], self.deviceId1)
            network2 = self.getAndroidNet(self.pkgNameList[1], self.deviceId2)
        f.add_log(f'{f.report_dir}/network1.log', self.apm_time, network1)
        f.add_log(f'{f.report_dir}/network2.log', self.apm_time, network2)
        return network1, network2


class FPS_PK:

    def __init__(self, pkgNameList: list, deviceId1, deviceId2):
        self.pkgNameList = pkgNameList
        self.deviceId1 = deviceId1
        self.deviceId2 = deviceId2
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')

    def getAndroidFps(self, deviceId, pkgName):
        """get Android Fps, unit:HZ"""
        monitors = FPSMonitor(device_id=deviceId, package_name=pkgName, frequency=1,
                              start_time=TimeUtils.getCurrentTimeUnderline())
        monitors.start()
        fps, jank = monitors.stop()
        return fps


    def getFPS(self):
        """get fps"""
        if len(self.pkgNameList) == 1:
            fps1 = self.getAndroidFps(pkgName=self.pkgNameList[0], deviceId=self.deviceId1)
            fps2 = self.getAndroidFps(pkgName=self.pkgNameList[0], deviceId=self.deviceId2)

        else:
            fps1 = self.getAndroidFps(pkgName=self.pkgNameList[0], deviceId=self.deviceId1)
            fps2 = self.getAndroidFps(pkgName=self.pkgNameList[1], deviceId=self.deviceId2)

        f.add_log(f'{f.report_dir}/fps1.log', self.apm_time, fps1)
        f.add_log(f'{f.report_dir}/fps2.log', self.apm_time, fps2)

        return fps1, fps2


