from flask import Flask, render_template
from flask import request

app = Flask(__name__,template_folder='templates',static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/analysis',methods=['post','get'])
def analysis():
    id = request.args.get('id')
    return render_template('/analysis.html',**locals())

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)