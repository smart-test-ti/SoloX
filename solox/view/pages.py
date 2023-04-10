import json
import os
import traceback
from flask import Blueprint
from flask import render_template
from flask import request
from solox.public.common import file,Method
from logzero import logger

page = Blueprint("page", __name__)
m = Method()

@page.app_errorhandler(404)
def page_404(e):
    return render_template('404.html', **locals()), 404


@page.app_errorhandler(500)
def page_500(e):
    return render_template('500.html', **locals()), 500


@page.route('/')
def index():
    platform = request.args.get('platform')
    lan = request.args.get('lan')
    cpuWarning = (0, request.cookies.get('cpuWarning'))[request.cookies.get('cpuWarning') not in [None, 'NaN']]
    memWarning = (0, request.cookies.get('memWarning'))[request.cookies.get('memWarning') not in [None, 'NaN']]
    fpsWarning = (0, request.cookies.get('fpsWarning'))[request.cookies.get('fpsWarning') not in [None, 'NaN']]
    netdataRecvWarning = (0, request.cookies.get('netdataRecvWarning'))[request.cookies.get('netdataRecvWarning') not in [None, 'NaN']]
    netdataSendWarning = (0, request.cookies.get('netdataSendWarning'))[request.cookies.get('netdataSendWarning') not in [None, 'NaN']]
    betteryWarning = (0, request.cookies.get('betteryWarning'))[request.cookies.get('betteryWarning') not in [None, 'NaN']]
    runningTime = (0, request.cookies.get('runningTime'))[request.cookies.get('runningTime') not in [None, 'NaN']]
    solox_host = ('', request.cookies.get('solox_host'))[request.cookies.get('solox_host') not in [None, 'NaN']]
    host_switch = request.cookies.get('host_switch')
    return render_template('index.html', **locals())

@page.route('/pk')
def pk():
    lan = request.args.get('lan')
    model = request.args.get('model')
    return render_template('pk.html', **locals())


@page.route('/report')
def report():
    lan = request.args.get('lan')
    report_dir = os.path.join(os.getcwd(), 'report')
    if not os.path.exists(report_dir):
        os.mkdir(report_dir)
    dirs = os.listdir(report_dir)
    dir_list = reversed(sorted(dirs, key=lambda x: os.path.getmtime(os.path.join(report_dir, x))))
    apm_data = []
    for dir in dir_list:
        if dir.split(".")[-1] not in ['log', 'json']:
            try:
                f = open(f'{report_dir}/{dir}/result.json')
                json_data = json.loads(f.read())
                dict_data = {
                    'scene': dir,
                    'app': json_data['app'],
                    'platform': json_data['platform'],
                    'model': json_data['model'],
                    'devices': json_data['devices'],
                    'ctime': json_data['ctime'],
                }
                f.close()
                apm_data.append(dict_data)
            except Exception:
                traceback.print_exc()
                continue
    apm_data_len = len(apm_data)
    return render_template('report.html', **locals())


@page.route('/analysis', methods=['post', 'get'])
def analysis():
    lan = request.args.get('lan')
    scene = request.args.get('scene')
    app = request.args.get('app')
    platform = request.args.get('platform')
    report_dir = os.path.join(os.getcwd(), 'report')
    dirs = os.listdir(report_dir)
    f = file()
    apm_data = {}
    for dir in dirs:
        if dir == scene:
            try:
                if not os.path.exists(os.path.join(report_dir,scene,'apm.json')):
                    apm_dict = f._setAndroidPerfs(scene) if platform == 'Android' else f._setiOSPerfs(scene)
                    content = json.dumps(apm_dict)
                    with open(os.path.join(report_dir,scene,'apm.json'), 'a+', encoding="utf-8") as apmfile:
                        apmfile.write(content)
                f = open(os.path.join(report_dir,scene,'apm.json'))
                json_data = json.loads(f.read())
                apm_data['cpuAppRate'] = m._setValue(json_data['cpuAppRate'])
                apm_data['cpuSystemRate'] = m._setValue(json_data['cpuSystemRate'])
                apm_data['totalPassAvg'] = m._setValue(json_data['totalPassAvg'])
                apm_data['nativePassAvg'] = m._setValue(json_data['nativePassAvg'])
                apm_data['dalvikPassAvg'] = m._setValue(json_data['dalvikPassAvg'])
                apm_data['fps'] = m._setValue(json_data['fps'])
                apm_data['jank'] = m._setValue(json_data['jank'])
                apm_data['flow_send'] = m._setValue(json_data['flow_send'])
                apm_data['flow_recv'] = m._setValue(json_data['flow_recv'])
                if platform == 'Android':
                    apm_data['batteryLevel'] = m._setValue(json_data['batteryLevel'])
                    apm_data['batteryTeml'] = m._setValue(json_data['batteryTeml'])
                else:
                    apm_data['batteryTeml'] = m._setValue(json_data['batteryTeml'])
                    apm_data['batteryCurrent'] = m._setValue(json_data['batteryCurrent'])
                    apm_data['batteryVoltage'] = m._setValue(json_data['batteryVoltage'])
                    apm_data['batteryPower'] = m._setValue(json_data['batteryPower'])
                    apm_data['gpu'] = m._setValue(json_data['gpu'])
                f.close()
            except ZeroDivisionError:
                pass    
            except Exception:
                traceback.print_exc()
            finally:
                break
    return render_template('analysis.html', **locals())

@page.route('/pk_analysis', methods=['post', 'get'])
def analysis_pk():
    lan = request.args.get('lan')
    scene = request.args.get('scene')
    app = request.args.get('app')
    model = request.args.get('model')
    report_dir = os.path.join(os.getcwd(), 'report')
    dirs = os.listdir(report_dir)
    f = file()
    apm_data = {}
    for dir in dirs:
        if dir == scene:
            try:
                if not os.path.exists(os.path.join(report_dir,scene,'apm.json')):
                    apm_dict = f._setpkPerfs(scene)
                    content = json.dumps(apm_dict)
                    with open(os.path.join(report_dir,scene,'apm.json'), 'a+', encoding="utf-8") as apmfile:
                        apmfile.write(content)
                f = open(os.path.join(report_dir,scene,'apm.json'))
                json_data = json.loads(f.read())
                apm_data['cpuAppRate1'] = json_data['cpuAppRate1']
                apm_data['cpuAppRate2'] = json_data['cpuAppRate2']
                apm_data['totalPassAvg1'] = json_data['totalPassAvg1']
                apm_data['totalPassAvg2'] = json_data['totalPassAvg2']
                apm_data['network1'] = json_data['network1']
                apm_data['network2'] = json_data['network2']
                apm_data['fpsAvg1'] = json_data['fpsAvg1']
                apm_data['fpsAvg2'] = json_data['fpsAvg2']
                f.close()
            except Exception:
                traceback.print_exc()
            finally:
                break
    return render_template('analysis_pk.html', **locals())
