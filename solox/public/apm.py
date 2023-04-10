import datetime
import re
import time
import os
from logzero import logger
import tidevice
import solox.public._iosPerf as iosP
from solox.public.iosperf._perf import DataType, Performance
from solox.public.adb import adb
from solox.public.common import Devices, file, Method, Platform
from solox.public.fps import FPSMonitor, TimeUtils

d = Devices()
f = file()
m = Method()

class Target:
    CPU = 'cpu'
    Memory = 'memory'
    Battery = 'battery'
    Network = 'network'
    FPS = 'fps'
    GPU = 'gpu'

class CPU(object):

    def __init__(self, pkgName, deviceId, platform='Android'):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform

    def getprocessCpuStat(self):
        """get the cpu usage of a process at a certain time"""
        pid = d.getPid(pkgName=self.pkgName, deviceId=self.deviceId)
        cmd = f'cat /proc/{pid}/stat'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        r = re.compile("\\s+")
        toks = r.split(result)
        processCpu = float(int(toks[13]) + int(toks[14]) + int(toks[15]) + int(toks[16]))
        return processCpu

    def getTotalCpuStat(self):
        """get the total cpu usage at a certain time"""
        cmd = f'cat /proc/stat |{d.filterType()} ^cpu'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        totalCpu = 0
        for i in range(1, 9):
            totalCpu += float(toks[i])
        return float(totalCpu)

    def getCpuCores(self):
        """get Android cpu cores"""
        cmd = f'cat /sys/devices/system/cpu/online'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        try:
            nums = int(result.split('-')[1]) + 1
        except:
            nums = 1
        return nums

    def getSysCpuStat(self):
        """get the total cpu usage at a certain time"""
        cmd = f'cat /proc/stat |{d.filterType()} ^cpu'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        ileCpu = int(toks[4])
        sysCpu = self.getTotalCpuStat() - ileCpu
        return sysCpu

    def getAndroidCpuRate(self, sueApi=False):
        """get the Android cpu rate of a process"""
        processCpuTime_1 = self.getprocessCpuStat()
        totalCpuTime_1 = self.getTotalCpuStat()
        sysCpuTime_1 = self.getSysCpuStat()
        time.sleep(1)
        processCpuTime_2 = self.getprocessCpuStat()
        totalCpuTime_2 = self.getTotalCpuStat()
        sysCpuTime_2 = self.getSysCpuStat()
        appCpuRate = round(float((processCpuTime_2 - processCpuTime_1) / (totalCpuTime_2 - totalCpuTime_1) * 100), 2)
        sysCpuRate = round(float((sysCpuTime_2 - sysCpuTime_1) / (totalCpuTime_2 - totalCpuTime_1) * 100), 2)
        if sueApi is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'cpu_app.log'), apm_time, appCpuRate)
            f.add_log(os.path.join(f.report_dir,'cpu_sys.log'), apm_time, sysCpuRate)

        return appCpuRate, sysCpuRate

    def getiOSCpuRate(self, sueApi=False):
        """get the iOS cpu rate of a process, unit:%"""
        apm = iosAPM(self.pkgName)
        appCpuRate = round(float(apm.getPerformance(apm.cpu)[0]), 2)
        sysCpuRate = round(float(apm.getPerformance(apm.cpu)[1]), 2)
        if sueApi is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'cpu_app.log'), apm_time, appCpuRate)
            f.add_log(os.path.join(f.report_dir,'cpu_sys.log'), apm_time, sysCpuRate)
        return appCpuRate, sysCpuRate

    def getCpuRate(self, noLog=False):
        """Get the cpu rate of a process, unit:%"""
        appCpuRate, systemCpuRate = self.getAndroidCpuRate(noLog) if self.platform == Platform.Android else self.getiOSCpuRate(noLog)
        return appCpuRate, systemCpuRate


class MEM(object):
    def __init__(self, pkgName, deviceId, platform=Platform.Android):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform

    def getAndroidMem(self):
        """Get the Android memory ,unit:MB"""
        pid = d.getPid(pkgName=self.pkgName, deviceId=self.deviceId)
        cmd = f'dumpsys meminfo {pid}'
        output = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m_total = re.search(r'TOTAL\s*(\d+)', output)
        m_native = re.search(r'Native Heap\s*(\d+)', output)
        m_dalvik = re.search(r'Dalvik Heap\s*(\d+)', output)
        totalPass = round(float(float(m_total.group(1))) / 1024, 2)
        nativePass = round(float(float(m_native.group(1))) / 1024, 2)
        dalvikPass = round(float(float(m_dalvik.group(1))) / 1024, 2)
        return totalPass, nativePass, dalvikPass

    def getiOSMem(self):
        """Get the iOS memory"""
        apm = iosAPM(self.pkgName)
        totalPass = round(float(apm.getPerformance(apm.memory)), 2)
        nativePass = 0
        dalvikPass = 0
        return totalPass, nativePass, dalvikPass

    def getProcessMem(self, noLog=False):
        """Get the app memory"""
        totalPass, nativePass, dalvikPass = self.getAndroidMem() if self.platform == Platform.Android else self.getiOSMem()
        if noLog is False:    
            time.sleep(1)    
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'mem_total.log'), apm_time, totalPass)
            if self.platform == Platform.Android:
                f.add_log(os.path.join(f.report_dir,'mem_native.log'), apm_time, nativePass)
                f.add_log(os.path.join(f.report_dir,'mem_dalvik.log'), apm_time, dalvikPass)
        return totalPass, nativePass, dalvikPass


