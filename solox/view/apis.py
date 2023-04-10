import os
import shutil
import time
from flask import request, make_response
from logzero import logger
from flask import Blueprint
import traceback
from solox.public.apm import CPU, MEM, Flow, FPS, Battery, GPU, Target
from solox.public.apm_pk import CPU_PK, MEM_PK, Flow_PK, FPS_PK
from solox.public.common import Devices, file, Method, Install, Platform

d = Devices()
f = file()
api = Blueprint("api", __name__)
method = Method()

@api.route('/apm/cookie', methods=['post', 'get'])
def setCookie():
    """set apm data to cookie"""
    cpuWarning = request.args.get('cpuWarning')
    memWarning = request.args.get('memWarning')
    fpsWarning = request.args.get('fpsWarning')
    netdataRecvWarning = request.args.get('netdataRecvWarning')
    netdataSendWarning = request.args.get('netdataSendWarning')
    betteryWarning = request.args.get('betteryWarning')
    runningTime = request.args.get('runningTime')
    solox_host = request.args.get('solox_host')
    host_switch = request.args.get('host_switch')

    resp = make_response('set cookie ok')
    resp.set_cookie('cpuWarning', cpuWarning)
    resp.set_cookie('memWarning', memWarning)
    resp.set_cookie('fpsWarning', fpsWarning)
    resp.set_cookie('netdataRecvWarning', netdataRecvWarning)
    resp.set_cookie('netdataSendWarning', netdataSendWarning)
    resp.set_cookie('betteryWarning', betteryWarning)
    resp.set_cookie('runningTime', runningTime)
    resp.set_cookie('solox_host', solox_host)
    resp.set_cookie('host_switch', host_switch)
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
        traceback.print_exc()
        result = {'status': 0, 'msg': str(e)}

    return result


@api.route('/device/ids', methods=['post', 'get'])
def deviceids():
    """get devices info"""
    platform = method._request(request, 'platform')
    try:
        match(platform):
            case Platform.Android:
                deviceids = d.getDeviceIds()
                devices = d.getDevices()
                if len(deviceids) > 0:
                    pkgnames = d.getPkgname(deviceids[0])
                    device_detail = d.getDdeviceDetail(deviceId=deviceids[0], platform=platform)
                    result = {'status': 1, 
                              'deviceids': deviceids, 
                              'devices': devices,
                              'pkgnames': pkgnames, 
                              'device_detail': device_detail}
                else:
                    result = {'status': 0, 'msg': 'no devices'}
            case Platform.iOS:
                deviceinfos = d.getDeviceInfoByiOS()
                if len(deviceinfos) > 0:
                    pkgnames = d.getPkgnameByiOS(deviceinfos[0].split(':')[1])
                    device_detail = d.getDdeviceDetail(deviceId=deviceinfos[0].split(':')[1], platform=platform)
                    result = {'status': 1, 
                              'deviceids': deviceinfos, 
                              'devices': deviceinfos,
                              'pkgnames': pkgnames, 
                              'device_detail': device_detail}
                else:
                    result = {'status': 0, 'msg': 'no devices'}
            case _:
                result = {'status': 0, 'msg': f'no this platform = {platform}'}        
    except Exception:
        traceback.print_exc()
        result = {'status': 0, 'msg': 'devices connect error!'}
    return result


@api.route('/device/packagenames', methods=['post', 'get'])
def packageNames():
    """get devices packageNames"""
    platform = method._request(request, 'platform')
    device = method._request(request, 'device')
    match(platform):
        case Platform.Android:
            deviceId = d.getIdbyDevice(device, platform)
            pkgnames = d.getPkgname(deviceId)
        case Platform.iOS:
            udid = device.split(':')[1]
            pkgnames = d.getPkgnameByiOS(udid)
        case _:
            result = {'status': 0, 'msg': 'platform is undefined'}
            return result
    result = {'status': 1, 'pkgnames': pkgnames} if len(pkgnames) > 0 else  {'status': 0, 'msg': 'no pkgnames'} 
    return result


