import json
import os
import platform
import re
import shutil
import time
import requests
from logzero import logger
from tqdm import tqdm
import socket
from urllib.request import urlopen
import ssl
import xlwt
import psutil
import signal
import jinja2
from functools import wraps
from jinja2 import Environment, FileSystemLoader
from tidevice._device import Device
from tidevice import Usbmux
from solox.public.adb import adb


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
        try:
            text = r.buffer.read().decode(encoding='gbk').replace('\x1b[0m','').strip()
        except UnicodeDecodeError:
            text = r.buffer.read().decode(encoding='utf-8').replace('\x1b[0m','').strip()
        finally:
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
            id, state = Ids[i].strip().split()
            if state == 'device':
                deviceIds.append(id)
        return deviceIds

    def getDevicesName(self, deviceId):
        """Get the device name of the Android corresponding device ID"""
        try:
            devices_name = os.popen(f'{self.adb} -s {deviceId} shell getprop ro.product.model').readlines()[0].strip()
        except Exception:
            devices_name = os.popen(f'{self.adb} -s {deviceId} shell getprop ro.product.model').buffer.readlines()[0].decode("utf-8").strip()
        return devices_name

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
            deviceId = deviceinfo
        return deviceId
    
    def getSdkVersion(self, deviceId):
        version = adb.shell(cmd='getprop ro.build.version.sdk', deviceId=deviceId)
        return version
    
    def getCpuCores(self, deviceId):
        """get Android cpu cores"""
        cmd = 'cat /sys/devices/system/cpu/online'
        result = adb.shell(cmd=cmd, deviceId=deviceId)
        try:
            nums = int(result.split('-')[1]) + 1
        except:
            nums = 1
        return nums

    def getPid(self, deviceId, pkgName):
        """Get the pid corresponding to the Android package name"""
        try:
            sdkversion = self.getSdkVersion(deviceId)
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

    def getPkgname(self, deviceId):
        """Get all package names of Android devices"""
        pkginfo = os.popen(f"{self.adb} -s {deviceId} shell pm list packages --user 0")
        pkglist = [p.lstrip('package').lstrip(":").strip() for p in pkginfo]
        if pkglist.__len__() > 0:
            return pkglist
        else:
            pkginfo = os.popen(f"{self.adb} -s {deviceId} shell pm list packages")
            pkglist = [p.lstrip('package').lstrip(":").strip() for p in pkginfo]
            return pkglist

    def getDeviceInfoByiOS(self):
        """Get a list of all successfully connected iOS devices"""
        deviceInfo = [udid for udid in Usbmux().device_udid_list()]
        logger.info('Connected devices: {}'.format(deviceInfo))    
        return deviceInfo

    def getPkgnameByiOS(self, udid):
        """Get all package names of the corresponding iOS device
        
        Args:
            udid: Device identifier
            
        Returns:
            list: List of package bundle identifiers installed on the device
            
        Raises:
            Exception: If device is not found or error occurs accessing device
        """
        try:
            d = Device(udid)
            if not d:
                logger.error(f"Could not connect to device {udid}")
                return []
                
            pkgNames = [
                i.get("CFBundleIdentifier") 
                for i in d.installation.iter_installed(app_type="User") 
                if i.get("CFBundleIdentifier")
            ]
            
            if not pkgNames:
                logger.warning(f"No user applications found on device {udid}")
                return []
                
            logger.debug(f"Found {len(pkgNames)} applications on device {udid}")
            return pkgNames
            
        except Exception as e:
            logger.exception(f"Error getting package names for device {udid}: {str(e)}")
            return []
    
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
        """Check the device environment
        
        Args:
            platform: Platform type (Android or iOS)
            deviceid: Device identifier (optional)
            pkgname: Package name to check (optional)
            
        Raises:
            Exception: If no devices found, device not found, or package not found
        """
        if platform == Platform.Android:
            if len(self.getDeviceIds()) == 0:
                raise Exception('no devices found')
            if deviceid and deviceid not in self.getDeviceIds():
                raise Exception('device not found')
            if pkgname and not self.checkPkgname(pkgname):
                raise Exception('package not found')
        elif platform == Platform.iOS:
            devices = self.getDeviceInfoByiOS()
            if len(devices) == 0:
                raise Exception('no devices found')
            if deviceid and deviceid not in devices:
                raise Exception('device not found')
            if pkgname:
                try:
                    d = Device(deviceid)
                    pkgNames = [i.get("CFBundleIdentifier") for i in d.installation.iter_installed(app_type="User")]
                    if pkgname not in pkgNames:
                        raise Exception('package not found')
                except Exception as e:
                    logger.error(f"Error checking iOS package: {str(e)}")
                    raise Exception('error checking package')
        else:
            logger.error(f"Unsupported platform: {platform}")
            raise ValueError(f"Unsupported platform: {platform}. Only Android and iOS are supported.")
            
    def getDdeviceDetail(self, deviceId, platform):
        """Get device details based on platform
        
        Args:
            deviceId: Device identifier
            platform: Platform type (Android or iOS)
            
        Returns:
            dict: Device details
            
        Raises:
            ValueError: If platform is unsupported
            Exception: If device is not found or error occurs
        """
        result = dict()
        try:
            if platform == Platform.Android:
                result['brand'] = adb.shell(cmd='getprop ro.product.brand', deviceId=deviceId)
                if not result['brand']:
                    raise Exception('Device not found or error accessing device')
                result['name'] = adb.shell(cmd='getprop ro.product.model', deviceId=deviceId)
                result['version'] = adb.shell(cmd='getprop ro.build.version.release', deviceId=deviceId)
                result['cpu'] = adb.shell(cmd='getprop ro.product.cpu.abi', deviceId=deviceId)
                result['manufacturer'] = adb.shell(cmd='getprop ro.product.manufacturer', deviceId=deviceId)
                result['battery'] = adb.shell(cmd='dumpsys battery', deviceId=deviceId)
            elif platform == Platform.iOS:
                try:
                    d = Device(deviceId)
                    device_info = d.device_info()  # Call it as a method
                    if not device_info:
                        raise Exception('Device not found or error accessing device')
                    result.update({
                        'name': device_info.get('DeviceName', 'Unknown'),
                        'version': device_info.get('ProductVersion', 'Unknown'),
                        'model': device_info.get('ProductType', 'Unknown'),
                        'brand': 'Apple',
                        'manufacturer': 'Apple'
                    })
                except Exception as e:
                    logger.error(f"Error accessing iOS device: {str(e)}")
                    raise Exception('Device not found or error accessing device')
            else:
                logger.error(f"Unsupported platform: {platform}")
                raise ValueError(f"Unsupported platform: {platform}. Only Android and iOS are supported.")
        except Exception as e:
            logger.error(f"Error getting device details: {str(e)}")
            raise
        return result
    
    def getPhysicalSizeOfiOS(self, deviceId):
        """Get the physical screen size of an iOS device
        
        Args:
            deviceId: Device identifier
            
        Returns:
            str: Screen size in format 'widthxheight', or empty string if error occurs
            
        Raises:
            Exception: If device is not found or error occurs accessing device
        """
        try:
            ios_device = Device(udid=deviceId)
            screen_info = ios_device.screen_info()
            if not screen_info:
                logger.error(f"Could not get screen info for device {deviceId}")
                return ''
                
            width = screen_info.get('width')
            height = screen_info.get('height')
            if width is None or height is None:
                logger.error(f"Invalid screen dimensions for device {deviceId}")
                return ''
                
            physical_size = f'{width}x{height}'
            logger.debug(f"Got screen size for device {deviceId}: {physical_size}")
            return physical_size
            
        except Exception as e:
            logger.exception(f"Error getting screen size for device {deviceId}: {str(e)}")
            return ''
    
    def getCurrentActivity(self, deviceId):
        result = adb.shell(cmd='dumpsys window | {} mCurrentFocus'.format(self.filterType()), deviceId=deviceId)
        if result.__contains__('mCurrentFocus'):
            activity = str(result).split(' ')[-1].replace('}','') 
            return activity
        else:
            raise Exception('No activity found')

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
        """Clean up temporary files and stop screen recording
        
        This method removes log, json, and mkv files from the report directory
        and stops any active screen recording sessions.
        
        Raises:
            OSError: If file deletion operations fail
        """
        try:
            logger.info('Cleaning up temporary files...')
            if os.path.exists(self.report_dir):
                for f in os.listdir(self.report_dir):
                    filename = os.path.join(self.report_dir, f)
                    if os.path.isfile(filename) and f.split(".")[-1] in ['log', 'json', 'mkv']:
                        try:
                            os.remove(filename)
                            logger.debug(f"Removed file: {filename}")
                        except OSError as e:
                            logger.warning(f"Failed to remove file {filename}: {str(e)}")
                            
            Scrcpy.stop_record()
            logger.info('Cleanup completed successfully')
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            logger.exception(e)
            raise

    def export_excel(self, platform, scene):
        """Export performance data to Excel format
        
        Args:
            platform (str): Target platform (Android or iOS)
            scene (str): Test scene name
            
        Returns:
            str: Path to the generated Excel file
            
        Raises:
            ValueError: If platform or scene parameters are invalid
            OSError: If file operations fail
        """
        if not platform or platform not in [Platform.Android, Platform.iOS]:
            raise ValueError(f"Invalid platform: {platform}. Must be Android or iOS")
        if not scene or not isinstance(scene, str):
            raise ValueError("Scene parameter must be a non-empty string")
            
        try:
            logger.info('Exporting performance data to Excel...')
            
            # Define log file lists based on platform
            android_log_files = ['cpu_app', 'cpu_sys', 'mem_total', 'mem_swap',
                               'battery_level', 'battery_tem', 'upflow', 'downflow', 'fps', 'gpu']
            ios_log_files = ['cpu_app', 'cpu_sys', 'mem_total', 'battery_tem', 'battery_current',
                            'battery_voltage', 'battery_power', 'upflow', 'downflow', 'fps', 'gpu']
            log_files = android_log_files if platform == Platform.Android else ios_log_files
            
            # Create workbook and format headers
            wb = xlwt.Workbook(encoding='utf-8')
            row_count = 1
            
            # Process each log file
            for name in log_files:
                ws = wb.add_sheet(name)
                ws.write(0, 0, 'Time')
                ws.write(0, 1, 'Value')
                row = 1
                col = 0
                
                log_path = os.path.join(self.report_dir, scene, f'{name}.log')
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                target = line.strip().split('=')
                                if len(target) == 2:  # Validate line format
                                    for i, value in enumerate(target):
                                        ws.write(row, col + i, value)
                                    row += 1
                                    row_count += 1
                                else:
                                    logger.warning(f"Skipping invalid line in {name}.log: {line}")
                    except Exception as e:
                        logger.error(f"Error processing {name}.log: {str(e)}")
                        continue
                
            # Save workbook
            xls_path = os.path.join(self.report_dir, scene, f'{scene}.xls')
            os.makedirs(os.path.dirname(xls_path), exist_ok=True)
            wb.save(xls_path)
            
            logger.info(f'Excel export completed successfully: {xls_path}')
            return xls_path
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            logger.exception(e)
            raise

    def make_android_html(self, scene, summary: dict, report_path=None):
        """Generate HTML report for Android performance data
        
        Args:
            scene: Test scene name
            summary: Dictionary containing performance data
            report_path: Optional custom path for the report
            
        Returns:
            str: Path to the generated HTML report
            
        Raises:
            ValueError: If required data is missing in summary
            OSError: If there are file operation errors
        """
        logger.info('Generating HTML report...')
        
        # Validate required fields
        required_fields = ['devices', 'app', 'platform', 'ctime', 'cpu_app', 'cpu_sys', 
                         'mem_total', 'mem_swap', 'fps', 'jank', 'level', 'tem',
                         'net_send', 'net_recv', 'cpu_charts', 'mem_charts', 'net_charts',
                         'battery_charts', 'fps_charts', 'jank_charts', 'mem_detail_charts',
                         'gpu', 'gpu_charts']
        
        missing_fields = [field for field in required_fields if field not in summary]
        if missing_fields:
            raise ValueError(f"Missing required fields in summary: {', '.join(missing_fields)}")
            
        try:
            STATICPATH = os.path.dirname(os.path.realpath(__file__))
            file_loader = FileSystemLoader(os.path.join(STATICPATH, 'report_template'))
            env = Environment(loader=file_loader)
            template = env.get_template('android.html')
            
            if report_path:
                html_path = report_path
            else:
                html_path = os.path.join(self.report_dir, scene, 'report.html')
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(html_path), exist_ok=True)
            
            with open(html_path, 'w+', encoding='utf-8') as fout:
                html_content = template.render(
                    devices=summary['devices'],
                    app=summary['app'],
                    platform=summary['platform'],
                    ctime=summary['ctime'],
                    cpu_app=summary['cpu_app'],
                    cpu_sys=summary['cpu_sys'],
                    mem_total=summary['mem_total'],
                    mem_swap=summary['mem_swap'],
                    fps=summary['fps'],
                    jank=summary['jank'],
                    level=summary['level'],
                    tem=summary['tem'],
                    net_send=summary['net_send'],
                    net_recv=summary['net_recv'],
                    cpu_charts=summary['cpu_charts'],
                    mem_charts=summary['mem_charts'],
                    net_charts=summary['net_charts'],
                    battery_charts=summary['battery_charts'],
                    fps_charts=summary['fps_charts'],
                    jank_charts=summary['jank_charts'],
                    mem_detail_charts=summary['mem_detail_charts'],
                    gpu=summary['gpu'],
                    gpu_charts=summary['gpu_charts']
                )
                fout.write(html_content)
                
            logger.info(f'HTML report generated successfully: {html_path}')
            return html_path
            
        except jinja2.TemplateError as e:
            logger.error(f"Template error while generating HTML: {str(e)}")
            raise
        except OSError as e:
            logger.error(f"File operation error while generating HTML: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while generating HTML: {str(e)}")
            logger.exception(e)
            raise
  
    def make_ios_html(self, scene, summary: dict, report_path=None):
        """Generate HTML report for iOS performance data
        
        Args:
            scene: Test scene name
            summary: Dictionary containing performance data
            report_path: Optional custom path for the report
            
        Returns:
            str: Path to the generated HTML report
            
        Raises:
            ValueError: If required data is missing in summary
            OSError: If there are file operation errors
        """
        logger.info('Generating HTML report...')
        
        # Validate required fields
        required_fields = ['devices', 'app', 'platform', 'ctime', 'cpu_app', 'cpu_sys', 
                         'gpu', 'mem_total', 'fps', 'tem', 'current', 'voltage', 'power',
                         'net_send', 'net_recv', 'cpu_charts', 'mem_charts', 'net_charts',
                         'battery_charts', 'fps_charts', 'gpu_charts']
        
        missing_fields = [field for field in required_fields if field not in summary]
        if missing_fields:
            raise ValueError(f"Missing required fields in summary: {', '.join(missing_fields)}")
            
        try:
            STATICPATH = os.path.dirname(os.path.realpath(__file__))
            file_loader = FileSystemLoader(os.path.join(STATICPATH, 'report_template'))
            env = Environment(loader=file_loader)
            template = env.get_template('ios.html')
            
            if report_path:
                html_path = report_path
            else:
                html_path = os.path.join(self.report_dir, scene, 'report.html')
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(html_path), exist_ok=True)
            
            with open(html_path, 'w+', encoding='utf-8') as fout:
                html_content = template.render(
                    devices=summary['devices'],
                    app=summary['app'],
                    platform=summary['platform'],
                    ctime=summary['ctime'],
                    cpu_app=summary['cpu_app'],
                    cpu_sys=summary['cpu_sys'],
                    gpu=summary['gpu'],
                    mem_total=summary['mem_total'],
                    fps=summary['fps'],
                    tem=summary['tem'],
                    current=summary['current'],
                    voltage=summary['voltage'],
                    power=summary['power'],
                    net_send=summary['net_send'],
                    net_recv=summary['net_recv'],
                    cpu_charts=summary['cpu_charts'],
                    mem_charts=summary['mem_charts'],
                    net_charts=summary['net_charts'],
                    battery_charts=summary['battery_charts'],
                    fps_charts=summary['fps_charts'],
                    gpu_charts=summary['gpu_charts']
                )
                fout.write(html_content)
                
            logger.info(f'HTML report generated successfully: {html_path}')
            return html_path
            
        except jinja2.TemplateError as e:
            logger.error(f"Template error while generating HTML: {str(e)}")
            raise
        except OSError as e:
            logger.error(f"File operation error while generating HTML: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while generating HTML: {str(e)}")
            logger.exception(e)
            raise
  
    def filter_secen(self, scene):
        """Filter out the current scene from the list of report directories"""
        try:
            dirs = os.listdir(self.report_dir)
            dir_list = list(reversed(sorted(dirs, key=lambda x: os.path.getmtime(os.path.join(self.report_dir, x)))))
            if scene in dir_list:
                dir_list.remove(scene)
            return dir_list
        except OSError as e:
            logger.error(f"Error accessing report directory: {str(e)}")
            return []

    def get_repordir(self):
        """Get or create the report directory"""
        report_dir = os.path.join(os.getcwd(), 'report')
        try:
            os.makedirs(report_dir, exist_ok=True)
            return report_dir
        except OSError as e:
            logger.error(f"Error creating report directory: {str(e)}")
            raise

    def create_file(self, filename, content=''):
        """Create a new file in the report directory with optional content"""
        try:
            os.makedirs(self.report_dir, exist_ok=True)
            file_path = os.path.join(self.report_dir, filename)
            with open(file_path, 'a+', encoding="utf-8") as file:
                file.write(content)
        except OSError as e:
            logger.error(f"Error creating file {filename}: {str(e)}")
            raise

    def add_log(self, path, log_time, value):
        """Add a timestamped log entry if the value is valid"""
        if value >= 0:
            try:
                with open(path, 'a+', encoding="utf-8") as file:
                    file.write(f'{log_time}={str(value)}\n')
            except OSError as e:
                logger.error(f"Error writing to log file {path}: {str(e)}")
    
    def record_net(self, type, send, recv):
        """Record or compute network traffic deltas.

        Types:
        - 'pre': snapshot current counters to pre_net.json
        - 'end': snapshot current counters to end_net.json
        - 'next': return delta from previously stored pre_net.json (no file write)
        """
        net_dict = dict()
        report_root = os.path.join(os.getcwd(), 'report')
        os.makedirs(report_root, exist_ok=True)
        pre_path = os.path.join(report_root, 'pre_net.json')
        end_path = os.path.join(report_root, 'end_net.json')

        if type == 'pre':
            net_dict = {'send': send, 'recv': recv}
            with open(pre_path, 'w') as f:
                json.dump(net_dict, f)
        elif type == 'end':
            net_dict = {'send': send, 'recv': recv}
            with open(end_path, 'w') as f:
                json.dump(net_dict, f)
        elif type == 'next':
            if not os.path.exists(pre_path):
                logger.warning('pre_net.json not found; returning zeros for next delta')
                net_dict = {'send': 0, 'recv': 0}
            else:
                with open(pre_path, 'r') as f:
                    pre_net = json.load(f)
                net_dict['send'] = send - pre_net.get('send', 0)
                net_dict['recv'] = recv - pre_net.get('recv', 0)
        else:
            logger.error(f"Unsupported network record type: {type}")
            raise ValueError("Unsupported network record type: {}. Only 'pre', 'end', and 'next' are supported.".format(type))
        return net_dict
    
    def make_report(self, app, devices, video, platform=Platform.Android, model='normal', cores=0):
        """Generate a test report with performance data and metadata
        
        Args:
            app (str): Application name or identifier
            devices (str): Device information
            video (str): Path to recorded video file
            platform (Platform): Target platform (Android or iOS)
            model (str): Test model type, defaults to 'normal'
            cores (int): Number of CPU cores, defaults to 0
            
        Returns:
            str: Name of the report directory (format: apm_YYYY-MM-DD-HH-MM-SS)
            
        Raises:
            ValueError: If required parameters are invalid
            OSError: If directory creation or file operations fail
        """
        if not app or not isinstance(app, str):
            raise ValueError("App parameter must be a non-empty string")
        if not devices or not isinstance(devices, str):
            raise ValueError("Devices parameter must be a non-empty string")
        if not isinstance(platform, str) or platform not in [Platform.Android, Platform.iOS]:
            raise ValueError(f"Invalid platform: {platform}. Must be Android or iOS")
            
        try:
            logger.info('Generating performance test report...')
            current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
            report_dir_name = f'apm_{current_time}'
            
            # Prepare result dictionary
            result_dict = {
                "app": app,
                "icon": "",
                "platform": platform,
                "model": model,
                "devices": devices,
                "ctime": current_time,
                "video": video,
                "cores": cores
            }
            
            # Create result.json
            try:
                content = json.dumps(result_dict)
                self.create_file(filename='result.json', content=content)
            except Exception as e:
                logger.error(f"Failed to create result.json: {str(e)}")
                raise
            
            # Create and setup report directory
            report_new_dir = os.path.join(self.report_dir, report_dir_name)
            try:
                os.makedirs(report_new_dir, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create report directory: {str(e)}")
                raise
            
            # Move relevant files to report directory
            moved_files = []
            for f in os.listdir(self.report_dir):
                filename = os.path.join(self.report_dir, f)
                if os.path.isfile(filename) and f.split(".")[-1] in ['log', 'json', 'mkv']:
                    try:
                        shutil.move(filename, report_new_dir)
                        moved_files.append(f)
                    except OSError as e:
                        logger.warning(f"Failed to move file {f}: {str(e)}")
            
            logger.info(f'Report generated successfully: {report_new_dir}')
            logger.debug(f'Moved {len(moved_files)} files to report directory')
            return report_dir_name
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            logger.exception(e)
            raise

    def instance_type(self, data):
        if isinstance(data, float):
            return 'float'
        elif isinstance(data, int):
            return 'int'
        else:
            return 'int'
    
    def open_file(self, path, mode):
        """Generator to read file lines efficiently"""
        try:
            with open(path, mode) as f:
                for line in f:
                    yield line
        except OSError as e:
            logger.error(f"Error reading file {path}: {str(e)}")
            return
    
    def readJson(self, scene):
        """Read and parse the result.json file for a given scene"""
        path = os.path.join(self.report_dir, scene, 'result.json')
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Result file not found for scene {scene}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in result file for scene {scene}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error reading result file for scene {scene}: {str(e)}")
            return {}

    def readLog(self, scene, filename):
        """Read apmlog file data"""
        log_data_list = list()
        target_data_list = list()
        if os.path.exists(os.path.join(self.report_dir,scene,filename)):
            lines = self.open_file(os.path.join(self.report_dir,scene,filename), "r")
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
        targetDic = dict()
        targetDic['cpuAppData'] = self.readLog(scene=scene, filename='cpu_app.log')[0]
        targetDic['cpuSysData'] = self.readLog(scene=scene, filename='cpu_sys.log')[0]
        result = {'status': 1, 'cpuAppData': targetDic['cpuAppData'], 'cpuSysData': targetDic['cpuSysData']}
        return result
    
    def getCpuLogCompare(self, platform, scene1, scene2):
        targetDic = dict()
        targetDic['scene1'] = self.readLog(scene=scene1, filename='cpu_app.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='cpu_app.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        return result
    
    def getGpuLog(self, platform, scene):
        targetDic = dict()
        targetDic['gpu'] = self.readLog(scene=scene, filename='gpu.log')[0]
        result = {'status': 1, 'gpu': targetDic['gpu']}
        return result
    
    def getGpuLogCompare(self, platform, scene1, scene2):
        targetDic = dict()
        targetDic['scene1'] = self.readLog(scene=scene1, filename='gpu.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='gpu.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        return result
    
    def getMemLog(self, platform, scene):
        targetDic = dict()
        targetDic['memTotalData'] = self.readLog(scene=scene, filename='mem_total.log')[0]
        if platform == Platform.Android:
            targetDic['memSwapData']  = self.readLog(scene=scene, filename='mem_swap.log')[0]
            result = {'status': 1, 
                      'memTotalData': targetDic['memTotalData'], 
                      'memSwapData': targetDic['memSwapData']}
        else:
            result = {'status': 1, 'memTotalData': targetDic['memTotalData']}
        return result
    
    def getMemDetailLog(self, platform, scene):
        targetDic = dict()
        targetDic['java_heap'] = self.readLog(scene=scene, filename='mem_java_heap.log')[0]
        targetDic['native_heap'] = self.readLog(scene=scene, filename='mem_native_heap.log')[0]
        targetDic['code_pss'] = self.readLog(scene=scene, filename='mem_code_pss.log')[0]
        targetDic['stack_pss'] = self.readLog(scene=scene, filename='mem_stack_pss.log')[0]
        targetDic['graphics_pss'] = self.readLog(scene=scene, filename='mem_graphics_pss.log')[0]
        targetDic['private_pss'] = self.readLog(scene=scene, filename='mem_private_pss.log')[0]
        targetDic['system_pss'] = self.readLog(scene=scene, filename='mem_system_pss.log')[0]
        result = {'status': 1, 'memory_detail': targetDic}
        return result
    
    def getCpuCoreLog(self, platform, scene):
        targetDic = dict()
        cores =self.readJson(scene=scene).get('cores', 0)
        if int(cores) > 0:
            for i in range(int(cores)):
                targetDic['cpu{}'.format(i)] = self.readLog(scene=scene, filename='cpu{}.log'.format(i))[0]
        result = {'status': 1, 'cores':cores, 'cpu_core': targetDic}
        return result
    
    def getMemLogCompare(self, platform, scene1, scene2):
        targetDic = dict()
        targetDic['scene1'] = self.readLog(scene=scene1, filename='mem_total.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='mem_total.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        return result
    
    def getBatteryLog(self, platform, scene):
        targetDic = dict()
        if platform == Platform.Android:
            targetDic['batteryLevel'] = self.readLog(scene=scene, filename='battery_level.log')[0]
            targetDic['batteryTem'] = self.readLog(scene=scene, filename='battery_tem.log')[0]
            result = {'status': 1, 'batteryLevel': targetDic['batteryLevel'], 'batteryTem': targetDic['batteryTem']}
        else:
            targetDic['batteryTem'] = self.readLog(scene=scene, filename='battery_tem.log')[0]
            targetDic['batteryCurrent'] = self.readLog(scene=scene, filename='battery_current.log')[0]
            targetDic['batteryVoltage'] = self.readLog(scene=scene, filename='battery_voltage.log')[0]
            targetDic['batteryPower'] = self.readLog(scene=scene, filename='battery_power.log')[0]
            result = {'status': 1, 'batteryTem': targetDic['batteryTem'], 'batteryCurrent': targetDic['batteryCurrent'], 'batteryVoltage': targetDic['batteryVoltage'], 'batteryPower': targetDic['batteryPower']}
        return result

    def getBatteryLogCompare(self, platform, scene1, scene2):
        targetDic = dict()
        if platform == Platform.Android:
            targetDic['scene1'] = self.readLog(scene=scene1, filename='battery_level.log')[0]
            targetDic['scene2'] = self.readLog(scene=scene2, filename='battery_level.log')[0]
            result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        else:
            targetDic['scene1'] = self.readLog(scene=scene1, filename='battery_power.log')[0]
            targetDic['scene2'] = self.readLog(scene=scene2, filename='battery_power.log')[0]
            result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}    
        return result
    
    def getFlowLog(self, platform, scene):
        targetDic = dict()
        targetDic['upFlow'] = self.readLog(scene=scene, filename='upflow.log')[0]
        targetDic['downFlow'] = self.readLog(scene=scene, filename='downflow.log')[0]
        result = {'status': 1, 'upFlow': targetDic['upFlow'], 'downFlow': targetDic['downFlow']}
        return result
    
    def getFlowSendLogCompare(self, platform, scene1, scene2):
        targetDic = dict()
        targetDic['scene1'] = self.readLog(scene=scene1, filename='upflow.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='upflow.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        return result
    
    def getFlowRecvLogCompare(self, platform, scene1, scene2):
        targetDic = dict()
        targetDic['scene1'] = self.readLog(scene=scene1, filename='downflow.log')[0]
        targetDic['scene2'] = self.readLog(scene=scene2, filename='downflow.log')[0]
        result = {'status': 1, 'scene1': targetDic['scene1'], 'scene2': targetDic['scene2']}
        return result
    
    def getFpsLog(self, platform, scene):
        targetDic = dict()
        targetDic['fps'] = self.readLog(scene=scene, filename='fps.log')[0]
        if platform == Platform.Android:
            targetDic['jank'] = self.readLog(scene=scene, filename='jank.log')[0]
            result = {'status': 1, 'fps': targetDic['fps'], 'jank': targetDic['jank']}
        else:
            result = {'status': 1, 'fps': targetDic['fps']}     
        return result
    
    def getDiskLog(self, platform, scene):
        targetDic = dict()
        targetDic['used'] = self.readLog(scene=scene, filename='disk_used.log')[0]
        targetDic['free'] = self.readLog(scene=scene, filename='disk_free.log')[0]
        result = {'status': 1, 'used': targetDic['used'], 'free':targetDic['free']}
        return result

    def analysisDisk(self, scene):
        initail_disk_list = list()
        current_disk_list = list()
        sum_init_disk = dict()
        sum_current_disk = dict()
        if os.path.exists(os.path.join(self.report_dir,scene,'initail_disk.log')):
            size_list = list()
            used_list = list()
            free_list = list()
            lines = self.open_file(os.path.join(self.report_dir,scene,'initail_disk.log'), "r")
            for line in lines:
                if 'Filesystem' not in line and line.strip() != '':
                    disk_value_list = line.split()
                    disk_dict = dict(
                        filesystem = disk_value_list[0],
                        blocks = disk_value_list[1],
                        used = disk_value_list[2],
                        available = disk_value_list[3],
                        use_percent = disk_value_list[4],
                        mounted = disk_value_list[5]
                    )
                    initail_disk_list.append(disk_dict)
                    size_list.append(int(disk_value_list[1]))
                    used_list.append(int(disk_value_list[2]))
                    free_list.append(int(disk_value_list[3]))
            sum_init_disk['sum_size'] = int(sum(size_list) / 1024 / 1024)
            sum_init_disk['sum_used'] = int(sum(used_list) / 1024)
            sum_init_disk['sum_free'] = int(sum(free_list) / 1024)
               
        if os.path.exists(os.path.join(self.report_dir,scene,'current_disk.log')):
            size_list = list()
            used_list = list()
            free_list = list()
            lines = self.open_file(os.path.join(self.report_dir,scene,'current_disk.log'), "r")
            for line in lines:
                if 'Filesystem' not in line and line.strip() != '':
                    disk_value_list = line.split()
                    disk_dict = dict(
                        filesystem = disk_value_list[0],
                        blocks = disk_value_list[1],
                        used = disk_value_list[2],
                        available = disk_value_list[3],
                        use_percent = disk_value_list[4],
                        mounted = disk_value_list[5]
                    )
                    current_disk_list.append(disk_dict)
                    size_list.append(int(disk_value_list[1]))
                    used_list.append(int(disk_value_list[2]))
                    free_list.append(int(disk_value_list[3]))
            sum_current_disk['sum_size'] = int(sum(size_list) / 1024 / 1024)
            sum_current_disk['sum_used'] = int(sum(used_list) / 1024)
            sum_current_disk['sum_free'] = int(sum(free_list) / 1024)       
                 
        return initail_disk_list, current_disk_list, sum_init_disk, sum_current_disk

    def getFpsLogCompare(self, platform, scene1, scene2):
        targetDic = dict()
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
        
        app = self.readJson(scene=scene).get('app')
        devices = self.readJson(scene=scene).get('devices')
        platform = self.readJson(scene=scene).get('platform')
        ctime = self.readJson(scene=scene).get('ctime')

        cpuAppData = self.readLog(scene=scene, filename=f'cpu_app.log')[1]
        cpuSystemData = self.readLog(scene=scene, filename=f'cpu_sys.log')[1]
        if cpuAppData.__len__() > 0 and cpuSystemData.__len__() > 0:
            cpuAppRate = f'{round(sum(cpuAppData) / len(cpuAppData), 2)}%'
            cpuSystemRate = f'{round(sum(cpuSystemData) / len(cpuSystemData), 2)}%'
        else:
            cpuAppRate, cpuSystemRate = 0, 0    

        batteryLevelData = self.readLog(scene=scene, filename=f'battery_level.log')[1]
        batteryTemlData = self.readLog(scene=scene, filename=f'battery_tem.log')[1]
        if batteryLevelData.__len__() > 0 and batteryTemlData.__len__() > 0:
            batteryLevel = f'{batteryLevelData[-1]}%'
            batteryTeml = f'{batteryTemlData[-1]}°C'
        else:
            batteryLevel, batteryTeml = 0, 0   
    

        totalPassData = self.readLog(scene=scene, filename=f'mem_total.log')[1]
        
        if totalPassData.__len__() > 0:
            swapPassData = self.readLog(scene=scene, filename=f'mem_swap.log')[1]
            totalPassAvg = f'{round(sum(totalPassData) / len(totalPassData), 2)}MB'
            swapPassAvg = f'{round(sum(swapPassData) / len(swapPassData), 2)}MB'
        else:
            totalPassAvg, swapPassAvg = 0, 0    

        fpsData = self.readLog(scene=scene, filename=f'fps.log')[1]
        jankData = self.readLog(scene=scene, filename=f'jank.log')[1]
        if fpsData.__len__() > 0:
            fpsAvg = f'{int(sum(fpsData) / len(fpsData))}HZ/s'
            jankAvg = f'{int(sum(jankData))}'
        else:
            fpsAvg, jankAvg = 0, 0    

        if os.path.exists(os.path.join(self.report_dir,scene,'end_net.json')):
            f_pre = open(os.path.join(self.report_dir,scene,'pre_net.json'))
            f_end = open(os.path.join(self.report_dir,scene,'end_net.json'))
            json_pre = json.loads(f_pre.read())
            json_end = json.loads(f_end.read())
            send = json_end['send'] - json_pre['send']
            recv = json_end['recv'] - json_pre['recv']
        else:
            send, recv = 0, 0    
        flowSend = f'{round(float(send / 1024), 2)}MB'
        flowRecv = f'{round(float(recv / 1024), 2)}MB'

        gpuData = self.readLog(scene=scene, filename='gpu.log')[1]
        if gpuData.__len__() > 0:
            gpu = round(sum(gpuData) / len(gpuData), 2)
        else:
            gpu = 0

        mem_detail_flag = os.path.exists(os.path.join(self.report_dir,scene,'mem_java_heap.log'))
        disk_flag = os.path.exists(os.path.join(self.report_dir,scene,'disk_free.log'))
        thermal_flag = os.path.exists(os.path.join(self.report_dir,scene,'init_thermal_temp.json'))
        cpu_core_flag = os.path.exists(os.path.join(self.report_dir,scene,'cpu0.log'))
        apm_dict = dict()
        apm_dict['app'] = app
        apm_dict['devices'] = devices
        apm_dict['platform'] = platform
        apm_dict['ctime'] = ctime
        apm_dict['cpuAppRate'] = cpuAppRate
        apm_dict['cpuSystemRate'] = cpuSystemRate
        apm_dict['totalPassAvg'] = totalPassAvg
        apm_dict['swapPassAvg'] = swapPassAvg
        apm_dict['fps'] = fpsAvg
        apm_dict['jank'] = jankAvg
        apm_dict['flow_send'] = flowSend
        apm_dict['flow_recv'] = flowRecv
        apm_dict['batteryLevel'] = batteryLevel
        apm_dict['batteryTeml'] = batteryTeml
        apm_dict['mem_detail_flag'] = mem_detail_flag
        apm_dict['disk_flag'] = disk_flag
        apm_dict['gpu'] = gpu
        apm_dict['thermal_flag'] = thermal_flag
        apm_dict['cpu_core_flag'] = cpu_core_flag
        
        if thermal_flag:
            init_thermal_temp = json.loads(open(os.path.join(self.report_dir,scene,'init_thermal_temp.json')).read())
            current_thermal_temp = json.loads(open(os.path.join(self.report_dir,scene,'current_thermal_temp.json')).read())
            apm_dict['init_thermal_temp'] = init_thermal_temp
            apm_dict['current_thermal_temp'] = current_thermal_temp

        return apm_dict

    def _setiOSPerfs(self, scene):
        """Aggregate APM data for iOS"""
        
        app = self.readJson(scene=scene).get('app')
        devices = self.readJson(scene=scene).get('devices')
        platform = self.readJson(scene=scene).get('platform')
        ctime = self.readJson(scene=scene).get('ctime')

        cpuAppData = self.readLog(scene=scene, filename=f'cpu_app.log')[1]
        cpuSystemData = self.readLog(scene=scene, filename=f'cpu_sys.log')[1]
        if cpuAppData.__len__() > 0 and cpuSystemData.__len__() > 0:
            cpuAppRate = f'{round(sum(cpuAppData) / len(cpuAppData), 2)}%'
            cpuSystemRate = f'{round(sum(cpuSystemData) / len(cpuSystemData), 2)}%'
        else:
            cpuAppRate, cpuSystemRate = 0, 0

        totalPassData = self.readLog(scene=scene, filename='mem_total.log')[1]
        if totalPassData.__len__() > 0:
            totalPassAvg = f'{round(sum(totalPassData) / len(totalPassData), 2)}MB'
        else:
            totalPassAvg = 0

        fpsData = self.readLog(scene=scene, filename='fps.log')[1]
        if fpsData.__len__() > 0:
            fpsAvg = f'{int(sum(fpsData) / len(fpsData))}HZ/s'
        else:
            fpsAvg = 0

        flowSendData = self.readLog(scene=scene, filename='upflow.log')[1]
        flowRecvData = self.readLog(scene=scene, filename='downflow.log')[1]
        if flowSendData.__len__() > 0:
            flowSend = f'{round(float(sum(flowSendData) / 1024), 2)}MB'
            flowRecv = f'{round(float(sum(flowRecvData) / 1024), 2)}MB'
        else:
            flowSend, flowRecv = 0, 0    

        batteryTemlData = self.readLog(scene=scene, filename='battery_tem.log')[1]
        batteryCurrentData = self.readLog(scene=scene, filename='battery_current.log')[1]
        batteryVoltageData = self.readLog(scene=scene, filename='battery_voltage.log')[1]
        batteryPowerData = self.readLog(scene=scene, filename='battery_power.log')[1]
        if batteryTemlData.__len__() > 0:
            batteryTeml = int(batteryTemlData[-1])
            batteryCurrent = int(sum(batteryCurrentData) / len(batteryCurrentData))
            batteryVoltage = int(sum(batteryVoltageData) / len(batteryVoltageData))
            batteryPower = int(sum(batteryPowerData) / len(batteryPowerData))
        else:
            batteryTeml,  batteryCurrent , batteryVoltage, batteryPower = 0, 0, 0, 0 

        gpuData = self.readLog(scene=scene, filename='gpu.log')[1]
        if gpuData.__len__() > 0:
            gpu = round(sum(gpuData) / len(gpuData), 2)
        else:
            gpu = 0    
        disk_flag = os.path.exists(os.path.join(self.report_dir,scene,'disk_free.log'))
        apm_dict = dict()
        apm_dict['app'] = app
        apm_dict['devices'] = devices
        apm_dict['platform'] = platform
        apm_dict['ctime'] = ctime
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
        apm_dict['disk_flag'] = disk_flag
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
        
        apm_dict = dict()
        apm_dict['cpuAppRate1'] = cpuAppRate1
        apm_dict['cpuAppRate2'] = cpuAppRate2
        apm_dict['totalPassAvg1'] = totalPassAvg1
        apm_dict['totalPassAvg2'] = totalPassAvg2
        apm_dict['network1'] = network1
        apm_dict['network2'] = network2
        apm_dict['fpsAvg1'] = fpsAvg1
        apm_dict['fpsAvg2'] = fpsAvg2
        return apm_dict


# Minimal utility classes expected by other modules/tests
class Method:
    @staticmethod
    def _request(request):
        """Return a dict of parameters for GET/POST requests."""
        try:
            if request.method == 'POST':
                return request.get_json(silent=True) or request.form.to_dict() or {}
            if request.method == 'GET':
                return request.args.to_dict() or {}
            raise ValueError('Unsupported request method')
        except Exception as e:
            logger.exception(e)
            return {}

    @staticmethod
    def _settings(request):
        """Return minimal settings used by templates/pages."""
        host = '127.0.0.1'
        port = '5000'
        try:
            if hasattr(request, 'host') and request.host:
                parts = str(request.host).split(':')
                host = parts[0] or host
                if len(parts) > 1 and parts[1]:
                    port = parts[1]
        except Exception:
            pass
        return {'host': host, 'port': port}


class Install:
    @staticmethod
    def uploadFile(dst_dir, fs):
        os.makedirs(dst_dir, exist_ok=True)
        filename = getattr(fs, 'filename', None) or 'upload.bin'
        path = os.path.join(dst_dir, filename)
        fs.save(path)
        return path

    @staticmethod
    def downloadLink(url, dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
        local = os.path.join(dst_dir, os.path.basename(url) or 'download.bin')
        with urlopen(url) as r, open(local, 'wb') as f:
            f.write(r.read())
        return local

    @staticmethod
    def installAPK(deviceId, apk_path):
        return adb.tcp_shell(deviceId=deviceId, cmd=f'install -r "{apk_path}"')

    @staticmethod
    def installIPA(udid, ipa_path):
        try:
            d = Device(udid)
            d.install(ipa_path)
            return True
        except Exception as e:
            logger.error(f'iOS install failed: {e}')
            return False


class Scrcpy:
    _recording = False

    @staticmethod
    def start_record(deviceId, filename='record.mkv'):
        Scrcpy._recording = True
        return 0

    @staticmethod
    def stop_record():
        Scrcpy._recording = False
        return True

    @staticmethod
    def cast_screen(deviceId):
        return 0

    @staticmethod
    def play_video(path):
        if not os.path.exists(path):
            return 1
        try:
            sys = platform.system()
            if sys == 'Darwin':
                os.system(f'open "{path}"')
            elif sys == 'Windows':
                os.system(f'start "" "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
            return 0
        except Exception:
            return 1