class Battery(object):
    def __init__(self, deviceId, platform=Platform.Android):
        self.deviceId = deviceId
        self.platform = platform
    
    def getBattery(self, noLog=False):
        if self.platform == Platform.Android:
            level, temperature = self.getAndroidBattery(noLog)
            return level, temperature
        else:
            temperature, current, voltage, power = self.getiOSBattery(noLog)
            return temperature, current, voltage, power
        
    def getAndroidBattery(self, noLog=False):
        """Get android battery info, unit:%"""
        # Switch mobile phone battery to non-charging state
        cmd = 'dumpsys battery set status 1'
        adb.shell(cmd=cmd, deviceId=self.deviceId)
        # Get phone battery info
        cmd = 'dumpsys battery'
        output = adb.shell(cmd=cmd, deviceId=self.deviceId)
        level = int(re.findall(u'level:\s?(\d+)', output)[0])
        temperature = int(re.findall(u'temperature:\s?(\d+)', output)[0]) / 10
        if noLog is False:
             time.sleep(1)
             apm_time = datetime.datetime.now().strftime('%H:%M:%S')
             f.add_log(os.path.join(f.report_dir,'battery_level.log'), apm_time, level)
             f.add_log(os.path.join(f.report_dir,'battery_tem.log'), apm_time, temperature)
        return level, temperature
    
    def getiOSBattery(self, noLog=False):
        """Get ios battery info, unit:%"""
        d  = tidevice.Device()
        ioDict =  d.get_io_power()
        tem = m._setValue(ioDict['Diagnostics']['IORegistry']['Temperature'])
        current = m._setValue(abs(ioDict['Diagnostics']['IORegistry']['InstantAmperage']))
        voltage = m._setValue(ioDict['Diagnostics']['IORegistry']['Voltage'])
        power = current * voltage / 1000
        if noLog is False:
            time.sleep(1)
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'battery_tem.log'), apm_time, tem) # unknown
            f.add_log(os.path.join(f.report_dir,'battery_current.log'), apm_time, current) #mA
            f.add_log(os.path.join(f.report_dir,'battery_voltage.log'), apm_time, voltage) #mV
            f.add_log(os.path.join(f.report_dir,'battery_power.log'), apm_time, power)
        return tem, current, voltage, power

    def recoverBattery(self):
        """Reset phone charging status"""
        cmd = 'dumpsys battery reset'
        adb.shell(cmd=cmd, deviceId=self.deviceId)


class Flow(object):

    def __init__(self, pkgName, deviceId, platform=Platform.Android):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform

    def getAndroidNet(self, wifi=True):
        """Get Android send/recv data, unit:KB wlan0/rmnet0"""
        net = 'wlan0' if wifi else 'rmnet0'
        pid = d.getPid(pkgName=self.pkgName, deviceId=self.deviceId)
        cmd = f'cat /proc/{pid}/net/dev |{d.filterType()} {net}'
        output_pre = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m_pre = re.search(r'{}:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)'.format(net), output_pre)
        sendNum_pre = round(float(float(m_pre.group(2)) / 1024), 2)
        recNum_pre = round(float(float(m_pre.group(1)) / 1024), 2)
        time.sleep(1)
        output_final = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m_final = re.search(r'{}:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)'.format(net), output_final)
        sendNum_final = round(float(float(m_final.group(2)) / 1024), 2)
        recNum_final = round(float(float(m_final.group(1)) / 1024), 2)
        sendNum = round(float(sendNum_final - sendNum_pre), 2)
        recNum = round(float(recNum_final - recNum_pre), 2)
        return sendNum, recNum
    
    def setAndroidNet(self, wifi=True):
        net = 'wlan0' if wifi else 'rmnet0'
        pid = d.getPid(pkgName=self.pkgName, deviceId=self.deviceId)
        cmd = f'cat /proc/{pid}/net/dev |{d.filterType()} {net}'
        output_pre = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m = re.search(r'{}:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)'.format(net), output_pre)
        sendNum = round(float(float(m.group(2)) / 1024), 2)
        recNum = round(float(float(m.group(1)) / 1024), 2)
        return sendNum, recNum


    def getiOSNet(self):
        """Get iOS upflow and downflow data"""
        apm = iosAPM(self.pkgName)
        apm_data = apm.getPerformance(apm.network)
        sendNum = round(float(apm_data[1]), 2)
        recNum = round(float(apm_data[0]), 2)
        return sendNum, recNum

    def getNetWorkData(self, wifi=True, noLog=False):
        """Get the upflow and downflow data, unit:KB"""
        sendNum, recNum = self.getAndroidNet(wifi) if self.platform == Platform.Android else self.getiOSNet()
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'upflow.log'), apm_time, sendNum)
            f.add_log(os.path.join(f.report_dir,'downflow.log'), apm_time, recNum)
        return sendNum, recNum


