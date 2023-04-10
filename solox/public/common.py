import json
import os
import platform
import re
import shutil
import time
import requests
from logzero import logger
from solox.public.adb import adb
from tqdm import tqdm
import traceback
from urllib.request import urlopen
import ssl
import xlwt

class Platform:
    Android = 'Android'
    iOS = 'iOS'
    Mac = 'MacOS'
    Windows = 'Windows'

class Devices:

    def __init__(self, platform=Platform.Android):
        self.platform = platform
        self.adb = adb.adb_path

    def execCmd(self, cmd):
        """Execute the command to get the terminal print result"""
        r = os.popen(cmd)
        text = r.read().strip()
        r.close()
        return text

    def filterType(self):
        """Select the pipe filtering method according to the system"""
        filtertype = ('grep', 'findstr')[platform.system() == Platform.Windows]
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
        if platform == Platform.Android:
            deviceId = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", deviceinfo)
            if deviceId not in self.getDeviceIds():
                raise Exception('no found device: %s'.format(deviceId))
        else:
            deviceId = deviceinfo.split(':')[1]
        return deviceId

    def getPid(self, deviceId, pkgName):
        """Get the pid corresponding to the Android package name"""
        result = os.popen(f"{self.adb} -s {deviceId} shell ps -ef | {self.filterType()} {pkgName}").readlines()
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

    def devicesCheck(self, platform, deviceid=None, pkgname=None):
        """Check the device environment"""
        match(platform):
            case Platform.Android:
                if len(self.getDeviceIds()) == 0:
                    raise Exception('no devices')
                if not self.getPid(deviceId=deviceid, pkgName=pkgname):
                    raise Exception('no found app process')
            case Platform.iOS:
                if len(self.getDeviceInfoByiOS()) == 0:
                    raise Exception('no devices')
            case _:
                raise Exception('platform must be Android or iOS')        
            
    def getDdeviceDetail(self, deviceId, platform):
        result = {}
        match(platform):
            case Platform.Android:
                result['brand'] = adb.shell(cmd='getprop ro.product.brand', deviceId=deviceId)
                result['name'] = adb.shell(cmd='getprop ro.product.model', deviceId=deviceId)
                result['version'] = adb.shell(cmd='getprop ro.build.version.release', deviceId=deviceId)
                result['serialno'] = adb.shell(cmd='getprop ro.serialno', deviceId=deviceId)
                cmd = f'ip addr show wlan0 | {self.filterType()} link/ether'
                result['wifiadr'] = adb.shell(cmd=cmd, deviceId=deviceId).split(' ')[1]
            case Platform.iOS:
                iosInfo = json.loads(self.execCmd('tidevice info --json'))
                result['brand'] = iosInfo['DeviceClass']
                result['name'] = iosInfo['DeviceName']
                result['version'] = iosInfo['ProductVersion']
                result['serialno'] = iosInfo['SerialNumber']
                result['wifiadr'] = iosInfo['WiFiAddress']
            case _:
                raise Exception('{} is undefined'.format(platform)) 
        return result       

