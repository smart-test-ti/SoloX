from . import *

api = Blueprint("api",__name__)

@api.route('/apm/initialize',methods=['post','get'])
def initialize():
    """初始化apm环境"""
    try:
        report_dir = os.path.join(os.getcwd(), 'report')
        if os.path.exists(report_dir):
            for f in os.listdir(report_dir):
                filename = os.path.join(report_dir, f)
                if f.split(".")[-1] in ['log','json']:
                    os.remove(filename)
        result = {'status': 1, 'msg': 'initialize env success'}
    except Exception as e:
        result = {'status': 0, 'msg': str(e)}
    return result

@api.route('/device/ids',methods=['post','get'])
def deviceids():
    """获取设备包名信息"""
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
    """获取进程cpu损耗占比"""
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId,pkgName=pkgname)
    if pid:
        try:
            cpu = CPU(pkgName=pkgname,deviceId=deviceId)
            cpuRate = cpu.getSingCpuRate()
            result = {'status': 1, 'cpuRate': cpuRate}
        except Exception as e:
            logger.error(f'Get cpu failed:{str(e)}')
            result = {'status': 0, 'msg': f'{str(e)}'}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}

    return result

@api.route('/apm/mem',methods=['post','get'])
def getMEM():
    """获取内存损耗"""
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId,pkgName=pkgname)
    if pid:
        try:
            mem = MEM(pkgName=pkgname,deviceId=deviceId)
            pss = mem.getProcessMem()
            result = {'status': 1, 'pss': pss}
        except Exception as e:
            logger.error(f'Get mem failed:{str(e)}')
            result = {'status': 0, 'msg': f'{str(e)}'}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}

    return result

@api.route('/apm/flow',methods=['post','get'])
def getFlow():
    """获取流量损耗"""
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    deviceId = d.getIdbyDevice(device)
    pid = d.getPid(deviceId=deviceId,pkgName=pkgname)
    if pid:
        try:
            flow = Flow(pkgName=pkgname,deviceId=deviceId)
            send = flow.getUpFlow()
            recv = flow.getDownFlow()
            result = {'status': 1, 'send': send,'recv':recv}
        except Exception as e:
            logger.error(f'Get flow failed:{str(e)}')
            result = {'status': 0, 'msg': f'{str(e)}'}
    else:
        result = {'status': 0, 'msg': f'未发现{pkgname}的进程'}

    return result

@api.route('/apm/create/report',methods=['post','get'])
def makeReport():
    """创建测试报告记录"""
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    app = request.args.get('app')
    devices = request.args.get('devices')
    try:
        file(fileroot=f'apm_{current_time}').make_report(app=app,devices=devices)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0,'msg':str(e)}
    return result

@api.route('/apm/edit/report',methods=['post','get'])
def editReport():
    """编辑测试报告记录"""
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
    """获取apm详细数据"""
    scene = request.args.get('scene')
    target = request.args.get('target')
    try:
        log_data = file().readLog(scene=scene,filename=f'{target}.log')[0]
        result = {'status': 1,'log_data':log_data}
    except Exception as e:
        result = {'status': 0,'msg':str(e)}
    return result

@api.route('/apm/remove/report',methods=['post','get'])
def removeReport():
    """移除测试报告记录"""
    scene = request.args.get('scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    try:
        shutil.rmtree(f'{report_dir}/{scene}', True)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0,'msg':str(e)}
    return result