from flask import Flask, render_template
from flask import request
from view.apm import *
from view.common import *
import os
import json
import time
import shutil


app = Flask(__name__,template_folder='templates',static_folder='static')
d = Devices()


@app.route('/')
def index():
    return render_template('index.html',**locals())

@app.route('/report')
def report():
    report_dir = os.path.join(os.getcwd(), 'report')
    dirs = os.listdir(report_dir)
    apm_data = []
    for dir in dirs:
        if dir.split(".")[-1] not in ['log','json']:
            try:
                f = open(f'{report_dir}/{dir}/result.json')
                json_data = json.loads(f.read())
                dict_data = {
                    'scene':dir,
                    'app':json_data['app'],
                    'platform': json_data['platform'],
                    'devices': json_data['devices'],
                    'ctime': json_data['ctime'],
                }
                f.close()
                apm_data.append(dict_data)
            except Exception as e:
                print(e)
                continue
    apm_data_len = len(apm_data)        
    return render_template('report.html',**locals())

@app.route('/analysis',methods=['post','get'])
def analysis():
    scene = request.args.get('scene')
    app = request.args.get('app')
    report_dir = os.path.join(os.getcwd(), 'report')
    dirs = os.listdir(report_dir)
    apm_data = {}
    for dir in dirs:
        if dir == scene:
            try:
                if not os.path.exists(f'{report_dir}/{scene}/apm.json'):
                    cpu_data = file().readLog(scene=scene,filename=f'cpu.log')[1]
                    cpu_rate = f'{round(sum(cpu_data)/len(cpu_data),2)}%'
                    apm_dict = {
                        "cpu":cpu_rate,
                        "mem":"500MB",
                        "fps":"25fps",
                        "flow":"300MB",
                        "bettery":"100MA"
                    }
                    content = json.dumps(apm_dict)
                    with open(f'{report_dir}/{scene}/apm.json', 'a+', encoding="utf-8") as apmfile:
                        apmfile.write(content)
                f = open(f'{report_dir}/{scene}/apm.json')
                json_data = json.loads(f.read())
                apm_data['cpu'] = json_data['cpu']
                apm_data['mem'] = json_data['mem']
                apm_data['fps'] = json_data['fps']
                apm_data['bettery'] = json_data['bettery']
                apm_data['flow'] = json_data['flow']
                f.close()
                break
            except Exception as e:
                print(e)
                break
    return render_template('/analysis.html',**locals())

@app.route('/device/ids',methods=['post','get'])
def deviceids():
    deviceids = d.getDeviceIds()
    devices = d.getDevices()
    pkgnames = d.getPkgname()
    if len(deviceids)>0:
        result = {'status':1,'deviceids':deviceids,'devices':devices,'pkgnames':pkgnames}
    else:
        result = {'status':0,'msg':'no devices'}
    return result

@app.route('/apm/cpu',methods=['post','get'])
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

@app.route('/apm/create/report',methods=['post','get'])
def makeReport():
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    app = request.args.get('app')
    devices = request.args.get('devices')
    file(fileroot=f'apm_{current_time}').make_report(app=app,devices=devices)
    result = {'status': 1}
    return result

@app.route('/apm/edit/report',methods=['post','get'])
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

@app.route('/apm/log',methods=['post','get'])
def getLogData():
    scene = request.args.get('scene')
    target = request.args.get('target')
    try:
        cpu_data = file().readLog(scene=scene,filename=f'{target}.log')[0]
        result = {'status': 1,'cpu_data':cpu_data}
    except Exception as e:
        result = {'status': 0,'msg':str(e)}
    return result


@app.route('/apm/remove/report',methods=['post','get'])
def removeReport():
    scene = request.args.get('scene')
    report_dir = os.path.join(os.getcwd(), 'report')
    try:
        shutil.rmtree(f'{report_dir}/{scene}', True)
        result = {'status': 1}
    except Exception as e:
        result = {'status': 0,'msg':str(e)}
    return result

if __name__ == '__main__':

    app.run(debug=True,host='0.0.0.0',port=5000)