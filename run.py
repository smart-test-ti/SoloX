from unittest import result
from flask import Flask, render_template
from flask import request
from view.common import *
from view.apm import *
import random
import os
import json
import time


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
        if dir.split(".")[-1] != "log":
            try:
                f = open(f'{report_dir}/{dir}/result.json')
                json_data = json.loads(f.read())
                dict_data = {
                    'scene':dir,
                    'app':json_data['app'],
                    'platform': json_data['platform'],
                    'devices': json_data['devices'],
                    'cpu': json_data['cpu'],
                    'mem': json_data['mem'],
                    'fps': json_data['fps'],
                    'bettery': json_data['bettery'],
                    'flow': json_data['flow'],
                    'ctime': json_data['ctime'],
                }
                f.close()
                apm_data.append(dict_data)
            except Exception as e:
                print(e)
                continue
    return render_template('report.html',**locals())

@app.route('/analysis',methods=['post','get'])
def analysis():
    scene = request.args.get('scene')
    app = request.args.get('app')
    return render_template('/analysis.html',**locals())

@app.route('/device/ids',methods=['post','get'])
def deviceids():

    deviceids = d.getDeviceIds()
    devices = d.getDevices()
    pkgnames = d.getPkgname()
    time.sleep(2)
    if len(deviceids)>0:
        result = {'status':1,'deviceids':deviceids,'devices':devices,'pkgnames':pkgnames}
    else:
        result = {'status':0,'msg':'no devices'}
    return result

@app.route('/apm/cpu',methods=['post','get'])
def getCpuRate():
    pkgname = request.args.get('pkgname')
    device = request.args.get('device')
    # deviceId = d.getIdbyDevice(device)
    if pkgname and device:
        cpu = CPU(pkgName='s',deviceId='s')
        # cpuRate = cpu.getSingCpuRate()
        result = {'status': 1, 'cpuRate': random.randint(50, 200)}
    else:
        result = {'status': 0, 'msg': '未选择设备或者不包名'}

    return result

@app.route('/apm/create/report',methods=['post','get'])
def makeReport():
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    file(fileroot=f'apm_{current_time}').make_report()
    result = {'status': 1}
    return result


if __name__ == '__main__':

    app.run(debug=True,host='0.0.0.0',port=5000)