class file:

    def __init__(self, fileroot='.'):
        self.fileroot = fileroot
        self.report_dir = self.get_repordir()
    
    def export_excel(self, platform, scene):
        
        android_log_file_list = ['cpu_app','cpu_sys','mem_total','mem_native','mem_dalvik',
                                 'battery_level', 'battery_tem','upflow','downflow','fps']
        ios_log_file_list = ['cpu_app','cpu_sys', 'mem_total', 'battery_tem', 'battery_current', 
                             'battery_voltage', 'battery_power','upflow','downflow','fps','gpu']
        log_file_list = android_log_file_list if platform == 'Android' else ios_log_file_list
        wb = xlwt.Workbook(encoding = 'utf-8')
       
        k = 1
        for name in log_file_list:
            ws1 = wb.add_sheet(name)
            ws1.write(0,0,'Time') 
            ws1.write(0,1,'Value')
            row = 1 #start row
            col = 0 #start col
            if os.path.exists(f'{self.report_dir}/{scene}/{name}.log'):
                f = open(f'{self.report_dir}/{scene}/{name}.log','r',encoding='utf-8')
                for lines in f: 
                    target = lines.split('=')
                    k += 1
                    for i in range(len(target)):
                        ws1.write(row, col ,target[i])
                        col += 1
                    row += 1
                    col = 0
        wb.save(f'{scene}.xls')   

    def get_repordir(self):
        report_dir = os.path.join(os.getcwd(), 'report')
        if not os.path.exists(report_dir):
            os.mkdir(report_dir)
        return report_dir

    def create_file(self, filename, content=''):
        if not os.path.exists(self.report_dir):
            os.mkdir(self.report_dir)
        with open(os.path.join(self.report_dir, filename), 'a+', encoding="utf-8") as file:
            file.write(content)

    def add_log(self, path, log_time, value):
        if value >= 0:
            with open(path, 'a+', encoding="utf-8") as file:
                file.write(f'{log_time}={str(value)}' + '\n')
    
    def record_net(self, type, send , recv):
        net_dict = {}
        match(type):
            case 'pre':
                net_dict['send'] = send
                net_dict['recv'] = recv
                content = json.dumps(net_dict)
                self.create_file(filename='pre_net.json', content=content)
            case 'end':
                net_dict['send'] = send
                net_dict['recv'] = recv
                content = json.dumps(net_dict)
                self.create_file(filename='end_net.json', content=content)
            case _:
                logger.error('record network data failed')
    
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
        report_new_dir = os.path.join(self.report_dir, self.fileroot)
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
        if os.path.exists(os.path.join(self.report_dir,scene,filename)):
            f = open(os.path.join(self.report_dir,scene,filename), "r")
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
        
    
    def getCpuLog(self, platform, scene):
        targetDic = {}
        targetDic['cpuAppData'] = self.readLog(scene=scene, filename='cpu_app.log')[0]
        targetDic['cpuSysData'] = self.readLog(scene=scene, filename='cpu_sys.log')[0]
        result = {'status': 1, 'cpuAppData': targetDic['cpuAppData'], 'cpuSysData': targetDic['cpuSysData']}
        return result
    
    def getGpuLog(self, platform, scene):
        targetDic = {}
        targetDic['gpu'] = self.readLog(scene=scene, filename='gpu.log')[0]
        result = {'status': 1, 'gpu': targetDic['gpu']}
        return result
    
    def getMemLog(self, platform, scene):
        targetDic = {}
        targetDic['memTotalData'] = self.readLog(scene=scene, filename='mem_total.log')[0]
        if platform == Platform.Android:
            targetDic['memNativeData']  = self.readLog(scene=scene, filename='mem_native.log')[0]
            targetDic['memDalvikData']  = self.readLog(scene=scene, filename='mem_dalvik.log')[0]
            result = {'status': 1, 
                      'memTotalData': targetDic['memTotalData'], 
                      'memNativeData': targetDic['memNativeData'],
                      'memDalvikData': targetDic['memDalvikData']}
        else:
            result = {'status': 1, 'memTotalData': targetDic['memTotalData']}
        return result
    
    def getBatteryLog(self, platform, scene):
        targetDic = {}
        if platform == Platform.Android:
            targetDic['batteryLevel'] = self.readLog(scene=scene, filename='battery_level.log')[0]
            targetDic['batteryTem'] = self.readLog(scene=scene, filename='battery_tem.log')[0]
            result = {'status': 1, 
                      'batteryLevel': targetDic['batteryLevel'], 
                      'batteryTem': targetDic['batteryTem']}
        else:
            targetDic['batteryTem'] = self.readLog(scene=scene, filename='battery_tem.log')[0]
            targetDic['batteryCurrent'] = self.readLog(scene=scene, filename='battery_current.log')[0]
            targetDic['batteryVoltage'] = self.readLog(scene=scene, filename='battery_voltage.log')[0]
            targetDic['batteryPower'] = self.readLog(scene=scene, filename='battery_power.log')[0]
            result = {'status': 1, 
                      'batteryTem': targetDic['batteryTem'], 
                      'batteryCurrent': targetDic['batteryCurrent'],
                      'batteryVoltage': targetDic['batteryVoltage'], 
                      'batteryPower': targetDic['batteryPower']}    
        return result
    
    def getFlowLog(self, platform, scene):
        targetDic = {}
        targetDic['upFlow'] = self.readLog(scene=scene, filename='upflow.log')[0]
        targetDic['downFlow'] = self.readLog(scene=scene, filename='downflow.log')[0]
        result = {'status': 1, 'upFlow': targetDic['upFlow'], 'downFlow': targetDic['downFlow']}
        return result
    
    def getFpsLog(self, platform, scene):
        targetDic = {}
        targetDic['fps'] = self.readLog(scene=scene, filename='fps.log')[0]
        if platform == Platform.Android:
            targetDic['jank'] = self.readLog(scene=scene, filename='jank.log')[0]
            result = {'status': 1, 'fps': targetDic['fps'], 'jank': targetDic['jank']}
        else:
            result = {'status': 1, 'fps': targetDic['fps']}     
        return result
        
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
        jankAvg = f'{int(sum(jankData))}'
       
        f_pre = open(os.path.join(self.report_dir,scene,'pre_net.json'))
        f_end = open(os.path.join(self.report_dir,scene,'end_net.json'))
        json_pre = json.loads(f_pre.read())
        json_end = json.loads(f_end.read())
        send = json_end['send'] - json_pre['send']
        recv = json_end['recv'] - json_pre['recv']
        flowSend = f'{round(float(send / 1024), 2)}MB'
        flowRecv = f'{round(float(recv / 1024), 2)}MB'
        apm_dict = {}
        apm_dict['cpuAppRate'] = cpuAppRate
        apm_dict['cpuSystemRate'] = cpuSystemRate
        apm_dict['totalPassAvg'] = totalPassAvg
        apm_dict['nativePassAvg'] = nativePassAvg
        apm_dict['dalvikPassAvg'] = dalvikPassAvg
        apm_dict['fps'] = fpsAvg
        apm_dict['jank'] = jankAvg
        apm_dict['flow_send'] = flowSend
        apm_dict['flow_recv'] = flowRecv
        apm_dict['batteryLevel'] = batteryLevel
        apm_dict['batteryTeml'] = batteryTeml
        
        return apm_dict

    def _setiOSPerfs(self, scene):
        """Aggregate APM data for iOS"""
        cpuAppData = self.readLog(scene=scene, filename='cpu_app.log')[1]
        cpuAppRate = f'{round(sum(cpuAppData) / len(cpuAppData), 2)}%'

        cpuSystemData = self.readLog(scene=scene, filename='cpu_sys.log')[1]
        cpuSystemRate = f'{round(sum(cpuSystemData) / len(cpuSystemData), 2)}%'

        totalPassData = self.readLog(scene=scene, filename='mem_total.log')[1]
        totalPassAvg = f'{round(sum(totalPassData) / len(totalPassData), 2)}MB'

        fpsData = self.readLog(scene=scene, filename='fps.log')[1]
        fpsAvg = f'{int(sum(fpsData) / len(fpsData))}HZ/s'

        flowSendData = self.readLog(scene=scene, filename='upflow.log')[1]
        flowSend = f'{round(float(sum(flowSendData) / 1024), 2)}MB'

        flowRecvData = self.readLog(scene=scene, filename='downflow.log')[1]
        flowRecv = f'{round(float(sum(flowRecvData) / 1024), 2)}MB'

        batteryTemlData = self.readLog(scene=scene, filename='battery_tem.log')[1]
        batteryTeml = round(sum(batteryTemlData) / len(batteryTemlData), 2)

        batteryCurrentData = self.readLog(scene=scene, filename='battery_current.log')[1]
        batteryCurrent = round(sum(batteryCurrentData) / len(batteryCurrentData), 2)

        batteryVoltageData = self.readLog(scene=scene, filename='battery_voltage.log')[1]
        batteryVoltage = round(sum(batteryVoltageData) / len(batteryVoltageData), 2)

        batteryPowerData = self.readLog(scene=scene, filename='battery_power.log')[1]
        batteryPower = round(sum(batteryPowerData) / len(batteryPowerData), 2)

        gpuData = self.readLog(scene=scene, filename='gpu.log')[1]
        gpu = round(sum(gpuData) / len(gpuData), 2)

        apm_dict = {}
        apm_dict['cpuAppRate'] = cpuAppRate
        apm_dict['cpuSystemRate'] = cpuSystemRate
        apm_dict['totalPassAvg'] = totalPassAvg
        apm_dict['nativePassAvg'] = 0
        apm_dict['dalvikPassAvg'] = 0
        apm_dict['fps'] = fpsAvg
        apm_dict['jank'] = 0
        apm_dict['flow_send'] = flowSend
        apm_dict['flow_recv'] = flowRecv
        apm_dict['batteryTeml'] = batteryTeml
        apm_dict['batteryCurrent'] = batteryCurrent
        apm_dict['batteryVoltage'] = batteryVoltage
        apm_dict['batteryPower'] = batteryPower
        apm_dict['gpu'] = gpu
        
        return apm_dict

    def _setpkPerfs(self, scene):
        """Aggregate APM data for pk model"""
        cpuAppData1 = self.readLog(scene=scene, filename='cpu_app1.log')[1]
        cpuAppRate1 = f'{round(sum(cpuAppData1) / len(cpuAppData1), 2)}%'
        cpuAppData2 = self.readLog(scene=scene, filename='cpu_app2.log')[1]
        cpuAppRate2 = f'{round(sum(cpuAppData2) / len(cpuAppData2), 2)}%'

        totalPassData1 = self.readLog(scene=scene, filename='mem1.log')[1]
        totalPassAvg1 = f'{round(sum(totalPassData1) / len(totalPassData1), 2)}MB'
        totalPassData2 = self.readLog(scene=scene, filename='mem2.log')[1]
        totalPassAvg2 = f'{round(sum(totalPassData2) / len(totalPassData2), 2)}MB'

        fpsData1 = self.readLog(scene=scene, filename='fps1.log')[1]
        fpsAvg1 = f'{int(sum(fpsData1) / len(fpsData1))}HZ/s'
        fpsData2 = self.readLog(scene=scene, filename='fps2.log')[1]
        fpsAvg2 = f'{int(sum(fpsData2) / len(fpsData2))}HZ/s'

        networkData1 = self.readLog(scene=scene, filename='network1.log')[1]
        network1 = f'{round(float(sum(networkData1) / 1024), 2)}MB'
        networkData2 = self.readLog(scene=scene, filename='network2.log')[1]
        network2 = f'{round(float(sum(networkData2) / 1024), 2)}MB'
        
        apm_dict = {}
        apm_dict['cpuAppRate1'] = cpuAppRate1
        apm_dict['cpuAppRate2'] = cpuAppRate2
        apm_dict['totalPassAvg1'] = totalPassAvg1
        apm_dict['totalPassAvg2'] = totalPassAvg2
        apm_dict['network1'] = network1
        apm_dict['network2'] = network2
        apm_dict['fpsAvg1'] = fpsAvg1
        apm_dict['fpsAvg2'] = fpsAvg2
        return apm_dict


