import os
import shutil
import time
from flask import request, make_response
from logzero import logger
from flask import Blueprint
from solox.public.apm import CPU, Memory, Network, FPS, Battery, GPU, Target
from solox.public.apm_pk import CPU_PK, MEM_PK, Flow_PK, FPS_PK
from solox.public.common import Devices, File, Method, Install, Platform, Scrcpy

d = Devices()
f = File()
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
    duration = request.args.get('duration')
    solox_host = request.args.get('solox_host')
    host_switch = request.args.get('host_switch')

    resp = make_response('set cookie ok')
    resp.set_cookie('cpuWarning', cpuWarning)
    resp.set_cookie('memWarning', memWarning)
    resp.set_cookie('fpsWarning', fpsWarning)
    resp.set_cookie('netdataRecvWarning', netdataRecvWarning)
    resp.set_cookie('netdataSendWarning', netdataSendWarning)
    resp.set_cookie('betteryWarning', betteryWarning)
    resp.set_cookie('duration', duration)
    resp.set_cookie('solox_host', solox_host)
    resp.set_cookie('host_switch', host_switch)
    return resp


@api.route('/apm/initialize', methods=['post', 'get'])
def initialize():
    """initialize apm env"""
    try:
        f.clear_file()
        result = {'status': 1, 'msg': 'initialize env success'}
    except Exception as e:
        logger.exception(e)
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
    except Exception as e:
        logger.exception(e)
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


@api.route('/package/pids', methods=['post', 'get'])
def getPackagePids():
    platform = method._request(request, 'platform')
    device = method._request(request, 'device')
    pkgname = method._request(request, 'pkgname')
    try:
        deviceId = d.getIdbyDevice(device, platform)
        pids = d.getPid(deviceId, pkgname)
        if len(pids) > 0:
            result = {'status': 1, 'pids': pids}
        else:
            result = {'status': 0, 'msg': 'No process found, please start the app first.'} 
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': 'No process foundd, please start the app first.'} 
    return result        

@api.route('/package/activity', methods=['post', 'get'])
def getPackageActivity():
    platform = method._request(request, 'platform')
    device = method._request(request, 'device')
    try:
        deviceId = d.getIdbyDevice(device, platform)
        activity = d.getCurrentActivity(deviceId)
        result = {'status': 1, 'activity': activity} 
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': 'no activity found'} 
    return result


@api.route('/package/start/time/android', methods=['post', 'get'])
def getStartupTimeByAndroid():
    platform = method._request(request, 'platform')
    device = method._request(request, 'device')
    activity = method._request(request, 'activity')
    try:
        deviceId = d.getIdbyDevice(device, platform)
        time = d.getStartupTimeByAndroid(activity, deviceId)
        result = {'status': 1, 'time': time} 
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': 'no result found'} 
    return result