@api.route('/apm/cpu', methods=['post', 'get'])
def getCpuRate():
    """get process cpu rate"""
    model = method._request(request, 'model')
    platform = method._request(request, 'platform')
    pkgname = method._request(request, 'pkgname')
    device = method._request(request, 'device')
    try:
        match(model):
            case '2-devices':
                pkgNameList = []
                pkgNameList.append(pkgname)
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                cpu = CPU_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
                first, second = cpu.getAndroidCpuRate()
                result = {'status': 1, 'first': first, 'second': second}
            case '2-app':
                pkgNameList = pkgname.split(',')
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                cpu = CPU_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
                first, second = cpu.getAndroidCpuRate()
                result = {'status': 1, 'first': first, 'second': second}
            case _:
                deviceId = d.getIdbyDevice(device, platform)
                cpu = CPU(pkgName=pkgname, deviceId=deviceId, platform=platform)
                appCpuRate, systemCpuRate = cpu.getCpuRate()
                result = {'status': 1, 'appCpuRate': appCpuRate, 'systemCpuRate': systemCpuRate}        
    except Exception:
        logger.error('get cpu failed')
        traceback.print_exc()
        result = {'status': 1, 'appCpuRate': 0, 'systemCpuRate': 0, 'first': 0, 'second': 0}
    return result


@api.route('/apm/mem', methods=['post', 'get'])
def getMEM():
    """get memery data"""
    model = method._request(request, 'model')
    platform = method._request(request, 'platform')
    pkgname = method._request(request, 'pkgname')
    device = method._request(request, 'device')
    try:
        match(model):
            case '2-devices':
                pkgNameList = []
                pkgNameList.append(pkgname)
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                mem = MEM_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
                first, second = mem.getProcessMem()
                result = {'status': 1, 'first': first, 'second': second}
            case '2-app':
                pkgNameList = pkgname.split(',')
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                mem = MEM_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
                first, second = mem.getProcessMem()
                result = {'status': 1, 'first': first, 'second': second}
            case _:
                deviceId = d.getIdbyDevice(device, platform)
                mem = MEM(pkgName=pkgname, deviceId=deviceId, platform=platform)
                totalPass, nativePass, dalvikPass = mem.getProcessMem()
                result = {'status': 1, 'totalPass': totalPass, 'nativePass': nativePass, 'dalvikPass': dalvikPass}        
    except Exception:
        logger.error('get memory data failed')
        traceback.print_exc()
        result = {'status': 1, 'totalPass': 0, 'nativePass': 0, 'dalvikPass': 0, 'first': 0, 'second': 0}
    return result

@api.route('/apm/set/network', methods=['post', 'get'])
def setNetWorkData():
    """set network data"""
    platform = method._request(request, 'platform')
    pkgname = method._request(request, 'pkgname')
    device = method._request(request, 'device')
    wifi_switch = method._request(request, 'wifi_switch')
    type = method._request(request, 'type')
    try:
        wifi = False if wifi_switch == 'false' else True
        deviceId = d.getIdbyDevice(device, platform)
        flow = Flow(pkgName=pkgname, deviceId=deviceId, platform=platform)
        data = flow.setAndroidNet(wifi=wifi)
        f.record_net(type, data[0], data[1])
        result = {'status': 1, 'msg':'set network data success'}
    except Exception as e:
        traceback.print_exc()
        result = {'status': 0, 'msg':'set network data failed'}
    return result        

@api.route('/apm/network', methods=['post', 'get'])
def getNetWorkData():
    """get network data"""
    model = method._request(request, 'model')
    platform = method._request(request, 'platform')
    pkgname = method._request(request, 'pkgname')
    device = method._request(request, 'device')
    wifi_switch = method._request(request, 'wifi_switch')
    try:
        wifi = False if wifi_switch == 'false' else True
        match(model):
            case '2-devices':
                pkgNameList = []
                pkgNameList.append(pkgname)
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                network = Flow_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
                first, second = network.getNetWorkData()
                result = {'status': 1, 'first': first, 'second': second}
            case '2-app':
                pkgNameList = pkgname.split(',')
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                network = Flow_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2)
                first, second = network.getNetWorkData()
                result = {'status': 1, 'first': first, 'second': second}
            case _:
                deviceId = d.getIdbyDevice(device, platform)
                flow = Flow(pkgName=pkgname, deviceId=deviceId, platform=platform)
                data = flow.getNetWorkData(wifi=wifi,noLog=False)
                result = {'status': 1, 'upflow': data[0], 'downflow': data[1]}    
    except Exception:
        logger.error('get network data failed')
        traceback.print_exc()
        result = {'status': 1, 'upflow': 0, 'downflow': 0, 'first': 0, 'second': 0}    
    return result


