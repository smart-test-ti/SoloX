import re
from .common import *
from functools import reduce
import time

d = Devices()
adb = Adb()
current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
report_dir = os.path.join(os.getcwd(), 'report')
class CPU():

    def __init__(self, pkgName ,deviceId):
        self.pkgName = pkgName
        self.deviceId = deviceId
        # self.cpufile = file().create_file(filename='cpu.log')
        self.apm_time = time.strftime("%H:%M:%S", time.localtime())

    def getprocessCpuStat(self):
        """获取某个时刻的某个进程的cpu损耗"""
        pid = d.getPid(pkgName=self.pkgName,deviceId=self.deviceId)
        cmd = f'cat /proc/{pid}/stat'
        result = adb.shell(cmd)
        r = re.compile("\\s+")
        toks = r.split(result)
        processCpu = float(int(toks[13]) + int(toks[14]));
        return processCpu

    def getTotalCpuStat(self):
        """获取某个时刻的总cpu损耗"""
        cmd = f'cat /proc/stat |grep ^cpu\ '
        result = adb.shell(cmd)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        idleCpu = float(toks[3])
        totalCpu = float(reduce(lambda x, y: int(x) + int(y), toks));
        return totalCpu

    def getSingCpuRate(self):
        """获取进程损耗cpu的占比%"""
        processCpuTime_1 = self.getprocessCpuStat()
        totalCpuTime_1 = self.getTotalCpuStat()
        time.sleep(0.5)
        processCpuTime_2 = self.getprocessCpuStat()
        totalCpuTime_2 = self.getTotalCpuStat()
        cpuRate = int((processCpuTime_2 - processCpuTime_1) / (totalCpuTime_2 - totalCpuTime_1) * 100)
        with open(f'{report_dir}/cpu.log', 'a+') as f:
            f.write(f'{self.apm_time}={str(cpuRate)}' + '\n')
        return cpuRate

class MEM():
    def __init__(self, pkgName ,deviceId):
        self.pkgName = pkgName
        self.deviceId = deviceId

    def getProcessMem(self):
        """获取进程内存Total、NativeHeap、NativeHeap;单位MB"""
        pid = d.getPid(pkgName=self.pkgName,deviceId=self.deviceId)
        cmd = f'adb shell dumpsys meminfo {pid}'
        output = adb.shell(cmd)
        m = re.search(r'TOTAL\s*(\d+)', output)
        m1 = re.search(r'Native Heap\s*(\d+)', output)
        m2 = re.search(r'Dalvik Heap\s*(\d+)', output)
        PSS = round(float(float(m.group(1))) / 1024, 2)
        NativeHeap = round(float(float(m1.group(1))) / 1024, 2)
        DalvikHeap = round(float(float(m2.group(1))) / 1024, 2)
        return PSS, NativeHeap, DalvikHeap