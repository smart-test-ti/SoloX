import os
import shutil
import time
from flask import request, make_response
from logzero import logger
from flask import Blueprint
# import traceback
from solox.public.apm import CPU, MEM, Flow, FPS, Battery
from solox.public.apm_pk import CPU_PK, MEM_PK, Flow_PK, FPS_PK
from solox.public.common import Devices, file, Method

d = Devices()
api = Blueprint("api", __name__)


@api.route('/apm/cookie', methods=['post', 'get'])
def setCookie():
    """set apm data to cookie"""
    cpuWarning = request.args.get('cpuWarning')
    memWarning = request.args.get('memWarning')
    fpsWarning = request.args.get('fpsWarning')
    netdataRecvWarning = request.args.get('netdataRecvWarning')
    netdataSendWarning = request.args.get('netdataSendWarning')
    betteryWarning = request.args.get('betteryWarning')
    resp = make_response('set cookie ok')
    resp.set_cookie('cpuWarning', cpuWarning)
    resp.set_cookie('memWarning', memWarning)
    resp.set_cookie('fpsWarning', fpsWarning)
    resp.set_cookie('netdataRecvWarning', netdataRecvWarning)
    resp.set_cookie('netdataSendWarning', netdataSendWarning)
    resp.set_cookie('betteryWarning', betteryWarning)
    return resp


@api.route('/apm/initialize', methods=['post', 'get'])
def initialize():
    """initialize apm env"""
    try:
        report_dir = os.path.join(os.getcwd(), 'report')
        if os.path.exists(report_dir):
            for f in os.listdir(report_dir):
                filename = os.path.join(report_dir, f)
                if f.split(".")[-1] in ['log', 'json']:
                    os.remove(filename)
        result = {'status': 1, 'msg': 'initialize env success'}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}

    return result


@api.route('/device/ids', methods=['post', 'get'])
def deviceids():
    """get devices info"""
    platform = request.args.get('platform')
    try:
        if platform == 'Android':
            deviceids = d.getDeviceIds()
            devices = d.getDevices()
            if len(deviceids) > 0:
                pkgnames = d.getPkgname(deviceids[0])
                result = {'status': 1, 'deviceids': deviceids, 'devices': devices, 'pkgnames': pkgnames}
            else:
                result = {'status': 0, 'msg': 'no devices'}
        elif platform == 'iOS':
            deviceinfos = d.getDeviceInfoByiOS()
            if len(deviceinfos) > 0:
                pkgnames = d.getPkgnameByiOS(deviceinfos[0].split(':')[1])
                result = {'status': 1, 'deviceids': deviceinfos, 'devices': deviceinfos, 'pkgnames': pkgnames}
            else:
                result = {'status': 0, 'msg': 'no devices'}
        else:
            result = {'status': 0, 'msg': f'no this platform = {platform}'}
    except:
        result = {'status': 0, 'msg': 'devices connect error!'}
    return result


@api.route('/device/packagenames', methods=['post', 'get'])
def packageNames():
    """get devices packageNames"""
    platform = request.args.get('platform')
    device = request.args.get('device')
    if platform == 'Android':
        deviceId = d.getIdbyDevice(device, platform)
        pkgnames = d.getPkgname(deviceId)
    elif platform == 'iOS':
        udid = device.split(':')[1]
        pkgnames = d.getPkgnameByiOS(udid)
    else:
        result = {'status': 0, 'msg': f'no platform = {platform}'}
        return result
    if len(pkgnames) > 0:
        result = {'status': 1, 'pkgnames': pkgnames}
    else:
        result = {'status': 0, 'msg': 'no pkgnames'}
    return result


@api.route('/apm/cpu', methods=['post', 'get'])
def getCpuRate():
    """get process cpu rate"""
    model = request.args.get('model')
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    try:
        if model == '2-devices':
            pkgNameList = []
            pkgNameList.append(pkgname)
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            cpu = CPU_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = cpu.getAndroidCpuRate()
            result = {'status': 1, 'first': first, 'second': second}
        elif model == '2-app':
            pkgNameList = pkgname.split(',')
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            cpu = CPU_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = cpu.getAndroidCpuRate()
            result = {'status': 1, 'first': first, 'second': second}
        else:
            deviceId = d.getIdbyDevice(device, platform)
            cpu = CPU(pkgName=pkgname, deviceId=deviceId, platform=platform)
            appCpuRate, systemCpuRate = cpu.getCpuRate()
            result = {'status': 1, 'appCpuRate': appCpuRate, 'systemCpuRate': systemCpuRate}
    except Exception as e:
        logger.error(f'get cpu failed : {str(e)}')
        result = {'status': 1, 'appCpuRate': 0, 'systemCpuRate': 0, 'first': 0, 'second': 0}
    return result


