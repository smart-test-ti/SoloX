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
import socket
from urllib.request import urlopen
import ssl
import xlwt
import psutil
import signal
import cv2
from functools import wraps
from jinja2 import Environment, FileSystemLoader
 
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
        text = r.buffer.read().decode(encoding='gbk').replace('\x1b[0m','').strip()
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
        DeviceIds = self.getDeviceIds()
        Devices = [f'{id}({self.getDevicesName(id)})' for id in DeviceIds]
        logger.info('Connected devices: {}'.format(Devices))
        return Devices

    def getIdbyDevice(self, deviceinfo, platform):
        """Obtain the corresponding device id according to the Android device information"""
        if platform == Platform.Android:
            deviceId = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", deviceinfo)
            if deviceId not in self.getDeviceIds():
                raise Exception('no device found')
        else:
            deviceId = deviceinfo.split(':')[1]
        return deviceId

    def getPid(self, deviceId, pkgName):
        """Get the pid corresponding to the Android package name"""
        try:
            sdkversion = adb.shell(cmd='getprop ro.build.version.sdk', deviceId=deviceId)
            if sdkversion and int(sdkversion) < 26:
                result = os.popen(f"{self.adb} -s {deviceId} shell ps | {self.filterType()} {pkgName}").readlines()
                processList = ['{}:{}'.format(process.split()[1],process.split()[8]) for process in result]
            else:
                result = os.popen(f"{self.adb} -s {deviceId} shell ps -ef | {self.filterType()} {pkgName}").readlines()
                processList = ['{}:{}'.format(process.split()[1],process.split()[7]) for process in result]
            for i in range(len(processList)):
                if processList[i].count(':') == 1:
                    index = processList.index(processList[i])
                    processList.insert(0, processList.pop(index))
                    break
            if len(processList) == 0:
               logger.warning('{}: no pid found'.format(pkgName))     
        except Exception as e:
            processList = []
            logger.exception(e)
        return processList

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
        logger.info('Connected devices: {}'.format(deviceInfo))    
        return deviceInfo

    def getPkgnameByiOS(self, udid):
        """Get all package names of the corresponding iOS device"""
        pkgResult = self.execCmd(f'tidevice --udid {udid} applist').split('\n')
        pkgNames = [pkgResult[i].split(' ')[0] for i in range(len(pkgResult))]
        return pkgNames
    
    def get_pc_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            logger.error('get local ip failed')
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def get_device_ip(self, deviceId):
        content = os.popen(f"{self.adb} -s {deviceId} shell ip addr show wlan0").read()
        logger.info(content)
        math_obj = re.search(r'inet\s(\d+\.\d+\.\d+\.\d+).*?wlan0', content)
        if math_obj and math_obj.group(1):
            return math_obj.group(1)
        return None
    
    def devicesCheck(self, platform, deviceid=None, pkgname=None):
        """Check the device environment"""
        match(platform):
            case Platform.Android:
                if len(self.getDeviceIds()) == 0:
                    raise Exception('no devices found')
                if len(self.getPid(deviceId=deviceid, pkgName=pkgname)) == 0:
                    raise Exception('no process found')
            case Platform.iOS:
                if len(self.getDeviceInfoByiOS()) == 0:
                    raise Exception('no devices found')
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

    def getCurrentActivity(self, deviceId):
        result = adb.shell(cmd='dumpsys window | {} mCurrentFocus'.format(self.filterType()), deviceId=deviceId)
        if result.__contains__('mCurrentFocus'):
            activity = str(result).split(' ')[-1].replace('}','') 
            return activity
        else:
            raise Exception('no activity found')

    def getStartupTimeByAndroid(self, activity, deviceId):
        result = adb.shell(cmd='am start -W {}'.format(activity), deviceId=deviceId)
        return result

    def getStartupTimeByiOS(self, pkgname):
        try:
            import ios_device
        except ImportError:
            logger.error('py-ios-devices not found, please run [pip install py-ios-devices]') 
        result = self.execCmd('pyidevice instruments app_lifecycle -b {}'.format(pkgname))       
        return result          

