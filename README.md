<p align="center">
<a href="#">
<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1643364757640-b4529458-ec8d-42cc-a2d8-c0ce60fdf50f.png" alt="SoloX" width="300">
</a>
<br>
<br>
</p>
<p align="center">
<a href="https://pypi.org/project/solox/" target="__blank"><img src="https://img.shields.io/pypi/v/solox" alt="solox preview"></a>
<br>
</p>

## SoloX

SoloX - Real-time collection tool for Android/iOS performance data.

We are committed to solving inefficient, cumbersome test execution, and our goal is Simple Test In SoloX!


## Installation
```
1.Python:3.6+ 
2.pip3 install -U solox
```

## Run locally
### default
>the startup host and port defaults to 0.0.0.0 and 50003.

```
   python3 -m solox

 * Serving Flask app 'run' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on all addresses.
   WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://0.0.0.0:50003/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 906-499-328

```

### custom
>custom startup host and port, support command line input.

```shell
python3 -m solox --host=0.0.0.0 --port=50003
```
## Features
#### Home
<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1659519461516-871ecf61-4745-4c92-bf01-96fe0f7be560.png?x-oss-process=image%2Fresize%2Cw_1500%2Climit_0"  width="100%">


#### Error Log
<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1659519461659-555b7fe9-b4c1-44dc-b1f8-7ae9a9595150.png?x-oss-process=image%2Fresize%2Cw_1500%2Climit_0"  width="100%">


#### Report
<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1648879616511-15f271b7-2761-43c5-a86c-50f82bc68f32.png?x-oss-process=image%2Fresize%2Cw_1500%2Climit_0"  width="100%">

#### Analysis
<img src="https://user-images.githubusercontent.com/29191106/174444708-70621044-f836-446f-852f-05925e60cada.png"  width="100%">


## Thanks
- https://github.com/alibaba/mobileperf

- https://github.com/alibaba/taobao-iphone-device
