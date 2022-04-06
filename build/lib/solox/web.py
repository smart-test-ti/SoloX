from __future__ import absolute_import

import platform
import re
from flask import Flask
import webbrowser
import requests
from .view.apis import api
from .view.pages import page
from logzero import logger
from threading import Lock
from flask_socketio import SocketIO, disconnect
import multiprocessing
import subprocess
import time
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.register_blueprint(api)
app.register_blueprint(page)

socketio = SocketIO(app, cors_allowed_origins="*")
thread = True
thread_lock = Lock()


@socketio.on('connect', namespace='/logcat')
def test_connect():
    socketio.emit('start connect', {'data': 'Connected'}, namespace='/logcat')
    if not os.path.exists('adblog'):
        os.mkdir('adblog')
    global thread
    thread = True
    with thread_lock:
        if thread:
            thread = socketio.start_background_task(target=background_thread)


def background_thread():
    global thread
    try:
        current_time = time.strftime("%Y%m%d%H", time.localtime())
        logcat = subprocess.Popen(f'adb logcat *:E > ./adblog/{current_time}_adb.log', stdout=subprocess.PIPE,
                                  shell=True)
        file = f"./adblog/{current_time}_adb.log"
        with open(file, "r") as f:
            while thread:
                socketio.sleep(1)
                for line in f.readlines():
                    socketio.emit('message', {'data': line}, namespace='/logcat')
        if logcat.poll() == 0:
            thread = False
    except Exception:
        pass


@socketio.on('disconnect_request', namespace='/logcat')
def disconnect_request():
    global thread
    logger.warning('Logcat client disconnected')
    thread = False
    disconnect()


def check_port(port):
    """
    Detect whether the port is occupied and clean up
    :param port: System port
    :return: None
    """
    if platform.system() != 'Windows':
        os.system("lsof -i:%s| grep LISTEN| awk '{print $2}'|xargs kill -9" % port)
    else:
        port_cmd = 'netstat -ano | findstr {}'.format(port)
        r = os.popen(port_cmd)
        # 获取5000端口的程序的pid，先保存在一个列表中，后面需要用，
        # 否则后面调用读取，指针会到末尾，会造成索引越界
        r_data_list = r.readlines()
        if len(r_data_list) == 0:
            return
        else:
            pid_list = []
            for line in r_data_list:
                line = line.strip()
                pid = re.findall(r'[1-9]\d*', line)
                pid_list.append(pid[-1])
            pid_set = list(set(pid_list))[0]
            pid_cmd = 'taskkill -PID {} -F'.format(pid_set)
            os.system(pid_cmd)


def get_running_status():
    """get solox server status"""
    try:
        r = requests.get(f'http://localhost:5000', timeout=2.0)
        flag = (False, True)[r.status_code == 200]
        return flag
    except requests.exceptions.ConnectionError:
        pass
    except Exception:
        pass


def open_url():
    """监听并打开solox启动后的url"""
    flag = True
    while flag:
        logger.info('Start solox server...')
        flag = get_running_status()
    webbrowser.open(f'http://localhost:5000', new=2)
    logger.info('Running on http://localhost:5000 (Press CTRL+C to quit)')


def start_web():
    """启动solox服务"""
    socketio.run(app, host='0.0.0.0', debug=False, port=5000)
    # app.run(debug=False, host='0.0.0.0', port=5000)


def main():
    try:
        check_port(port=5000)
        pool = multiprocessing.Pool(processes=2)
        pool.apply_async(start_web)
        pool.apply_async(open_url)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        logger.info('Stop solox server success')