class File:

    def __init__(self, fileroot='.'):
        self.fileroot = fileroot
        self.report_dir = self.get_repordir()

    def clear_file(self):
        logger.info('Clean up useless files ...')
        if os.path.exists(self.report_dir):
            for f in os.listdir(self.report_dir):
                filename = os.path.join(self.report_dir, f)
                if f.split(".")[-1] in ['log', 'json', 'mkv']:
                    os.remove(filename)
        Scrcpy.stop_record()            
        logger.info('Clean up useless files success')            

    def export_excel(self, platform, scene):
        logger.info('Exporting excel ...')
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
        xls_path = os.path.join(self.report_dir, scene, f'{scene}.xls')            
        wb.save(xls_path)
        logger.info('Exporting excel success : {}'.format(xls_path))
        return xls_path   
    
    def make_android_html(self, scene, summary : dict):
        logger.info('Generating HTML ...')
        STATICPATH = os.path.dirname(os.path.realpath(__file__))
        file_loader = FileSystemLoader(os.path.join(STATICPATH, 'report_template'))
        env = Environment(loader=file_loader)
        template = env.get_template('android.html')
        with open(os.path.join(self.report_dir, scene, 'report.html'),'w+') as fout:
            html_content = template.render(cpu_app=summary['cpu_app'],cpu_sys=summary['cpu_sys'],
                                           mem_total=summary['mem_total'],mem_native=summary['mem_native'],
                                           mem_dalvik=summary['mem_dalvik'],fps=summary['fps'],
                                           jank=summary['jank'],level=summary['level'],
                                           tem=summary['tem'],net_send=summary['net_send'],
                                           net_recv=summary['net_recv'],cpu_charts=summary['cpu_charts'],
                                           mem_charts=summary['mem_charts'],net_charts=summary['net_charts'],
                                           battery_charts=summary['battery_charts'],fps_charts=summary['fps_charts'],
                                           jank_charts=summary['jank_charts'])
            
            fout.write(html_content)
        html_path = os.path.join(self.report_dir, scene, 'report.html')    
        logger.info('Generating HTML success : {}'.format(html_path))  
        return html_path
    
    def make_ios_html(self, scene, summary : dict):
        logger.info('Generating HTML ...')
        STATICPATH = os.path.dirname(os.path.realpath(__file__))
        file_loader = FileSystemLoader(os.path.join(STATICPATH, 'report_template'))
        env = Environment(loader=file_loader)
        template = env.get_template('ios.html')
        with open(os.path.join(self.report_dir, scene, 'report.html'),'w+') as fout:
            html_content = template.render(cpu_app=summary['cpu_app'],cpu_sys=summary['cpu_sys'],gpu=summary['gpu'],
                                           mem_total=summary['mem_total'],fps=summary['fps'],
                                           tem=summary['tem'],current=summary['current'],
                                           voltage=summary['voltage'],power=summary['power'],
                                           net_send=summary['net_send'],net_recv=summary['net_recv'],
                                           cpu_charts=summary['cpu_charts'],mem_charts=summary['mem_charts'],
                                           net_charts=summary['net_charts'],battery_charts=summary['battery_charts'],
                                           fps_charts=summary['fps_charts'],gpu_charts=summary['gpu_charts'])            
            fout.write(html_content)
        html_path = os.path.join(self.report_dir, scene, 'report.html')    
        logger.info('Generating HTML success : {}'.format(html_path))  
        return html_path
  
    def filter_secen(self, scene):
        dirs = os.listdir(self.report_dir)
        dir_list = list(reversed(sorted(dirs, key=lambda x: os.path.getmtime(os.path.join(self.report_dir, x)))))
        dir_list.remove(scene)
        return dir_list

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
    
    def make_report(self, app, devices, video, platform=Platform.Android, model='normal'):
        logger.info('Generating test results ...')
        current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        result_dict = {
            "app": app,
            "icon": "",
            "platform": platform,
            "model": model,
            "devices": devices,
            "ctime": current_time,
            "video": video
        }
        content = json.dumps(result_dict)
        self.create_file(filename='result.json', content=content)
        report_new_dir = os.path.join(self.report_dir, f'apm_{current_time}')
        if not os.path.exists(report_new_dir):
            os.mkdir(report_new_dir)

        for f in os.listdir(self.report_dir):
            filename = os.path.join(self.report_dir, f)
            if f.split(".")[-1] in ['log', 'json', 'mkv']:
                shutil.move(filename, report_new_dir)        
        logger.info('Generating test results success: {}'.format(report_new_dir))
        return f'apm_{current_time}'        

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
    
    def getCpuLogCompare(self, platform, scene1, scene2):
        targetDic = {}
        targetDic['scene1'] = self.readLog(scene=scene1, filename='cpu_app.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='cpu_app.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        return result
    
    def getGpuLog(self, platform, scene):
        targetDic = {}
        targetDic['gpu'] = self.readLog(scene=scene, filename='gpu.log')[0]
        result = {'status': 1, 'gpu': targetDic['gpu']}
        return result
    
    def getGpuLogCompare(self, platform, scene1, scene2):
        targetDic = {}
        targetDic['scene1'] = self.readLog(scene=scene1, filename='gpu.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='gpu.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
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
    
    def getMemLogCompare(self, platform, scene1, scene2):
        targetDic = {}
        targetDic['scene1'] = self.readLog(scene=scene1, filename='mem_total.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='mem_total.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
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
    
    def getBatteryLogCompare(self, platform, scene1, scene2):
        targetDic = {}
        if platform == Platform.Android:
            targetDic['scene1'] = self.readLog(scene=scene1, filename='battery_level.log')[0]
            targetDic['scene2'] = self.readLog(scene=scene2, filename='battery_level.log')[0]
            result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        else:
            targetDic['scene1'] = self.readLog(scene=scene1, filename='batteryPower.log')[0]
            targetDic['scene2'] = self.readLog(scene=scene2, filename='batteryPower.log')[0]
            result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}    
        return result
    
    def getFlowLog(self, platform, scene):
        targetDic = {}
        targetDic['upFlow'] = self.readLog(scene=scene, filename='upflow.log')[0]
        targetDic['downFlow'] = self.readLog(scene=scene, filename='downflow.log')[0]
        result = {'status': 1, 'upFlow': targetDic['upFlow'], 'downFlow': targetDic['downFlow']}
        return result
    
    def getFlowSendLogCompare(self, platform, scene1, scene2):
        targetDic = {}
        targetDic['scene1'] = self.readLog(scene=scene1, filename='upflow.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='upflow.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        return result
    
    def getFlowRecvLogCompare(self, platform, scene1, scene2):
        targetDic = {}
        targetDic['scene1'] = self.readLog(scene=scene1, filename='downflow.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='downflow.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
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

    def getFpsLogCompare(self, platform, scene1, scene2):
        targetDic = {}
        targetDic['scene1'] = self.readLog(scene=scene1, filename='fps.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='fps.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
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
    
    @classmethod
    def _get_setting(cls, request):
        content = {}
        content['cpuWarning'] = (0, request.cookies.get('cpuWarning'))[request.cookies.get('cpuWarning') not in [None, 'NaN']]
        content['memWarning'] = (0, request.cookies.get('memWarning'))[request.cookies.get('memWarning') not in [None, 'NaN']]
        content['fpsWarning'] = (0, request.cookies.get('fpsWarning'))[request.cookies.get('fpsWarning') not in [None, 'NaN']]
        content['netdataRecvWarning'] = (0, request.cookies.get('netdataRecvWarning'))[request.cookies.get('netdataRecvWarning') not in [None, 'NaN']]
        content['netdataSendWarning'] = (0, request.cookies.get('netdataSendWarning'))[request.cookies.get('netdataSendWarning') not in [None, 'NaN']]
        content['betteryWarning'] = (0, request.cookies.get('betteryWarning'))[request.cookies.get('betteryWarning') not in [None, 'NaN']]
        content['duration'] = (0, request.cookies.get('duration'))[request.cookies.get('duration') not in [None, 'NaN']]
        content['solox_host'] = ('', request.cookies.get('solox_host'))[request.cookies.get('solox_host') not in [None, 'NaN']]
        content['host_switch'] = request.cookies.get('host_switch')
        return content

class Install:

    def uploadFile(self, file_path, file_obj):
        """save upload file"""
        try:
            file_obj.save(file_path)
            return True
        except Exception as e:
            logger.exception(e)
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
        except Exception as e:
            logger.exception(e)
            return False

    def installAPK(self, path):
        result = adb.shell_noDevice(cmd='install -r {}'.format(path))
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

class Scrcpy:

    STATICPATH = os.path.dirname(os.path.realpath(__file__))
    DEFAULT_SCRCPY_PATH = {
        "64": os.path.join(STATICPATH, "scrcpy", "scrcpy-win64-v2.1.1", "scrcpy.exe"),
        "32": os.path.join(STATICPATH, "scrcpy", "scrcpy-win32-v2.1.1", "scrcpy.exe"),
        "default":"scrcpy"
    }
    
    @classmethod
    def scrcpy_path(cls):
        bit = platform.architecture()[0]
        path = cls.DEFAULT_SCRCPY_PATH["default"]
        if platform.system().lower().__contains__('windows'):
            if bit.__contains__('64'):
                path =  cls.DEFAULT_SCRCPY_PATH["64"]
            elif bit.__contains__('32'):
                path =  cls.DEFAULT_SCRCPY_PATH["32"]
        return path
    
    @classmethod
    def start_record(cls, device):
        f = File()
        logger.info('start record screen')
        win_cmd = "start /b {scrcpy_path} -s {deviceId} --no-playback --record={video}".format(
            scrcpy_path = cls.scrcpy_path(), 
            deviceId = device, 
            video = os.path.join(f.report_dir, 'record.mkv')
        )
        mac_cmd = "nohup {scrcpy_path} -s {deviceId} --no-playback --record={video} &".format(
            scrcpy_path = cls.scrcpy_path(), 
            deviceId = device, 
            video = os.path.join(f.report_dir, 'record.mkv')
        )
        if platform.system().lower().__contains__('windows'):
            result = os.system(win_cmd)
        else:
            result = os.system(mac_cmd)    
        if result == 0:
            logger.info("record screen success : {}".format(os.path.join(f.report_dir, 'record.mkv')))
        else:
            logger.error("solox's scrcpy is incompatible with your PC")
            logger.info("Please install the software yourself : brew install scrcpy")    
        return result
    
    @classmethod
    def stop_record(cls):
        logger.info('stop scrcpy process')
        pids = psutil.pids()
        try:
            for pid in pids:
                p = psutil.Process(pid)
                if p.name().__contains__('scrcpy'):
                    os.kill(pid, signal.SIGABRT)
                    logger.info(pid)
        except Exception as e:
            logger.exception(e)
    
    @classmethod
    def cast_screen(cls, device):
        logger.info('start cast screen')
        win_cmd = "start /i {scrcpy_path} -s {deviceId} --stay-awake".format(
            scrcpy_path = cls.scrcpy_path(), 
            deviceId = device
        )
        mac_cmd = "nohup {scrcpy_path} -s {deviceId} --stay-awake &".format(
            scrcpy_path = cls.scrcpy_path(), 
            deviceId = device
        )
        if platform.system().lower().__contains__('windows'):
            result = os.system(win_cmd)
        else:
            result = os.system(mac_cmd)
        if result == 0:
            logger.info("cast screen success")
        else:
            logger.error("solox's scrcpy is incompatible with your PC")
            logger.info("Please install the software yourself : brew install scrcpy")    
        return result
    
    @classmethod
    def play_video(cls, video):
        logger.info('start play video : {}'.format(video))
        cap = cv2.VideoCapture(video)
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.namedWindow("frame", 0)  
                cv2.resizeWindow("frame", 430, 900)
                cv2.imshow('frame', gray)
                if cv2.waitKey(25) & 0xFF == ord('q') or not cv2.getWindowProperty("frame", cv2.WND_PROP_VISIBLE):
                    break
            else:
                break
        cap.release()
        cv2.destroyAllWindows()