class Method:
    
    @classmethod
    def _request(cls, request, object):
        match(request.method):
            case 'POST':
                return request.form[object]
            case 'GET':
                return request.args[object]
            case _:
                raise Exception('request method error')
    
    @classmethod   
    def _setValue(cls, value, default = 0):
        try:
            result = value
        except ZeroDivisionError :
            result = default    
        except Exception:
            result = default            
        return result

class Install:

    def uploadFile(self, file_path, file_obj):
        """save upload file"""
        try:
            file_obj.save(file_path)
            return True
        except:
            traceback.print_exc()
            return False            

    def downloadLink(self,filelink=None, path=None, name=None):
        try:
            logger.info('Install link : {}'.format(filelink))
            ssl._create_default_https_context = ssl._create_unverified_context
            file_size = int(urlopen(filelink).info().get('Content-Length', -1))
            header = {"Range": "bytes=%s-%s" % (0, file_size)}
            pbar = tqdm(
                total=file_size, initial=0,
                unit='B', unit_scale=True, desc=filelink.split('/')[-1])
            req = requests.get(filelink, headers=header, stream=True)
            with(open(os.path.join(path, name), 'ab')) as f:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                         f.write(chunk)
                         pbar.update(1024)
            pbar.close()
            return True
        except:
            traceback.print_exc()
            return False

    def installAPK(self, path):
        result = adb.shell_noDevice(cmd = 'install -r {}'.format(path))
        if result == 0:
            os.remove(path)
            return True, result
        else:
            return False, result

    def installIPA(self, path):
        result = Devices.execCmd('tidevice install {}'.format(path))
        if result == 0:
            os.remove(path)
            return True, result
        else:
            return False, result