class FPS(object):

    def __init__(self, pkgName, deviceId, platform=Platform.Android, surfaceview=True):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform
        self.surfaceview = surfaceview
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')

    def getAndroidFps(self, noLog=False):
        """get Android Fps, unit:HZ"""
        monitors = FPSMonitor(device_id=self.deviceId, package_name=self.pkgName, frequency=1,
                              surfaceview=self.surfaceview, start_time=TimeUtils.getCurrentTimeUnderline())
        monitors.start()
        fps, jank = monitors.stop()
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'fps.log'), apm_time, fps)
            f.add_log(os.path.join(f.report_dir,'jank.log'), apm_time, jank)
        return fps, jank

    def getiOSFps(self, noLog=False):
        """get iOS Fps"""
        apm = iosAPM(self.pkgName)
        fps = int(apm.getPerformance(apm.fps))
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'fps.log'), apm_time, fps)
        return fps, 0

    def getFPS(self, noLog=False):
        """get fps、jank"""
        fps, jank = self.getAndroidFps(noLog) if self.platform == Platform.Android else self.getiOSFps(noLog)
        return fps, jank

class GPU(object):
    def __init__(self, pkgName):
        self.pkgName = pkgName

    def getGPU(self, noLog=False):
        apm = iosAPM(self.pkgName)
        gpu = apm.getPerformance(apm.gpu)
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S')
            f.add_log(os.path.join(f.report_dir,'gpu.log'), apm_time, gpu)
        return gpu   

class iosAPM(object):

    def __init__(self, pkgName, deviceId=tidevice.Device()):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
        self.cpu = DataType.CPU
        self.memory = DataType.MEMORY
        self.network = DataType.NETWORK
        self.fps = DataType.FPS
        self.gpu = DataType.GPU
        self.perfs = 0
        self.app_cpu = 0
        self.sys_cpu = 0
        self.downflow = 0
        self.upflow = 0

    def callback(self, _type: DataType, value: dict):
        if _type == 'network':
            self.downflow = value['downFlow']
            self.upflow = value['upFlow']
        else:
            self.perfs = value['value']

    def getPerformance(self, perfTpe: DataType):
        if perfTpe == DataType.NETWORK:
            perf = Performance(self.deviceId, [perfTpe])
            perf.start(self.pkgName, callback=self.callback)
            time.sleep(3)
            perf.stop()
            perf_value = self.downflow, self.upflow
        else:
            perf = iosP.Performance(self.deviceId, [perfTpe])
            perf_value = perf.start(self.pkgName, callback=self.callback)
        return perf_value


class APM(object):
    """for python api"""

    def __init__(self, pkgName, deviceId='', platform=Platform.Android, surfaceview=True, noLog=True):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform
        self.surfaceview = surfaceview
        self.noLog = noLog
        d.devicesCheck(platform=self.platform, deviceid=self.deviceId, pkgname=self.pkgName)

    def collectCpu(self):
        _cpu = CPU(self.pkgName, self.deviceId, self.platform)
        appCpuRate, systemCpuRate = _cpu.getCpuRate(noLog=self.noLog)
        result = {'appCpuRate': appCpuRate, 'systemCpuRate': systemCpuRate}
        logger.info(f'cpu: {result}')
        return result

    def collectMemory(self):
        _memory = MEM(self.pkgName, self.deviceId, self.platform)
        totalPass, nativePass, dalvikPass = _memory.getProcessMem(noLog=self.noLog)
        result = {'totalPass': totalPass, 'nativePass': nativePass, 'dalvikPass': dalvikPass}
        logger.info(f'memory: {result}')
        return result

    def collectBattery(self):
        _battery = Battery(self.deviceId, self.platform)
        final = _battery.getBattery(noLog=self.noLog)
        if self.platform == Platform.Android:
            result = {'level': final[0], 'temperature': final[1]}
        else:
            result = {'temperature': final[0], 'current': final[1], 'voltage': final[2], 'power': final[3]}
        logger.info(f'battery: {result}')
        return result

    def collectFlow(self, wifi=True):
        _flow = Flow(self.pkgName, self.deviceId, self.platform)
        upFlow, downFlow = _flow.getNetWorkData(wifi=wifi,noLog=self.noLog)
        result = {'upFlow': upFlow, 'downFlow': downFlow}
        logger.info(f'network: {result}')
        return result

    def collectFps(self):
        _fps = FPS(self.pkgName, self.deviceId, self.platform, self.surfaceview)
        fps, jank = _fps.getFPS(noLog=self.noLog)
        result = {'fps': fps, 'jank': jank}
        logger.info(f'fps: {result}')
        return result
    
    def collectGpu(self):
        _gpu = GPU(self.pkgName)
        if self.platform == Platform.Android:
            raise Exception('not support android')
        gpu = _gpu.getGPU(noLog=self.noLog)
        result = {'gpu': gpu}
        logger.info(f'gpu: {result}')
        return result
