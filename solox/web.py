from __future__ import absolute_import
import multiprocessing
import subprocess
import time
import os
import platform
import re
import webbrowser
import requests
import socket
import sys
import traceback
from solox.view.apis import api
from solox.view.pages import page
from logzero import logger
from threading import Lock
from flask_socketio import SocketIO, disconnect
from flask import Flask

app = Flask(__name__, template_folder='templates', static_folder='static')
app.register_blueprint(api)
app.register_blueprint(page)

socketio = SocketIO(app, cors_allowed_origins="*")
thread = True
thread_lock = Lock()


@socketio.on('connect', namespace='/logcat')
def connect():
    socketio.emit('start connect', {'data': 'Connected'}, namespace='/logcat')
    if not os.path.exists('adblog'):
        os.mkdir('adblog')
    global thread
    thread = True
    with thread_lock:
        if thread:
            thread = socketio.start_background_task(target=backgroundThread)


def backgroundThread():
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
def disconnect():
    global thread
    logger.warning('Logcat client disconnected')
    thread = False
    disconnect()


def checkPyVer():
    versions = platform.python_version().split('.')
    if int(versions[0]) < 3:
        logger.error('python version must be 3.10+ ,your python version is {}'.format(platform.python_version()))
        sys.exit()
    elif int(versions[1]) < 10:
        logger.error('python version must be 3.10+ ,your python version is {}'.format(platform.python_version()))
        sys.exit()

def hostIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception as e:
        raise e
    finally:
        s.close()
    return ip


def listeningPort(port):
    if platform.system() != 'Windows':
        os.system("lsof -i:%s| grep LISTEN| awk '{print $2}'|xargs kill -9" % port)
    else:
        port_cmd = 'netstat -ano | findstr {}'.format(port)
        r = os.popen(port_cmd)
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


def getServerStatus(host: str, port: int):
    r = requests.get('http://{}:{}'.format(host, port), timeout=2.0)
    flag = (True, False)[r.status_code == 200]
    return flag


def openUrl(host: str, port: int):
    flag = True
    while flag:
        logger.info('start solox server')
        flag = getServerStatus(host, port)
    webbrowser.open('http://{}:{}/?platform=Android&lan=en'.format(host, port), new=2)
    logger.info('Running on http://{}:{}/?platform=Android&lan=en (Press CTRL+C to quit)'.format(host, port))


def startServer(host: str, port: int):
    socketio.run(app, host=host, debug=False, port=port)


def main(host=hostIP(), port=50003):
    try:
        listeningPort(port=port)
        pool = multiprocessing.Pool(processes=2)
        pool.apply_async(startServer, (host, port))
        pool.apply_async(openUrl, (host, port))
        pool.close()
        pool.join()
    except Exception:
        traceback.print_exc()
    except KeyboardInterrupt:
        logger.info('stop solox success')
        sys.exit()
