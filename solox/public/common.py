from . import *

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
        if platform.system() != 'Windows':
            result = os.popen(f"adb -s {deviceId} shell ps | grep {pkgName}").readlines()
        else:
            result = os.popen(f"adb -s {deviceId} shell ps | findstr {pkgName}").readlines()
        flag = len(result) > 0
        try:
            pid = (0,result[0].split()[1])[flag]
        except Exception:
            pid = None
        return pid

    def checkPkgname(self,pkgname):
        flag = True
        replace_list = ['com.google']
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
        self.report_dir = self.get_repordir()

    def get_repordir(self):
        report_dir = os.path.join(os.getcwd(), 'report')
        if not os.path.exists(report_dir):
            os.mkdir(report_dir)
        return report_dir

    def create_file(self,filename,content=''):
        if not os.path.exists(f'{self.report_dir}'):
            os.mkdir(f'{self.report_dir}')
        with open(f'{self.report_dir}/{filename}', 'a+', encoding="utf-8") as file:
            file.write(content)

    def make_report(self,app,devices):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        result_dict = {
            "app": app,
            "icon": "",
            "platform": "Android",
            "devices": devices,
            "ctime": current_time
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

    def instance_type(self,data):
        if isinstance(data,float):
            return 'float'
        elif isinstance(data,int):
            return 'int'
        else:
            return 'int'

    def readLog(self,scene,filename):
        """读取apmlog文件数据"""
        log_data_list = []
        target_data_list = []
        f = open(f'{self.report_dir}/{scene}/{filename}', "r")
        lines = f.readlines()
        for line in lines:
            if isinstance(line.split('=')[1].strip(),int):
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
        return log_data_list,target_data_list


class Adb():

    def shell(self,cmd):
        run_cmd  = f'adb shell {cmd}'
        result = subprocess.Popen(run_cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[
            0].decode("utf-8").strip()
        return result
