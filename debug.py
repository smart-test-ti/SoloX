import re
import os
import subprocess
from functools import reduce
import sys
import time

def getPid(pkgName):
    """获取包名对应的pid"""
    result = os.popen(f"adb shell ps | grep {pkgName}").readlines()
    flag = len(result) > 0
    pid = (0,result[0].split()[1])[flag]
    return pid

def getDevices():
    str_init=' '
    all_info= os.popen('adb devices').readlines()
    for i in range(len(all_info)):
        str_init+=all_info[i]
    devices_name=re.findall('\n(.+?)\t',str_init,re.S)
    return  devices_name


def getprocessCpuStat(pkgName):
    pid = getPid(pkgName)
    cmd = f'adb shell cat /proc/{pid}/stat'
    stringBuffer = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode("utf-8").strip()
    r = re.compile("\\s+")
    toks = r.split(stringBuffer)
    processCpu = float(int(toks[13]) + int(toks[14]));
    return processCpu

def getTotalCpuStat():
    cmd = f'adb shell cat /proc/stat |grep ^cpu\ '
    child_out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode("utf-8").strip()
    # print child_out
    r = re.compile(r'(?<!cpu)\d+')
    toks = r.findall(child_out)
    idleCpu = float(toks[3])
    totalCpu = float(reduce(lambda x, y: int(x) + int(y), toks));
    return totalCpu

def getSingCpuRate(pkgName):
    processCpuTime_1 = getprocessCpuStat(pkgName)
    totalCpuTime_1 = getTotalCpuStat()
    time.sleep(0.5)
    processCpuTime_2 = getprocessCpuStat(pkgName)
    totalCpuTime_2 = getTotalCpuStat()
    cpuRate = int((processCpuTime_2 - processCpuTime_1) / (totalCpuTime_2 - totalCpuTime_1) * 100)
    return f'cpu%:{cpuRate}'

def getCPU(pkgName):
    """
    获取APP的CPU损耗占比
    """
    try:
        cmd = f"adb shell top -o ARGS -o %CPU | grep {pkgName}  >> ./test.txt"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cpuvalue = 0
    except IndexError as e:
        print(str(e))
        cpuvalue = 0
    finally:
        print(cpuvalue)
    return f'cpu%:{cpuvalue}'

def getProcessMem(pkgName):
    """获取进程内存Total\NativeHeap\NativeHeap;单位：MB"""
    pid = getPid(pkgName)
    cmd = f'adb shell dumpsys meminfo {pid}'
    output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode("utf-8").strip()
    m = re.search(r'TOTAL\s*(\d+)', output)
    m1 = re.search(r'Native Heap\s*(\d+)', output)
    m2 = re.search(r'Dalvik Heap\s*(\d+)', output)
    PSS = round(float(float(m.group(1))) / 1024, 2)
    NativeHeap = round(float(float(m1.group(1))) / 1024, 2)
    DalvikHeap = round(float(float(m2.group(1))) / 1024, 2)
    return PSS, NativeHeap, NativeHeap


if __name__ == "__main__":
    print(getPid('com.playit.videoplayer'))
    # print(getprocessCpuStat('com.playit.videoplayer'))
    # print(getTotalCpuStat())
    #print(getSingCpuRate('com.playit.videoplayer'))
    #getCPU('com.playit.videoplayer')
    print(getProcessMem('com.playit.videoplayer'))

