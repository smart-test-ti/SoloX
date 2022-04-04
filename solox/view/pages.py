from . import *

page = Blueprint("page",__name__)

@page.app_errorhandler(404)
def page_404(e):
    return render_template('404.html',**locals()),404

@page.app_errorhandler(500)
def page_500(e):
    return render_template('500.html',**locals()),500

@page.route('/')
def index():
    return render_template('index.html',**locals())

@page.route('/report')
def report():
    report_dir = os.path.join(os.getcwd(), 'report')
    if not os.path.exists(report_dir):
        os.mkdir(report_dir)
    dirs = os.listdir(report_dir)
    apm_data = []
    for dir in dirs:
        logger.info(dir)
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
    logger.info(apm_data_len)
    return render_template('report.html',**locals())

@page.route('/analysis',methods=['post','get'])
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
                    mem_data = file().readLog(scene=scene, filename=f'mem.log')[1]
                    mem_avg = f'{round(sum(mem_data)/len(mem_data),2)}MB'
                    flow_send_data = file().readLog(scene=scene, filename=f'upflow.log')[1]
                    flow_send_data_all = f'{round(flow_send_data[len(flow_send_data)-1] - flow_send_data[0],2)}MB'
                    flow_recv_data = file().readLog(scene=scene, filename=f'downflow.log')[1]
                    flow_recv_data_all = f'{round(flow_recv_data[len(flow_recv_data)-1] - flow_recv_data[0],2)}MB'
                    apm_dict = {
                        "cpu":cpu_rate,
                        "mem":mem_avg,
                        "fps":"25fps",
                        "flow_send":flow_send_data_all,
                        "flow_recv":flow_recv_data_all,
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
                apm_data['flow_send'] = json_data['flow_send']
                apm_data['flow_recv'] = json_data['flow_recv']
                f.close()
                break
            except Exception as e:
                traceback.print_exc()
                break
    return render_template('/analysis.html',**locals())