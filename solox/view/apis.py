import os
import shutil
import time

from flask import request
from logzero import logger
from flask import Blueprint

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
    try:
        deviceids = d.getDeviceIds()
        devices = d.getDevices()
        pkgnames = d.getPkgname(deviceids[0])
        if len(deviceids) > 0:
            result = {'status': 1, 'deviceids': deviceids, 'devices': devices, 'pkgnames': pkgnames}
        else:
            result = {'status': 0, 'msg': 'no devices,please try adb devices!'}
    except:
        result = {'status': 0, 'msg': 'no devices,please try adb devices!'}
    return result


@api.route('/device/packagenames', methods=['post', 'get'])
def packageNames():
    """get devices info"""
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pkgnames = d.getPkgname(deviceId)
    if len(pkgnames) > 0:
        result = {'status': 1, 'pkgnames': pkgnames}
    else:
        result = {'status': 0, 'msg': 'no pkgnames'}
    return result


@api.route('/apm/cpu', methods=['post', 'get'])
def getCpuRate():
    """get process cpu rate"""
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId, pkgName=pkgname)
    if pid:
        try:
            cpu = CPU(pkgName=pkgname, deviceId=deviceId)
            cpuRate = cpu.getSingCpuRate()
            result = {'status': 1, 'cpuRate': cpuRate}
        except Exception as e:
            logger.error(f'Get cpu failed:{str(e)}')
            result = {'status': 0, 'msg': f'{str(e)}'}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}

    return result


@api.route('/apm/mem', methods=['post', 'get'])
def getMEM():
    """get memery data"""
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId, pkgName=pkgname)
    if pid:
        try:
            mem = MEM(pkgName=pkgname, deviceId=deviceId)
            pss = mem.getProcessMem()
            result = {'status': 1, 'pss': pss}
        except Exception as e:
            logger.error(f'Get mem failed:{str(e)}')
            result = {'status': 0, 'msg': f'{str(e)}'}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}

    return result


@api.route('/apm/flow', methods=['post', 'get'])
def getFlow():
    """get network data"""
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId, pkgName=pkgname)
    if pid:
        try:
            flow = Flow(pkgName=pkgname, deviceId=deviceId)
            send = flow.getUpFlow()
            recv = flow.getDownFlow()
            result = {'status': 1, 'send': send, 'recv': recv}
        except Exception as e:
            logger.error(f'Get flow failed:{str(e)}')
            result = {'status': 0, 'msg': f'{str(e)}'}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}

    return result


@api.route('/apm/fps', methods=['post', 'get'])
def getFps():
    """get fps data"""
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId, pkgName=pkgname)
    if pid:
        try:
            fps_monitor = FPS(pkgName=pkgname, deviceId=deviceId)
            fps, jank = fps_monitor.getFPS()
            result = {'status': 1, 'fps': fps, 'jank': jank}
        except Exception as e:
            logger.error(f'Get fps failed:{str(e)}')
            result = {'status': 0, 'msg': f'{str(e)}'}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}
    return result


@api.route('/apm/battery', methods=['post', 'get'])
def getBattery():
    """get Battery data"""
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    try:
        battery_monitor = Battery(deviceId=deviceId)
        battery = battery_monitor.getBattery()
        result = {'status': 1, 'battery': battery}
    except Exception as e:
        logger.error(f'Get fps failed:{str(e)}')
        result = {'status': 0, 'msg': f'{str(e)}'}

    return result


@api.route('/apm/create/report', methods=['post', 'get'])
def makeReport():
    """创建测试报告记录"""
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    app = request.args.get('app')
    devices = request.args.get('devices')
    try:
        file(fileroot=f'apm_{current_time}').make_report(app=app, devices=devices)
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