@api.route('/package/start/time/ios', methods=['post', 'get'])
def getStartupTimeByiOS():
    pkgname = method._request(request, 'pkgname')
    try:
        time = d.getStartupTimeByiOS(pkgname)
        result = {'status': 1, 'time': time} 
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': 'no result found'} 
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
                process = method._request(request, 'process')
                pid = None
                deviceId = d.getIdbyDevice(device, platform)
                if process and platform == Platform.Android :
                    pid = process.split(':')[0] 
                cpu = CPU(pkgName=pkgname, deviceId=deviceId, platform=platform, pid=pid)
                appCpuRate, systemCpuRate = cpu.getCpuRate()
                result = {'status': 1, 'appCpuRate': appCpuRate, 'systemCpuRate': systemCpuRate}        
    except Exception as e:
        logger.error('get cpu failed')
        logger.exception(e)
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
                process = method._request(request, 'process')
                pid = None
                deviceId = d.getIdbyDevice(device, platform)
                if process and platform == Platform.Android :
                    pid = process.split(':')[0] 
                mem = Memory(pkgName=pkgname, deviceId=deviceId, platform=platform, pid=pid)
                totalPass, nativePass, dalvikPass = mem.getProcessMem()
                result = {'status': 1, 'totalPass': totalPass, 'nativePass': nativePass, 'dalvikPass': dalvikPass}        
    except Exception as e:
        logger.error('get memory data failed')
        logger.exception(e)
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
    process = method._request(request, 'process')
    try:
        wifi = False if wifi_switch == 'false' else True
        deviceId = d.getIdbyDevice(device, platform)
        pid = None
        if process and platform == Platform.Android :
            pid = process.split(':')[0] 
        network = Network(pkgName=pkgname, deviceId=deviceId, platform=platform, pid=pid)
        data = network.setAndroidNet(wifi=wifi)
        f.record_net(type, data[0], data[1])
        result = {'status': 1, 'msg':'set network data success'}
    except Exception as e:
        logger.exception(e)
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
                process = method._request(request, 'process')
                pid = None
                deviceId = d.getIdbyDevice(device, platform)
                if process and platform == Platform.Android :
                    pid = process.split(':')[0] 
                network = Network(pkgName=pkgname, deviceId=deviceId, platform=platform, pid=pid)
                data = network.getNetWorkData(wifi=wifi,noLog=False)
                result = {'status': 1, 'upflow': data[0], 'downflow': data[1]}    
    except Exception as e:
        logger.error('get network data failed')
        logger.exception(e)
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
    except Exception as e:
        logger.error('get fps failed')
        logger.exception(e)
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
    except Exception as e:
        logger.exception(e)
        result = {'status': 1, 'level': 0, 'temperature': 0, 'current':0, 'voltage':0 , 'power':0}
    return result

@api.route('/apm/gpu', methods=['post', 'get'])
def getGpu():
    """get gpu data"""
    pkgname = method._request(request, 'pkgname')
    try:
        gpu = GPU(pkgName=pkgname)
        final = gpu.getGPU()
        result = {'status': 1, 'gpu': final}
    except Exception as e:
        logger.exception(e)
        result = {'status': 1, 'gpu': 0}
    return result


@api.route('/apm/create/report', methods=['post', 'get'])
def makeReport():
    """Create test report records"""
    platform = method._request(request, 'platform')
    app = method._request(request, 'app')
    model = method._request(request, 'model')
    devices = method._request(request, 'devices')
    wifi_switch = method._request(request, 'wifi_switch')
    record_switch = method._request(request, 'record_switch')
    process = method._request(request, 'process')
    try:
        video = 0
        if platform == Platform.Android:
            deviceId = d.getIdbyDevice(devices, platform)
            battery_monitor = Battery(deviceId=deviceId)
            battery_monitor.recoverBattery()
            wifi = False if wifi_switch == 'false' else True
            deviceId = d.getIdbyDevice(devices, platform)
            pid = None
            if process and platform == Platform.Android :
                pid = process.split(':')[0]
            network = Network(pkgName=app, deviceId=deviceId, platform=platform, pid=pid)
            data = network.setAndroidNet(wifi=wifi)
            f.record_net('end', data[0], data[1])
            record = False if record_switch == 'false' else True
            if record:
                video = 1
                Scrcpy.stop_record()
        f.make_report(app=app, devices=devices, video=video, platform=platform, model=model)
        result = {'status': 1}
    except Exception as e:
        logger.exception(e)
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
    elif os.path.exists(os.path.join(report_dir, new_scene)):
        result = {'status': 0, 'msg': 'scene existed'}
    else:
        try:
            new_scene = new_scene.replace('/', '_').replace(' ', '').replace('&', '_')
            os.rename(os.path.join(report_dir, old_scene), os.path.join(report_dir, new_scene))
            result = {'status': 1}
        except Exception as e:
            logger.exception(e)
            result = {'status': 0, 'msg': str(e)}
    return result