@api.route('/apm/fps', methods=['post', 'get'])
def getFps():
    """get fps data"""
    model = method._request(request, 'model')
    platform = method._request(request, 'platform')
    pkgname = method._request(request, 'pkgname')
    device = method._request(request, 'device')
    surv = method._request(request, 'surv')
    try:
        surfaceview = False if surv == 'false' else True
        match(model):
            case '2-devices':
                pkgNameList = []
                pkgNameList.append(pkgname)
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                fps = FPS_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2, surfaceview=surfaceview)
                first, second = fps.getFPS()
                result = {'status': 1, 'first': first, 'second': second}
            case '2-app':
                pkgNameList = pkgname.split(',')
                deviceId1 = d.getIdbyDevice(device.split(',')[0], 'Android')
                deviceId2 = d.getIdbyDevice(device.split(',')[1], 'Android')
                fps = FPS_PK(pkgNameList=pkgNameList, deviceId1=deviceId1, deviceId2=deviceId2, surfaceview=surfaceview)
                first, second = fps.getFPS()
                result = {'status': 1, 'first': first, 'second': second}
            case _:
                deviceId = d.getIdbyDevice(device, platform)
                fps_monitor = FPS(pkgName=pkgname, deviceId=deviceId, surfaceview=surfaceview, platform=platform)
                fps, jank = fps_monitor.getFPS()
                result = {'status': 1, 'fps': fps, 'jank': jank}       
    except Exception:
        logger.error('get fps failed')
        traceback.print_exc()
        result = {'status': 1, 'fps': 0, 'jank': 0, 'first': 0, 'second': 0}
    return result


@api.route('/apm/battery', methods=['post', 'get'])
def getBattery():
    """get Battery data"""
    platform = method._request(request, 'platform')
    device = method._request(request, 'device')
    try:
        deviceId = d.getIdbyDevice(device, platform)
        battery_monitor = Battery(deviceId=deviceId, platform=platform)
        final = battery_monitor.getBattery()
        if platform == Platform.Android:
            result = {'status': 1, 'level': final[0], 'temperature': final[1]}
        else:
            result = {
                'status': 1, 
                'temperature': final[0], 
                'current': final[1], 
                'voltage': final[2], 
                'power': final[3]}    
    except Exception:
        traceback.print_exc()
        result = {'status': 1, 'level': 0, 'temperature': 0, 'current':0, 'voltage':0 , 'power':0}
    return result

@api.route('/apm/gpu', methods=['post', 'get'])
def getGpu():
    """get gpu data"""
    pkgname = method._request(request, 'pkgname')
    try:
        gpu = GPU(pkgname=pkgname)
        final = gpu.getGPU()
        result = {'status': 1, 'gpu': final}
    except Exception:
        traceback.print_exc()
        result = {'status': 1, 'gpu': 0}
    return result


@api.route('/apm/create/report', methods=['post', 'get'])
def makeReport():
    """Create test report records"""
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    platform = method._request(request, 'platform')
    app = method._request(request, 'app')
    model = method._request(request, 'model')
    devices = method._request(request, 'devices')
    wifi_switch = method._request(request, 'wifi_switch')
    try:
        if platform == Platform.Android:
            deviceId = d.getIdbyDevice(devices, platform)
            battery_monitor = Battery(deviceId=deviceId)
            battery_monitor.recoverBattery()
            wifi = False if wifi_switch == 'false' else True
            deviceId = d.getIdbyDevice(devices, platform)
            flow = Flow(pkgName=app, deviceId=deviceId, platform=platform)
            data = flow.setAndroidNet(wifi=wifi)
            f.record_net('end', data[0], data[1])
        file(fileroot=f'apm_{current_time}').make_report(app=app, devices=devices, platform=platform, model=model)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result


@api.route('/apm/edit/report', methods=['post', 'get'])
def editReport():
    """Edit test report records"""
    old_scene = method._request(request, 'old_scene')
    new_scene = method._request(request, 'new_scene')
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

@api.route('/apm/export/report', methods=['post', 'get'])
def exportReport():
    platform = method._request(request, 'platform')
    scene = method._request(request, 'scene')
    try:
        file().export_excel(platform=platform, scene=scene)
        result = {'status': 1, 'msg':'success'}
    except Exception as e:
        traceback.print_exc()
        result = {'status': 0, 'msg':str(e)}    
    return result    

@api.route('/apm/log', methods=['post', 'get'])
def getLogData():
    """Get apm detailed data"""
    scene = method._request(request, 'scene')
    target = method._request(request, 'target')
    platform = method._request(request, 'platform')
    try:
        fucDic = {
            'cpu': f.getCpuLog(platform, scene),
            'mem': f.getMemLog(platform, scene),
            'battery': f.getBatteryLog(platform, scene),
            'flow': f.getFlowLog(platform, scene),
            'fps': f.getFpsLog(platform, scene),
            'gpu': f.getGpuLog(platform, scene)
        }
        result = fucDic[target]
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result

