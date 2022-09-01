import json
import os
import platform
import re
import shutil
import time
from flask import request
from solox.public.adb import adb


class Devices:

    def __init__(self, platform='Android'):
        self.platform = platform
        self.adb = adb.adb_path

    def execCmd(self, cmd):
        """Execute the command to get the terminal print result"""
        r = os.popen(cmd)
        text = r.read()
        r.close()
        return text

    def _filterType(self):
        """Select the pipe filtering method according to the system"""
        filtertype = ('grep', 'findstr')[platform.system() == 'Windows']
        return filtertype

    def getDeviceIds(self):
        """Get all connected device ids"""
        Ids = list(os.popen(f"{self.adb} devices").readlines())
        deviceIds = []
        for i in range(1, len(Ids) - 1):
            output = re.findall(r'^[\w\d.:-]+\t[\w]+$', Ids[i])[0]
            id, state = str(output).split('\t')
            if state == 'device':
                deviceIds.append(id)
        return deviceIds

    def getDevicesName(self, deviceId):
        """Get the device name of the Android corresponding device ID"""
        devices_name = os.popen(f'{self.adb} -s {deviceId} shell getprop ro.product.model').readlines()
        return devices_name[0].strip()

    def getDevices(self):
        """Get all Android devices"""
        Devices = []
        DeviceIds = self.getDeviceIds()
        for id in DeviceIds:
            devices_name = self.getDevicesName(id)
            Devices.append(f'{id}({devices_name})')
        return Devices

    def getIdbyDevice(self, deviceinfo, platform):
        """Obtain the corresponding device id according to the Android device information"""
        if platform == 'Android':
            deviceId = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", deviceinfo)
        else:
            deviceId = deviceinfo.split(':')[1]
        return deviceId

    def getPid(self, deviceId, pkgName):
        """Get the pid corresponding to the Android package name"""
        result = os.popen(f"{self.adb} -s {deviceId} shell ps -ef | {self._filterType()} {pkgName}").readlines()
        flag = len(result) > 0
        try:
            pid = (0, result[0].split()[1])[flag]
        except Exception:
            pid = None
        return pid

    def checkPkgname(self, pkgname):
        flag = True
        replace_list = ['com.google']
        for i in replace_list:
            if i in pkgname:
                flag = False
        return flag

    def getPkgname(self, devicesId):
        """Get all package names of Android devices"""
        pkginfo = os.popen(f"{self.adb} -s {devicesId} shell pm list package")
        pkglist = []
        for p in pkginfo:
            p = p.lstrip('package').lstrip(":").strip()
            if self.checkPkgname(p):
                pkglist.append(p)
        return pkglist

    def getDeviceInfoByiOS(self):
        """Get a list of all successfully connected iOS devices"""
        deviceResult = json.loads(self.execCmd('tidevice list --json'))
        deviceInfo = []
        for i in range(len(deviceResult)):
            deviceName = deviceResult[i]['name']
            deviceUdid = deviceResult[i]['udid']
            deviceInfo.append(f'{deviceName}:{deviceUdid}')
        return deviceInfo

    def getPkgnameByiOS(self, udid):
        """Get all package names of the corresponding iOS device"""
        pkgResult = self.execCmd(f'tidevice --udid {udid} applist').split('\n')
        pkgNames = []
        for i in range(len(pkgResult)):
            pkgNames.append(pkgResult[i].split(' ')[0])
        return pkgNames

    def _devicesCheck(self, pf, id='', pkg=''):
        """Check the device environment"""
        if pf == 'Android':
            if len(self.getDeviceIds()) == 0:
                raise Exception('no devices')
            if not self.getPid(deviceId=id, pkgName=pkg):
                raise Exception('no found app process')
        elif pf == 'iOS':
            if len(self.getDeviceInfoByiOS()) == 0:
                raise Exception('no devices')
        else:
            raise Exception('platform must be Android or iOS')


