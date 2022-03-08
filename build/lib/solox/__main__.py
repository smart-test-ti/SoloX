from __future__ import absolute_import
import webbrowser
import multiprocessing
import requests
from flask import Flask
from .view.apis import api
from .view.pages import page


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
        print("Unknown error: %r" % e)

def open_url():
    """monitor solox status and open url"""
    flag = True
    while flag:
        flag = get_running_status()
    webbrowser.open(f'http://localhost:5000', new=2)

def start_web():
    """start solox web service"""
    app.run(debug=False, host='0.0.0.0', port=5000)


def main():
    try:
        pool = multiprocessing.Pool(processes=2)
        pool.apply_async(start_web)
        pool.apply_async(open_url)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print('stop solox success')


if __name__ == '__main__':
    main()