@api.route('/apm/log/pk', methods=['post', 'get'])
def getpkLogData():
    """Get apm detailed data"""
    scene = method._request(request, 'scene')
    target1 = method._request(request, 'target1')
    target2 = method._request(request, 'target2')
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
    scene = method._request(request, 'scene')
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
    platform = method._request(request, 'platform')
    deviceid = method._request(request, 'deviceid')
    pkgname = method._request(request, 'pkgname')
    target = method._request(request, 'target')
    try:
        match(target):
            case Target.CPU:
                cpu = CPU(pkgName=pkgname, deviceId=deviceid, platform=platform)
                appCpuRate, systemCpuRate = cpu.getCpuRate(noLog=True)
                result = {'status': 1, 'appCpuRate': appCpuRate, 'systemCpuRate': systemCpuRate}
            case Target.Memory:
                mem = MEM(pkgName=pkgname, deviceId=deviceid, platform=platform)
                totalPass, nativePass, dalvikPass = mem.getProcessMem(noLog=True)
                result = {'status': 1, 'totalPass': totalPass, 'nativePass': nativePass, 'dalvikPass': dalvikPass}
            case Target.Network:
                flow = Flow(pkgName=pkgname, deviceId=deviceid, platform=platform)
                data = flow.getNetWorkData(wifi=True, noLog=True)
                result = {'status': 1, 'upflow': data[0], 'downflow': data[1]}
            case Target.FPS:
                fps_monitor = FPS(pkgName=pkgname, deviceId=deviceid, platform=platform)
                fps, jank = fps_monitor.getFPS(noLog=True)
                result = {'status': 1, 'fps': fps, 'jank': jank}
            case Target.Battery:
                battery_monitor = Battery(deviceId=deviceid)
                final = battery_monitor.getBattery(noLog=True)
                if platform == 'Android':
                    result = {'status': 1, 'level': final[0], 'temperature': final[1]}
                else:
                    result = {'status': 1, 'temperature': final[0], 'current': final[1], 'voltage': final[2], 'power': final[3]}
            case Target.GPU:
                if platform == Platform.iOS:
                    gpu = GPU(pkgname=pkgname)
                    final = gpu.getGPU()
                    result = {'status': 1, 'gpu': final}
                else:
                    result = {'status': 0, 'msg': 'not support android'}    
            case _:
                result = {'status': 0, 'msg': 'no this target'}
    except Exception as e:
        traceback.print_exc()
        result = {'status': 0, 'msg': str(e)}
    return result

@api.route('/apm/install/file', methods=['post', 'get'])
def installFile():
    """install apk/ipa from file"""
    platform = method._request(request, 'platform')
    file = request.files['file']
    currentPath = os.path.dirname(os.path.realpath(__file__))
    install = Install()
    unixtime = int(time.time())
    if platform == Platform.Android:
        file_path = os.path.join(currentPath, '{}.apk'.format(unixtime))
        if install.uploadFile(file_path, file):
            install_status = install.installAPK(file_path)
        else:
            result = {'status': 0, 'msg': 'install file failed'} 
            return result   
    else:
        file_path = os.path.join(currentPath, '{}.ipa'.format(unixtime))
        if install.uploadFile(file_path, file):
            install_status = install.installIPA(file_path)
        else:
            result = {'status': 0, 'msg': 'install file failed'}   
            return result 
    if install_status[0]:
        result = {'status': 1, 'msg': 'install sucess'}
    else:
        result = {'status': 0, 'msg': install_status[1]}                 
    return result

@api.route('/apm/install/link', methods=['post', 'get'])
def installLink():
    """install apk/ipa from link"""
    platform = method._request(request, 'platform')
    link = method._request(request, 'link')
    currentPath = os.path.dirname(os.path.realpath(__file__))
    install = Install()
    unixtime = int(time.time())
    if platform == Platform.Android:
        d_status = install.downloadLink(filelink=link, path=currentPath, name='{}.apk'.format(unixtime))
        if d_status:
            install_status = install.installAPK(os.path.join(currentPath, '{}.apk'.format(unixtime)))
        else:
            result = {'status': 0, 'msg': 'download link failed'}    
            return result   
    else:
        d_status = install.downloadLink(filelink=link, path=currentPath, name='{}.ipa'.format(unixtime))
        if d_status:
            install_status = install.installIPA(os.path.join(currentPath, '{}.ipa'.format(unixtime)))
        else:
            result = {'status': 0, 'msg': 'download link failed'}
            return result
    if install_status[0]:
        result = {'status': 1, 'msg': 'install sucess'}
    else:
        result = {'status': 0, 'msg': install_status[1]}                 
    return result