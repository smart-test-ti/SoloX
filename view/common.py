import re
import os
import subprocess
import shutil
import json

class Devices():

    def __init__(self, platform='mac'):
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
        return devices_name[0].strip()

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
        try:
            pid = (0,result[0].split()[1])[flag]
        except Exception as e:
            print(str(e))
            pid = None    
        return pid

    def checkPkgname(self,pkgname):
        flag = True
        replace_list = ['com.android','com.google','com.xiaomi','com.miui','com.mi','android']
        for i in replace_list:
            if i in pkgname:
                flag = False
        return flag        


    def getPkgname(self):
        """获取手机所有包名"""
        pkginfo  = os.popen("adb shell pm list package")
        pkglist = []
        for p in pkginfo:
            p = p.lstrip('package').lstrip(":").strip()
            if self.checkPkgname(p):
                pkglist.append(p)
        return pkglist

class file():

    def __init__(self, fileroot='.'):
        self.fileroot = fileroot
        self.report_dir = os.path.join(os.getcwd(), 'report')

    def create_file(self,filename,content=''):
        if not os.path.exists(f'{self.report_dir}'):
            os.mkdir(f'{self.report_dir}')
        with open(f'{self.report_dir}/{filename}', 'a+', encoding="utf-8") as file:
            file.write(content)

    def make_report(self):
        result_dict = {
            "app":"com.xxx.xxxx.wechat",
            "icon":"",
            "platform":"Android",
            "devices":"华为Mate20",
            "cpu":"80%",
            "mem":"250MB",
            "fps":"60fps",
            "bettery":"300mA",
            "flow":"200MB",
            "ctime":"2022-2-8 10:10:10"
            }
        content = json.dumps(result_dict)
        self.create_file(filename='result.json',content=content)
        report_new_dir = f'{self.report_dir}/{self.fileroot}'
        if not os.path.exists(report_new_dir):
            os.mkdir(report_new_dir)

        for f in os.listdir(self.report_dir):
            filename = os.path.join(self.report_dir, f)
            if f.split(".")[-1] in ['log','json']:
                shutil.move(filename, report_new_dir)
        if os.path.exists(f'{self.report_dir}/cpu.log'):
             os.remove(f'{self.report_dir}/cpu.log')

class Adb():

    def shell(self,cmd):
        run_cmd  = f'adb shell {cmd}'
        result = subprocess.Popen(run_cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[
            0].decode("utf-8").strip()
        return result
