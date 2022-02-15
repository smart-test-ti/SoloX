import re
import os
import subprocess

class Devices():

    def __init__(self, platform):
        self.platform = platform

    def getDeviceIds(self):
        """获取所有连接成功的设备id"""
        Ids = list(os.popen("adb devices").readlines())
        deviceIds = []
        for i in range(1, len(Ids)-1):
            id = re.findall(r"^\w*\b", Ids[i])[0]
            deviceIds.append(id)
        return deviceIds

    def getDevicesName(self,deviceId):
        """获取对应设备Id的设备名称"""
        devices_name = os.popen(f'adb -s {deviceId} shell getprop ro.product.model').readlines()
        return devices_name

    def getDevices(self):
        """获取所有设备"""
        Devices = []
        DeviceIds = self.getDeviceIds()
        for id in DeviceIds:
            devices_name =  self.getDevicesName(id)
            Devices.append(f'{id}({devices_name})')
        return Devices

    def getIdbyDevice(self,deviceinfo):
        """根据设备信息获取对应设备id"""
        deviceId = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", deviceinfo)
        return deviceId

    def getPid(self,deviceId,pkgName):
        """获取对应包名的pid"""
        result = os.popen(f"adb -s {deviceId} shell ps | grep {pkgName}").readlines()
        flag = len(result) > 0
        pid = (0,result[0].split()[1])[flag]
        return pid

class Adb():

    def shell(self,cmd):
        run_cmd  = f'adb shell {cmd}'
        result = subprocess.Popen(run_cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[
            0].decode("utf-8").strip()
        return result
