<p align="center">
  <a>English</a> | <a href="./README.zh.md">中文</a> | <a href="./DocForAndroid.md">DocForAndroid</a>
</p>

<p align="center">
<a href="#">
<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1643364757640-b4529458-ec8d-42cc-a2d8-c0ce60fdf50f.png" alt="SoloX" width="250">
</a>
<br>
<br>

</p>
<p align="center">
<a href="https://pypi.org/project/solox/" target="__blank"><img src="https://img.shields.io/pypi/v/solox" alt="solox preview"></a>
<a href="https://pypistats.org/packages/solox" target="__blank"><img src="https://img.shields.io/pypi/dm/solox"></a>

<br>
</p>

## Preview

SoloX - Real-time collection tool for Android/iOS performance data.

We are committed to solving inefficient, cumbersome test execution, and our goal is Simple Test In SoloX!

<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1662348054846-b0164165-e83a-443e-9a05-8c1f9ddb355f.png?x-oss-process=image%2Fresize%2Cw_1500%2Climit_0"  width="100%" >

## Installation
```
1.Python:3.6+ 
2.pip3 install -U solox

notice: If Windows users need to test ios, install and start Itunes
```

## Startup SoloX
### default
```shell
python3 -m solox
```
### customize

```shell
python3 -m solox --host=0.0.0.0 --port=50003
```

## Collect in python 
```python
from solox.public.apm import APM
# solox version >= 2.1.2

apm = APM(pkgName='com.bilibili.app.in',deviceId='ca6bd5a5',platform='Android')
# apm = APM(pkgName='com.bilibili.app.in', platform='iOS') only supports one device
cpu = apm.collectCpu() # %
memory = apm.collectMemory() # MB
flow = apm.collectFlow() # KB
fps = apm.collectFps() # HZ
battery = apm.collectBattery() # level:% temperature:°C
```

## Collect in API 
### Start the service in the background

```
# solox version >= 2.1.5

macOS/Linux: nohup python3 -m solox &
Windows: start /min python3 -m solox &
```

### Request apm data from api
```
http://{ip}:50003/apm/collect?platform=Android&deviceid=ca6bd5a5&pkgname=com.bilibili.app.in&apm_type=cpu

apm_type in ['cpu','memory','network','fps','battery']
```

## PK Model
- 2-devices: test the same app on two different phones
- 2-apps: test two different apps on two phones with the same configuration

<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1662348055024-96e38b5e-d6b4-4a06-8070-0707e2fbcd99.png?x-oss-process=image%2Fresize%2Cw_1500%2Climit_0"  width="100%">


## Thanks

- https://github.com/alibaba/taobao-iphone-device

## Communicate
- Gmail: rafacheninc@gmail.com

