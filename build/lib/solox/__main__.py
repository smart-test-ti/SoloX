from __future__ import absolute_import

from flask import Flask
from .view.apis import api
from .view.pages import page


app = Flask(__name__,template_folder='templates',static_folder='static')
app.register_blueprint(api)
app.register_blueprint(page)

def main():
    app.run(debug=False, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()