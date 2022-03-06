from flask import Blueprint
from flask import request
from ..public.apm import *
from ..public.common import *
import os
import json
import time
import shutil

api = Blueprint("api",__name__)
d = Devices()


@api.route('/device/ids',methods=['post','get'])
def deviceids():
    deviceids = d.getDeviceIds()
    devices = d.getDevices()
    pkgnames = d.getPkgname()
    if len(deviceids)>0:
        result = {'status':1,'deviceids':deviceids,'devices':devices,'pkgnames':pkgnames}
    else:
        result = {'status':0,'msg':'no devices'}
    return result

@api.route('/apm/cpu',methods=['post','get'])
def getCpuRate():
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId,pkgName=pkgname)
    if pid:
        cpu = CPU(pkgName=pkgname,deviceId=deviceId)
        cpuRate = cpu.getSingCpuRate()
        result = {'status': 1, 'cpuRate': cpuRate}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}

    return result

@api.route('/apm/create/report',methods=['post','get'])
def makeReport():
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    app = request.args.get('app')
    devices = request.args.get('devices')
    file(fileroot=f'apm_{current_time}').make_report(app=app,devices=devices)
    result = {'status': 1}
    return result

@api.route('/apm/edit/report',methods=['post','get'])
def editReport():
    old_scene = request.args.get('old_scene')
    new_scene = request.args.get('new_scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    if old_scene == new_scene:
        result = {'status': 0,'msg':'scene名称没有改变'}
    elif os.path.exists(f'{report_dir}/{new_scene}'):
        result = {'status': 0, 'msg': 'scene名称已经存在'}
    else:
        try:
            new_scene = new_scene.replace('/', '_').replace(' ', '').replace('&', '_')
            os.rename(f'{report_dir}/{old_scene}',f'{report_dir}/{new_scene}')
            result = {'status': 1}
        except Exception as e:
            result = {'status': 0,'msg':str(e)}
    return result

@api.route('/apm/log',methods=['post','get'])
def getLogData():
    scene = request.args.get('scene')
    target = request.args.get('target')
    try:
        cpu_data = file().readLog(scene=scene,filename=f'{target}.log')[0]
        result = {'status': 1,'cpu_data':cpu_data}
    except Exception as e:
        result = {'status': 0,'msg':str(e)}
    return result


@api.route('/apm/remove/report',methods=['post','get'])
def removeReport():
    scene = request.args.get('scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    try:
        shutil.rmtree(f'{report_dir}/{scene}', True)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0,'msg':str(e)}
    return result