class file:

    def __init__(self, fileroot='.'):
        self.fileroot = fileroot
        self.report_dir = self.get_repordir()

    def get_repordir(self):
        report_dir = os.path.join(os.getcwd(), 'report')
        if not os.path.exists(report_dir):
            os.mkdir(report_dir)
        return report_dir

    def create_file(self, filename, content=''):
        if not os.path.exists(f'{self.report_dir}'):
            os.mkdir(f'{self.report_dir}')
        with open(f'{self.report_dir}/{filename}', 'a+', encoding="utf-8") as file:
            file.write(content)

    def add_log(self, path, log_time, value):
        if value >= 0:
            with open(path, 'a+', encoding="utf-8") as file:
                file.write(f'{log_time}={str(value)}' + '\n')

    def make_report(self, app, devices, platform='Android', model='normal'):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        result_dict = {
            "app": app,
            "icon": "",
            "platform": platform,
            "model": model,
            "devices": devices,
            "ctime": current_time
        }
        content = json.dumps(result_dict)
        self.create_file(filename='result.json', content=content)
        report_new_dir = f'{self.report_dir}/{self.fileroot}'
        if not os.path.exists(report_new_dir):
            os.mkdir(report_new_dir)

        for f in os.listdir(self.report_dir):
            filename = os.path.join(self.report_dir, f)
            if f.split(".")[-1] in ['log', 'json']:
                shutil.move(filename, report_new_dir)

    def instance_type(self, data):
        if isinstance(data, float):
            return 'float'
        elif isinstance(data, int):
            return 'int'
        else:
            return 'int'

    def readLog(self, scene, filename):
        """Read apmlog file data"""
        log_data_list = []
        target_data_list = []
        f = open(f'{self.report_dir}/{scene}/{filename}', "r")
        lines = f.readlines()
        for line in lines:
            if isinstance(line.split('=')[1].strip(), int):
                log_data_list.append({
                    "x": line.split('=')[0].strip(),
                    "y": int(line.split('=')[1].strip())
                })
                target_data_list.append(int(line.split('=')[1].strip()))
            else:
                log_data_list.append({
                    "x": line.split('=')[0].strip(),
                    "y": float(line.split('=')[1].strip())
                })
                target_data_list.append(float(line.split('=')[1].strip()))
        return log_data_list, target_data_list

    def approximateSize(self, size, a_kilobyte_is_1024_bytes=True):
        '''
        convert a file size to human-readable form.
        Keyword arguments:
        size -- file size in bytes
        a_kilobyte_is_1024_bytes -- if True (default),use multiples of 1024
                                    if False, use multiples of 1000
        Returns: string
        '''

        suffixes = {1000: ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
                    1024: ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']}

        if size < 0:
            raise ValueError('number must be non-negative')

        multiple = 1024 if a_kilobyte_is_1024_bytes else 1000

        for suffix in suffixes[multiple]:
            size /= multiple
            if size < multiple:
                return '{0:.2f} {1}'.format(size, suffix)

    def _setAndroidPerfs(self, scene):
        """Aggregate APM data for Android"""

        cpuAppData = self.readLog(scene=scene, filename=f'cpu_app.log')[1]
        cpuAppRate = f'{round(sum(cpuAppData) / len(cpuAppData), 2)}%'

        cpuSystemData = self.readLog(scene=scene, filename=f'cpu_sys.log')[1]
        cpuSystemRate = f'{round(sum(cpuSystemData) / len(cpuSystemData), 2)}%'

        batteryLevelData = self.readLog(scene=scene, filename=f'battery_level.log')[1]
        batteryLevel = f'{round(sum(batteryLevelData) / len(batteryLevelData), 2)}%'

        batteryTemlData = self.readLog(scene=scene, filename=f'battery_tem.log')[1]
        batteryTeml = f'{round(sum(batteryTemlData) / len(batteryTemlData), 2)}°C'

        totalPassData = self.readLog(scene=scene, filename=f'mem_total.log')[1]
        totalPassAvg = f'{round(sum(totalPassData) / len(totalPassData), 2)}MB'

        nativePassData = self.readLog(scene=scene, filename=f'mem_native.log')[1]
        nativePassAvg = f'{round(sum(nativePassData) / len(nativePassData), 2)}MB'

        dalvikPassData = self.readLog(scene=scene, filename=f'mem_dalvik.log')[1]
        dalvikPassAvg = f'{round(sum(dalvikPassData) / len(dalvikPassData), 2)}MB'

        fpsData = self.readLog(scene=scene, filename=f'fps.log')[1]
        fpsAvg = f'{int(sum(fpsData) / len(fpsData))}HZ/s'

        jankData = self.readLog(scene=scene, filename=f'jank.log')[1]
        jankAvg = f'{int(sum(jankData) / len(jankData))}'

        flowSendData = self.readLog(scene=scene, filename=f'upflow.log')[1]
        flowSend = f'{round(float(sum(flowSendData) / 1024), 2)}MB'

        flowRecvData = self.readLog(scene=scene, filename=f'downflow.log')[1]
        flowRecv = f'{round(float(sum(flowRecvData) / 1024), 2)}MB'

        apm_dict = {
            "cpuAppRate": cpuAppRate,
            "cpuSystemRate": cpuSystemRate,
            "totalPassAvg": totalPassAvg,
            "nativePassAvg": nativePassAvg,
            "dalvikPassAvg": dalvikPassAvg,
            "fps": fpsAvg,
            "jank": jankAvg,
            "flow_send": flowSend,
            "flow_recv": flowRecv,
            "batteryLevel": batteryLevel,
            "batteryTeml": batteryTeml
        }

        return apm_dict

    def _setiOSPerfs(self, scene):
        """Aggregate APM data for iOS"""
        cpuAppData = self.readLog(scene=scene, filename=f'cpu_app.log')[1]
        cpuAppRate = f'{round(sum(cpuAppData) / len(cpuAppData), 2)}%'

        totalPassData = self.readLog(scene=scene, filename=f'mem_total.log')[1]
        totalPassAvg = f'{round(sum(totalPassData) / len(totalPassData), 2)}MB'

        fpsData = self.readLog(scene=scene, filename=f'fps.log')[1]
        fpsAvg = f'{int(sum(fpsData) / len(fpsData))}HZ/s'

        flowSendData = self.readLog(scene=scene, filename=f'upflow.log')[1]
        flowSend = f'{round(float(sum(flowSendData) / 1024), 2)}MB'

        flowRecvData = self.readLog(scene=scene, filename=f'downflow.log')[1]
        flowRecv = f'{round(float(sum(flowRecvData) / 1024), 2)}MB'

        apm_dict = {
            "cpuAppRate": cpuAppRate,
            "cpuSystemRate": 0,
            "totalPassAvg": totalPassAvg,
            "nativePassAvg": 0,
            "dalvikPassAvg": 0,
            "fps": fpsAvg,
            "jank": 0,
            "flow_send": flowSend,
            "flow_recv": flowRecv,
            "batteryLevel": 0,
            "batteryTeml": 0
        }

        return apm_dict

    def _setpkPerfs(self, scene):
        """Aggregate APM data for pk model"""
        cpuAppData1 = self.readLog(scene=scene, filename=f'cpu_app1.log')[1]
        cpuAppRate1 = f'{round(sum(cpuAppData1) / len(cpuAppData1), 2)}%'
        cpuAppData2 = self.readLog(scene=scene, filename=f'cpu_app2.log')[1]
        cpuAppRate2 = f'{round(sum(cpuAppData2) / len(cpuAppData2), 2)}%'

        totalPassData1 = self.readLog(scene=scene, filename=f'mem1.log')[1]
        totalPassAvg1 = f'{round(sum(totalPassData1) / len(totalPassData1), 2)}MB'
        totalPassData2 = self.readLog(scene=scene, filename=f'mem2.log')[1]
        totalPassAvg2 = f'{round(sum(totalPassData2) / len(totalPassData2), 2)}MB'

        fpsData1 = self.readLog(scene=scene, filename=f'fps1.log')[1]
        fpsAvg1 = f'{int(sum(fpsData1) / len(fpsData1))}HZ/s'
        fpsData2 = self.readLog(scene=scene, filename=f'fps2.log')[1]
        fpsAvg2 = f'{int(sum(fpsData2) / len(fpsData2))}HZ/s'

        networkData1 = self.readLog(scene=scene, filename=f'network1.log')[1]
        network1 = f'{round(float(sum(networkData1) / 1024), 2)}MB'
        networkData2 = self.readLog(scene=scene, filename=f'network2.log')[1]
        network2 = f'{round(float(sum(networkData2) / 1024), 2)}MB'

        apm_dict = {
            "cpuAppRate1": cpuAppRate1,
            "cpuAppRate2": cpuAppRate2,
            "totalPassAvg1": totalPassAvg1,
            "totalPassAvg2": totalPassAvg2,
            "network1": network1,
            "network2": network2,
            "fpsAvg1": fpsAvg1,
            "fpsAvg2": fpsAvg2
        }

        return apm_dict


class Method:

    def _request(self, object):

        if request.method == 'POST':
            return request.form[object]
        elif request.method == 'GET':
            return request.args[object]
        else:
            raise Exception('request method error')
