from __future__ import absolute_import
from flask import Flask
import webbrowser
import multiprocessing
import requests
from .view.apis import api
from .view.pages import page
from logzero import logger

app = Flask(__name__,template_folder='templates',static_folder='static')
app.register_blueprint(api)
app.register_blueprint(page)

def get_running_status():
    """get solox server status"""
    try:
        r = requests.get(f'http://localhost:5000', timeout=2.0)
        flag = (False,True)[r.status_code == 200]
        return flag
    except requests.exceptions.ConnectionError:
        pass
    except Exception as e:
        logger.error("Unknown error: %r" % e)

def open_url():
    """监听并打开solox启动后的url"""
    flag = True
    while flag:
        flag = get_running_status()
    webbrowser.open(f'http://localhost:5000', new=2)

def start_web():
    """启动solox服务"""
    app.run(debug=False, host='0.0.0.0', port=5000)