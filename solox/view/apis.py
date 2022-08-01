import os
import shutil
import time

from flask import request
from logzero import logger
from flask import Blueprint
import traceback

from solox.public.apm import CPU, MEM, Flow, FPS, Battery
from solox.public.common import Devices, file

d = Devices()
api = Blueprint("api", __name__)


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
        deviceId = d.getIdbyDevice(device)
        pkgnames = d.getPkgname(deviceId)
    elif platform == 'iOS':
        udid = device.split(':')[1]
        pkgnames = d.getPkgnameByiOS(udid)
    else:
        result = {'status': 0, 'msg': f'no platform = {platform}'}
        return result
    if len(pkgnames)>0:
        result = {'status':1,'pkgnames':pkgnames}
    else:
        result = {'status':0,'msg':'no pkgnames'}
    return result


@api.route('/apm/cpu', methods=['post', 'get'])
def getCpuRate():
    """get process cpu rate"""
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device,platform)
    try:
        cpu = CPU(pkgName=pkgname, deviceId=deviceId,platform=platform)
        cpuRate = cpu.getSingCpuRate()
        result = {'status': 1, 'cpuRate': cpuRate}
    except Exception as e:
        logger.error(f'get cpu failed:{str(e)}')
        traceback.print_exc()
        result = {'status': 0, 'msg': f'{str(e)}'}
    return result


@api.route('/apm/mem', methods=['post', 'get'])
def getMEM():
    """get memery data"""
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device,platform)
    try:
        mem = MEM(pkgName=pkgname, deviceId=deviceId,platform=platform)
        pss = mem.getProcessMem()
        result = {'status': 1, 'pss': pss}
    except Exception as e:
        logger.error(f'get mem failed:{str(e)}')
        result = {'status': 0, 'msg': f'{str(e)}'}
    return result


@api.route('/apm/network', methods=['post', 'get'])
def getNetWorkData():
    """get network data"""
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device,platform)
    try:
        flow = Flow(pkgName=pkgname, deviceId=deviceId, platform=platform)
        data = flow.getNetWorkData()
        result = {'status': 1, 'upflow': data[0],'downflow': data[1]}
    except Exception as e:
        logger.error(f'get network data failed:{str(e)}')
        result = {'status': 0, 'msg': f'{str(e)}'}
    return result

@api.route('/apm/fps', methods=['post', 'get'])
def getFps():
    """get fps data"""
    platform = request.args.get('platform')
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device,platform)
    try:
        fps_monitor = FPS(pkgName=pkgname, deviceId=deviceId, platform=platform)
        fps, jank = fps_monitor.getFPS()
        result = {'status': 1, 'fps': fps, 'jank': jank}
    except Exception as e:
        logger.error(f'get fps failed:{str(e)}')
        result = {'status': 0, 'msg': f'{str(e)}'}
    return result


@api.route('/apm/battery', methods=['post', 'get'])
def getBattery():
    """get Battery data"""
    platform = request.args.get('platform')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device,platform)
    try:
        battery_monitor = Battery(deviceId=deviceId)
        battery = battery_monitor.getBattery()
        result = {'status': 1, 'battery': battery}
    except Exception as e:
        logger.error(f'get battery failed:{str(e)}')
        result = {'status': 0, 'msg': f'{str(e)}'}
    return result


@api.route('/apm/create/report', methods=['post', 'get'])
def makeReport():
    """创建测试报告记录"""
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    platform = request.args.get('platform')
    app = request.args.get('app')
    devices = request.args.get('devices')
    try:
        file(fileroot=f'apm_{current_time}').make_report(app=app, devices=devices, platform=platform)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result


@api.route('/apm/edit/report', methods=['post', 'get'])
def editReport():
    """编辑测试报告记录"""
    old_scene = request.args.get('old_scene')
    new_scene = request.args.get('new_scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    if old_scene == new_scene:
        result = {'status': 0, 'msg': 'scene名称没有改变'}
    elif os.path.exists(f'{report_dir}/{new_scene}'):
        result = {'status': 0, 'msg': 'scene名称已经存在'}
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
    """获取apm详细数据"""
    scene = request.args.get('scene')
    target = request.args.get('target')
    try:
        log_data = file().readLog(scene=scene, filename=f'{target}.log')[0]
        result = {'status': 1, 'log_data': log_data}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result


@api.route('/apm/remove/report', methods=['post', 'get'])
def removeReport():
    """移除测试报告记录"""
    scene = request.args.get('scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    try:
        shutil.rmtree(f'{report_dir}/{scene}', True)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result
