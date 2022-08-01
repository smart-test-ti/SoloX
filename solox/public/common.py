import json
import os
import platform
import re
import shutil
import time

from solox.public.adb import adb

class Devices:

    def __init__(self, platform='Android'):
        self.platform = platform
        self.adb = adb.adb_path

    def execCmd(self,cmd):
        """执行命令获取终端打印结果"""
        r = os.popen(cmd)
        text = r.read()
        r.close()
        return text

    def _filterType(self):
        """根据系统选择管道过滤方式"""
        filtertype = ('grep','findstr')[platform.system() == 'Windows']
        return filtertype

    def getDeviceIds(self):
        """获取所有连接成功的设备id"""
        Ids = list(os.popen(f"{self.adb} devices").readlines())
        deviceIds = []
        for i in range(1, len(Ids) - 1):
            output = re.findall(r'^[\w\d.:-]+\t[\w]+$', Ids[i])[0]
            id, state = str(output).split('\t')
            if state == 'device':
                deviceIds.append(id)
        return deviceIds

    def getDevicesName(self, deviceId):
        """获取对应设备Id的设备名称"""
        devices_name = os.popen(f'{self.adb} -s {deviceId} shell getprop ro.product.model').readlines()
        return devices_name[0].strip()

    def getDevices(self):
        """获取所有设备"""
        Devices = []
        DeviceIds = self.getDeviceIds()
        for id in DeviceIds:
            devices_name = self.getDevicesName(id)
            Devices.append(f'{id}({devices_name})')
        return Devices

    def getIdbyDevice(self, deviceinfo,platform):
        """根据设备信息获取对应设备id"""
        if platform == 'Android':
            deviceId = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", deviceinfo)
        else:
            deviceId = deviceinfo.split(':')[1]
        return deviceId

    def getPid(self, deviceId, pkgName):
        """获取对应包名的pid"""
        result = os.popen(f"{self.adb} -s {deviceId} shell ps | {self._filterType()} {pkgName}").readlines()
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
        """获取手机所有包名"""
        pkginfo = os.popen(f"{self.adb} -s {devicesId} shell pm list package")
        pkglist = []
        for p in pkginfo:
            p = p.lstrip('package').lstrip(":").strip()
            if self.checkPkgname(p):
                pkglist.append(p)
        return pkglist

    def getDeviceInfoByiOS(self):
        """获取所有连接成功的iOS设备列表"""
        deviceResult = json.loads(self.execCmd('tidevice list --json'))
        deviceInfo = []
        for i in range(len(deviceResult)):
            deviceName = deviceResult[i]['name']
            deviceUdid = deviceResult[i]['udid']
            deviceInfo.append(f'{deviceName}:{deviceUdid}')
        return deviceInfo

    def getPkgnameByiOS(self,udid):
        """获取对应iOS设备所有包名"""
        pkgResult = self.execCmd(f'tidevice --udid {udid} applist').split('\n')
        pkgNames = []
        for i in range(len(pkgResult)):
            pkgNames.append(pkgResult[i].split(' ')[0])
        return pkgNames


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

    def make_report(self, app, devices, platform='Android'):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        result_dict = {
            "app": app,
            "icon": "",
            "platform": platform,
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
        """读取apmlog文件数据"""
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


    def approximateSize(self,size, a_kilobyte_is_1024_bytes=True):
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


    def _setAndroidPerfs(self,scene):
        """汇总Android的APM数据"""
        cpu_data = self.readLog(scene=scene, filename=f'cpu.log')[1]
        cpu_rate = f'{round(sum(cpu_data) / len(cpu_data), 2)}%'

        battery_data = self.readLog(scene=scene, filename=f'battery.log')[1]
        battery_rate = f'{round(sum(battery_data) / len(battery_data), 2)}%'

        mem_data = self.readLog(scene=scene, filename=f'mem.log')[1]
        mem_avg = f'{round(sum(mem_data) / len(mem_data), 2)}MB'

        fps_data = self.readLog(scene=scene, filename=f'fps.log')[1]
        fps_avg = f'{int(sum(fps_data) / len(fps_data))}HZ/s'

        jank_data = self.readLog(scene=scene, filename=f'jank.log')[1]
        jank_avg = f'{int(sum(jank_data) / len(jank_data))}'

        flow_send_data = self.readLog(scene=scene, filename=f'upflow.log')[1]
        flow_send_data_all = f'{round(flow_send_data[len(flow_send_data) - 1] - flow_send_data[0], 2)}MB'

        flow_recv_data = self.readLog(scene=scene, filename=f'downflow.log')[1]
        flow_recv_data_all = f'{round(flow_recv_data[len(flow_recv_data) - 1] - flow_recv_data[0], 2)}MB'
        apm_dict = {
            "cpu": cpu_rate,
            "mem": mem_avg,
            "fps": fps_avg,
            "jank": jank_avg,
            "flow_send": flow_send_data_all,
            "flow_recv": flow_recv_data_all,
            "battery": battery_rate
        }

        return apm_dict

    def _setiOSPerfs(self, scene):
        """汇总iOS的APM数据"""
        cpu_data = self.readLog(scene=scene, filename=f'cpu.log')[1]
        cpu_rate = f'{round(sum(cpu_data) / len(cpu_data), 2)}%'

        mem_data = self.readLog(scene=scene, filename=f'mem.log')[1]
        mem_avg = f'{round(sum(mem_data) / len(mem_data), 2)}MB'

        # fps_data = self.readLog(scene=scene, filename=f'fps.log')[1]
        # fps_avg = f'{int(sum(fps_data) / len(fps_data))}HZ/s'

        flow_send_data = self.readLog(scene=scene, filename=f'upflow.log')[1]
        flow_send_data_all = f'{round((sum(flow_send_data)),2)}KB'

        flow_recv_data = self.readLog(scene=scene, filename=f'downflow.log')[1]
        flow_recv_data_all = f'{round((sum(flow_recv_data)),2)}KB'

        apm_dict = {
            "cpu": cpu_rate,
            "mem": mem_avg,
            "fps": 0,
            "flow_send": flow_send_data_all,
            "flow_recv": flow_recv_data_all,
            "jank": 0,
            "battery": 0
        }

        return apm_dict