@api.route('/apm/mem', methods=['post', 'get'])
def getMEM():
    """get memery data"""
    model = request.args.get('model')
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    try:
        if model == '2-devices':
            pkgNameList = []
            pkgNameList.append(pkgname)
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            mem = MEM_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = mem.getProcessMem()
            result = {'status': 1, 'first': first, 'second': second}
        elif model == '2-app':
            pkgNameList = pkgname.split(',')
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            mem = MEM_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = mem.getProcessMem()
            result = {'status': 1, 'first': first, 'second': second}
        else:
            deviceId = d.getIdbyDevice(device, platform)
            mem = MEM(pkgName=pkgname, deviceId=deviceId, platform=platform)
            totalPass, nativePass, dalvikPass = mem.getProcessMem()
            result = {'status': 1, 'totalPass': totalPass, 'nativePass': nativePass, 'dalvikPass': dalvikPass}
    except Exception as e:
        logger.error(f'get memory data failed : {str(e)}')
        result = {'status': 1, 'totalPass': 0, 'nativePass': 0, 'dalvikPass': 0, 'first': 0, 'second': 0}
    return result


@api.route('/apm/network', methods=['post', 'get'])
def getNetWorkData():
    """get network data"""
    model = request.args.get('model')
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    try:
        if model == '2-devices':
            pkgNameList = []
            pkgNameList.append(pkgname)
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            network = Flow_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = network.getNetWorkData()
            result = {'status': 1, 'first': first, 'second': second}
        elif model == '2-app':
            pkgNameList = pkgname.split(',')
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            network = Flow_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = network.getNetWorkData()
            result = {'status': 1, 'first': first, 'second': second}
        else:
            deviceId = d.getIdbyDevice(device, platform)
            flow = Flow(pkgName=pkgname, deviceId=deviceId, platform=platform)
            data = flow.getNetWorkData()
            result = {'status': 1, 'upflow': data[0], 'downflow': data[1]}
    except Exception as e:
        logger.error(f'get network data failed : {str(e)}')
        result = {'status': 1, 'upflow': 0, 'downflow': 0, 'first': 0, 'second': 0}
    return result


@api.route('/apm/fps', methods=['post', 'get'])
def getFps():
    """get fps data"""
    model = request.args.get('model')
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    try:
        if model == '2-devices':
            pkgNameList = []
            pkgNameList.append(pkgname)
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            fps = FPS_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = fps.getFPS()
            result = {'status': 1, 'first': first, 'second': second}
        elif model == '2-app':
            pkgNameList = pkgname.split(',')
            deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
            deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
            fps = FPS_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
            first, second = fps.getFPS()
            result = {'status': 1, 'first': first, 'second': second}
        else:
            deviceId = d.getIdbyDevice(device, platform)
            fps_monitor = FPS(pkgName=pkgname, deviceId=deviceId, platform=platform)
            fps, jank = fps_monitor.getFPS()
            result = {'status': 1, 'fps': fps, 'jank': jank}
    except Exception as e:
        logger.error(f'get fps failed : {str(e)}')
        result = {'status': 1, 'fps': 0, 'jank': 0, 'first': 0, 'second': 0}
    return result


@api.route('/apm/battery', methods=['post', 'get'])
def getBattery():
    """get Battery data"""
    platform = request.args.get('platform')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device, platform)
    try:
        battery_monitor = Battery(deviceId=deviceId)
        level, temperature = battery_monitor.getBattery()
        result = {'status': 1, 'level': level, 'temperature': temperature}
    except Exception as e:
        if not deviceId:
            logger.error('no device，please check the device connection status')
        else:
            logger.error(f'get cpu failed : {str(e)}')
        result = {'status': 1, 'level': 0, 'temperature': 0}
    return result


@api.route('/apm/create/report', methods=['post', 'get'])
def makeReport():
    """Create test report records"""
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    platform = request.args.get('platform')
    app = request.args.get('app')
    model = request.args.get('model')
    devices = request.args.get('devices')
    try:
        file(fileroot=f'apm_{current_time}').make_report(app=app, devices=devices, platform=platform, model=model)
        battery_monitor = Battery(deviceId=devices)
        battery_monitor.recoverBattery()
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result