@api.route('/apm/export/report', methods=['post', 'get'])
def exportReport():
    platform = method._request(request, 'platform')
    scene = method._request(request, 'scene')
    try:
        path = f.export_excel(platform=platform, scene=scene)
        result = {'status': 1, 'msg':'success', 'path': path}
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg':str(e)}    
    return result

@api.route('/apm/export/html/android', methods=['post', 'get'])
def exportAndroidHtml():
    scene = method._request(request, 'scene')
    cpu_app = method._request(request, 'cpu_app')
    cpu_sys = method._request(request, 'cpu_sys')
    mem_total = method._request(request, 'mem_total')
    mem_native = method._request(request, 'mem_native')
    mem_dalvik = method._request(request, 'mem_dalvik')
    fps = method._request(request, 'fps')
    jank = method._request(request, 'jank')
    level = method._request(request, 'level')
    temperature = method._request(request, 'temperature')
    net_send = method._request(request, 'net_send')
    net_recv = method._request(request, 'net_recv')
    try:
        summary_dict = {}
        summary_dict['cpu_app'] = cpu_app
        summary_dict['cpu_sys'] = cpu_sys
        summary_dict['mem_total'] = mem_total
        summary_dict['mem_native'] = mem_native
        summary_dict['mem_dalvik'] = mem_dalvik
        summary_dict['fps'] = fps
        summary_dict['jank'] = jank
        summary_dict['level'] = level
        summary_dict['tem'] = temperature
        summary_dict['net_send'] = net_send
        summary_dict['net_recv'] = net_recv
        summary_dict['cpu_charts'] = f.getCpuLog(Platform.Android, scene)
        summary_dict['mem_charts'] = f.getMemLog(Platform.Android, scene)
        summary_dict['net_charts'] = f.getFlowLog(Platform.Android, scene)
        summary_dict['battery_charts'] = f.getBatteryLog(Platform.Android, scene)
        summary_dict['fps_charts'] = f.getFpsLog(Platform.Android, scene)['fps']
        summary_dict['jank_charts'] = f.getFpsLog(Platform.Android, scene)['jank']
        path = f.make_android_html(scene, summary_dict)
        result = {'status': 1, 'msg':'success', 'path':path}
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg':str(e)}    
    return result

@api.route('/apm/export/html/ios', methods=['post', 'get'])
def exportiOSHtml():
    scene = method._request(request, 'scene')
    cpu_app = method._request(request, 'cpu_app')
    cpu_sys = method._request(request, 'cpu_sys')
    mem_total = method._request(request, 'mem_total')
    gpu = method._request(request, 'gpu')
    fps = method._request(request, 'fps')
    temperature = method._request(request, 'temperature')
    current = method._request(request, 'current')
    voltage = method._request(request, 'voltage')
    power = method._request(request, 'power')
    net_send = method._request(request, 'net_send')
    net_recv = method._request(request, 'net_recv')
    try:
        summary_dict = {}
        summary_dict['cpu_app'] = cpu_app
        summary_dict['cpu_sys'] = cpu_sys
        summary_dict['mem_total'] = mem_total
        summary_dict['gpu'] = gpu
        summary_dict['fps'] = fps
        summary_dict['tem'] = temperature
        summary_dict['current'] = current
        summary_dict['voltage'] = voltage
        summary_dict['power'] = power
        summary_dict['net_send'] = net_send
        summary_dict['net_recv'] = net_recv
        summary_dict['cpu_charts'] = f.getCpuLog(Platform.iOS, scene)
        summary_dict['mem_charts'] = f.getMemLog(Platform.iOS, scene)
        summary_dict['net_charts'] = f.getFlowLog(Platform.iOS, scene)
        summary_dict['battery_charts'] = f.getBatteryLog(Platform.iOS, scene)
        summary_dict['fps_charts'] = f.getFpsLog(Platform.iOS, scene)
        summary_dict['gpu_charts'] = f.getGpuLog(Platform.iOS, scene)
        path = f.make_ios_html(scene, summary_dict)
        result = {'status': 1, 'msg':'success', 'path':path}
    except Exception as e:
        logger.exception(e)
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
        logger.exception(e)
        result = {'status': 0, 'msg': str(e)}
    return result

@api.route('/apm/log/compare', methods=['post', 'get'])
def getLogCompareData():
    """Get apm detailed data"""
    scene1 = method._request(request, 'scene1')
    scene2 = method._request(request, 'scene2')
    target = method._request(request, 'target')
    platform = method._request(request, 'platform')
    try:
        match(target):
            case Target.CPU:
                result = f.getCpuLogCompare(platform, scene1, scene2)
            case Target.Memory:
                result = f.getMemLogCompare(platform, scene1, scene2)
            case Target.Battery:
                result = f.getBatteryLogCompare(platform, scene1, scene2)
            case Target.FPS:
                result = f.getFpsLogCompare(platform, scene1, scene2)
            case Target.GPU:
                result = f.getGpuLogCompare(platform, scene1, scene2)
            case 'net_send':
                result = f.getFlowSendLogCompare(platform, scene1, scene2)
            case 'net_recv':
                result = f.getFlowRecvLogCompare(platform, scene1, scene2)                     
            case _:
                result = {'status': 0, 'msg': 'no target found'}        
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': str(e)}
    return result

@api.route('/apm/log/pk', methods=['post', 'get'])
def getpkLogData():
    """Get apm detailed data"""
    scene = method._request(request, 'scene')
    target1 = method._request(request, 'target1')
    target2 = method._request(request, 'target2')
    try:
        first = f.readLog(scene=scene, filename=f'{target1}.log')[0]
        second = f.readLog(scene=scene, filename=f'{target2}.log')[0]
        result = {'status': 1, 'first': first, 'second': second}
    except Exception as e:
        logger.exception(e)
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
        logger.exception(e)
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
                mem = Memory(pkgName=pkgname, deviceId=deviceid, platform=platform)
                totalPass, nativePass, dalvikPass = mem.getProcessMem(noLog=True)
                result = {'status': 1, 'totalPass': totalPass, 'nativePass': nativePass, 'dalvikPass': dalvikPass}
            case Target.Network:
                network = Network(pkgName=pkgname, deviceId=deviceid, platform=platform)
                data = network.getNetWorkData(wifi=True, noLog=True)
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
        logger.exception(e)
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

@api.route('/apm/record/start', methods=['post', 'get'])
def start_record():
    device = method._request(request, 'device')
    platform = method._request(request, 'platform')
    try:
        deviceId = d.getIdbyDevice(device, platform)
        final = Scrcpy.start_record(deviceId)
        if final == 0:
            result = {'status': 1, 'msg': 'success'}
        else:
            result = {'status': 0, 'msg': 'record screen failed'}
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': 'record screen failed'}          
    return result

@api.route('/apm/record/cast', methods=['post', 'get'])
def cast_screen():
    device = method._request(request, 'device')
    platform = method._request(request, 'platform')
    try:
        deviceId = d.getIdbyDevice(device, platform)
        final = Scrcpy.cast_screen(deviceId)
        if final == 0:
            result = {'status': 1, 'msg': 'success'}
        else:
            result = {'status': 0, 'msg': 'cast screen failed'}
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': 'cast screen failed'}          
    return result  

@api.route('/apm/record/play', methods=['post', 'get'])
def play_record():
    scene = method._request(request, 'scene')
    video = os.path.join(f.get_repordir(), scene, 'record.mkv')
    try:
        Scrcpy.play_video(video)
        result = {'status': 1, 'msg': 'success'}  
    except Exception as e:
        logger.exception(e)
        result = {'status': 0, 'msg': 'play video failed'}  
    return result    