@api.route('/apm/edit/report', methods=['post', 'get'])
def editReport():
    """Edit test report records"""
    old_scene = request.args.get('old_scene')
    new_scene = request.args.get('new_scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    if old_scene == new_scene:
        result = {'status': 0, 'msg': 'scene not changed'}
    elif os.path.exists(f'{report_dir}/{new_scene}'):
        result = {'status': 0, 'msg': 'scene existed'}
    else:
        try:
            new_scene = new_scene.replace('/', '_').replace(' ', '').replace('&', '_')
            os.rename(f'{report_dir}/{old_scene}', f'{report_dir}/{new_scene}')
            result = {'status': 1}
        except Exception as e:
            result = {'status': 0, 'msg': str(e)}
    return result


@api.route('/apm/log', methods=['post', 'get'])
def getLogData():
    """Get apm detailed data"""
    scene = request.args.get('scene')
    target = request.args.get('target')
    platform = request.args.get('platform')
    try:
        if target == 'cpu':
            cpuAppData = file().readLog(scene=scene, filename='cpu_app.log')[0]
            if platform == 'Android':
                cpuSysData = file().readLog(scene=scene, filename='cpu_sys.log')[0]
                result = {'status': 1, 'cpuAppData': cpuAppData, 'cpuSysData': cpuSysData}
            else:
                result = {'status': 1, 'cpuAppData': cpuAppData}
        elif target == 'mem':
            memTotalData = file().readLog(scene=scene, filename='mem_total.log')[0]
            if platform == 'Android':
                memNativeData = file().readLog(scene=scene, filename='mem_native.log')[0]
                memDalvikData = file().readLog(scene=scene, filename='mem_dalvik.log')[0]
                result = {'status': 1, 'memTotalData': memTotalData, 'memNativeData': memNativeData,
                          'memDalvikData': memDalvikData}
            else:
                result = {'status': 1, 'memTotalData': memTotalData}

        elif target == 'battery':
            batteryLevel = file().readLog(scene=scene, filename='battery_level.log')[0]
            batteryTem = file().readLog(scene=scene, filename='battery_tem.log')[0]
            result = {'status': 1, 'batteryLevel': batteryLevel, 'batteryTem': batteryTem}
        elif target == 'flow':
            upFlow = file().readLog(scene=scene, filename='upflow.log')[0]
            downFlow = file().readLog(scene=scene, filename='downflow.log')[0]
            result = {'status': 1, 'upFlow': upFlow, 'downFlow': downFlow}
        else:
            log_data = file().readLog(scene=scene, filename=f'{target}.log')[0]
            result = {'status': 1, 'log_data': log_data}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result

@api.route('/apm/log/pk', methods=['post', 'get'])
def getpkLogData():
    """Get apm detailed data"""
    scene = request.args.get('scene')
    target1 = request.args.get('target1')
    target2 = request.args.get('target2')
    try:
        first = file().readLog(scene=scene, filename=f'{target1}.log')[0]
        second = file().readLog(scene=scene, filename=f'{target2}.log')[0]
        result = {'status': 1, 'first': first, 'second': second}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result


@api.route('/apm/remove/report', methods=['post', 'get'])
def removeReport():
    """Remove test report record"""
    scene = request.args.get('scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    try:
        shutil.rmtree(f'{report_dir}/{scene}', True)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result


@api.route('/apm/collect', methods=['post', 'get'])
def apmCollect():
    """apm common api"""
    platform = request.args.get('platform')
    deviceid = request.args.get('deviceid')
    pkgname = request.args.get('pkgname')
    apm_type = request.args.get('apm_type')
    try:
        if apm_type == 'cpu':
            cpu = CPU(pkgName=pkgname, deviceId=deviceid, platform=platform)
            appCpuRate, systemCpuRate = cpu.getCpuRate()
            result = {'status': 1, 'appCpuRate': appCpuRate, 'systemCpuRate': systemCpuRate}
        elif apm_type == 'memory':
            mem = MEM(pkgName=pkgname, deviceId=deviceid, platform=platform)
            totalPass, nativePass, dalvikPass = mem.getProcessMem()
            result = {'status': 1, 'totalPass': totalPass, 'nativePass': nativePass, 'dalvikPass': dalvikPass}
        elif apm_type == 'network':
            flow = Flow(pkgName=pkgname, deviceId=deviceid, platform=platform)
            data = flow.getNetWorkData()
            result = {'status': 1, 'upflow': data[0], 'downflow': data[1]}
        elif apm_type == 'fps':
            fps_monitor = FPS(pkgName=pkgname, deviceId=deviceid, platform=platform)
            fps, jank = fps_monitor.getFPS()
            result = {'status': 1, 'fps': fps, 'jank': jank}
        elif apm_type == 'battery':
            battery_monitor = Battery(deviceId=deviceid)
            level, temperature = battery_monitor.getBattery()
            result = {'status': 1, 'level': level, 'temperature': temperature}
        else:
            result = {'status': 0, 'msg': 'no this apm_type'}

    except Exception as e:
        if not deviceid:
            logger.error('no device，please check the device connection status')
        elif not d.getPid(deviceid, pkgname):
            logger.error('no app process，please check if the app is started')
        else:
            logger.error(f'get {apm_type} failed : {str(e)}')
        result = {'status': 0, 'msg': str(e)}

    return result
