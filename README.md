<p align="center">
  <a>English</a> | <a href="./README.zh.md">中文</a> | <a href="./FAQ.md">FAQ</a> | <a href="https://mp.weixin.qq.com/s?__biz=MzkxMzYyNDM2NA==&mid=2247484506&idx=1&sn=b7eb6de68f84bed03001375d08e08ce9&chksm=c17b9819f60c110fd14e652c104237821b95a13da04618e98d2cf27afa798cb45e53cf50f5bd&token=1402046775&lang=zh_CN&poc_token=HKmRi2WjP7gf9CVwvLWQ2cRhrUR3wmbB9-fNZdD4" target="__blank">使用文档</a>
</p>

<p align="center">
<a href="#">
<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1643364757640-b4529458-ec8d-42cc-a2d8-c0ce60fdf50f.png" alt="SoloX" width="130">
</a>
<br>
</p>
<p align="center">
<a href="https://pypi.org/project/solox/" target="__blank"><img src="https://img.shields.io/pypi/v/solox" alt="solox preview"></a>
<a href="https://pepy.tech/project/solox" target="__blank"><img src="https://static.pepy.tech/personalized-badge/solox?period=total&units=international_system&left_color=grey&right_color=orange&left_text=downloads"></a>

<br>
</p>

## 🔎Preview

SoloX - Real-time collection tool for Android/iOS performance data.

We are committed to solving inefficient, cumbersome test execution, and our goal is Simple Test In SoloX!

![10 37 192 142_50003__platform=Android lan=en](https://github.com/smart-test-ti/SoloX/assets/24454096/5b33183c-dcf3-48b7-8c91-dfe20bff3d5c)

## 📦Requirements

- Install Python 3.10 + [**Download**](https://www.python.org/downloads/)
- Install adb and configure environment variables (SoloX's  adb may not necessarily fit your computer) [**Download**](https://developer.android.com/studio/releases/platform-tools)

💡 Python 3.6 ~ 3.9 , please download a version of solox lower than 2.5.4.

💡 If Windows users need to test ios, install and start Itunes. [**Documentation**](https://github.com/alibaba/taobao-iphone-device)

## 📥Installation

### default

```shell
pip install -U solox    (pip install solox=={version})
```

### mirrors

```shell
pip install -i  https://mirrors.ustc.edu.cn/pypi/web/simple -U solox
```

💡 If your network is unable to download through [pip install -U solox], please try using mirrors to download, but the download of SoloX may not be the latest version.

## 🚀Quickstart

### default

```shell
python -m solox
```

### customize

```shell
python -m solox --host={ip} --port={port}
```

## 🏴󠁣󠁩󠁣󠁭󠁿Collect in python

```python
# solox version : >= 2.8.5
from solox.public.apm import AppPerformanceMonitor
from solox.public.common import Devices

d = Devices()
processList = d.getPid(deviceId='ca6bd5a5', pkgName='com.bilibili.app.in') # for android
print(processList) # ['{pid}:{packagename}',...]

apm = AppPerformanceMonitor(pkgName='com.bilibili.app.in',platform='Android', deviceId='ca6bd5a5', surfaceview=True, 
                            noLog=False, pid=None, record=False, collect_all=False, duration=0)
# apm = AppPerformanceMonitor(pkgName='com.bilibili.app.in', platform='iOS') only supports one device
# surfaceview： False = gfxinfo (Developer - GPU rendering mode - adb shell dumpsys gfxinfo)
# noLog : False (Save test data to log file)

# ************* Collect a performance parameter ************* #
cpu = apm.collectCpu() # %
memory = apm.collectMemory() # MB
memory_detail = apm.collectMemoryDetail() # MB
network = apm.collectNetwork(wifi=True) # KB
fps = apm.collectFps() # HZ
battery = apm.collectBattery() # level:% temperature:°C current:mA voltage:mV power:w
gpu = apm.collectGpu() # % only supports ios

# ************* Collect all performance parameter ************* #
 
if __name__ == '__main__':
  apm = AppPerformanceMonitor(pkgName='com.bilibili.app.in',platform='Android', deviceId='ca6bd5a5', surfaceview=True, 
                              noLog=False, pid=None, record=False, collect_all=True, duration=0)
  # apm = AppPerformanceMonitor(pkgName='com.bilibili.app.in', platform='iOS',  deviceId='xxxx', noLog=False, record=False, collect_all=True, duration=0)
  #duration: running time (second)
  #record: record android screen
  apm.collectAll() # will generate HTML report

# in other python file
from solox.public.apm import initPerformanceService  

initPerformanceService.stop() # stop solox
```

## 🏴󠁣󠁩󠁣󠁭󠁿Collect in API

### Start the service in the background

```
# solox version >= 2.1.5

macOS/Linux: nohup python3 -m solox &
Windows: start /min python3 -m solox &
```

### Request apm data from api

```shell
Android: http://{ip}:{port}/apm/collect?platform=Android&deviceid=ca6bd5a5&pkgname=com.bilibili.app.in&target=cpu
iOS: http://{ip}:{port}/apm/collect?platform=iOS&pkgname=com.bilibili.app.in&target=cpu

target in ['cpu','memory','memory_detail','network','fps','battery','gpu']
```

## 🔥Features

* **No ROOT/Jailbreak:** No need of Root for Android devices, Jailbreak for iOS devices. Efficiently solving the test and analysis challenges in Android & iOS performance.
* **Data Integrality:** We provide the data about CPU, GPU, Memory, Battery, Network,FPS, Jank, etc., which you may easy to get.
* **Beautiful Report:** A beautiful and detailed report analysis, where to store, visualize, edit, manage, and download all the test cases collected with SoloX no matter where you are or when is it.
* **Useful Monitoring Settings:** Support setting alarm values, collecting duration, and accessing mobile devices on other PC machines during the monitoring process.
* **PK Model:** Supports simultaneous comparative testing of two mobile devices.

  - 🌱2-devices: test the same app on two different phones.
  - 🌱2-apps: test two different apps on two phones with the same configuration.
* **Collect In Python/API:** Support Python and API to collect performance data, helping users easily integrate into automated testing processes.

## Develop

* https://github.com/pallets/flask
* https://github.com/tabler/tabler

#### debug

* remove [solox] moudel in all python file

```python

example
from solox.view.apis import api  
change to 
from view.apis import api

```
* run [python ./solox/debug.py]

```python
cd solox
python debug.py
```

## Browser

<img src="https://cdn.nlark.com/yuque/0/2023/png/153412/1677553244198-96ce5709-f33f-4038-888f-f330d1f74450.png" alt="Chrome" width="50px" height="50px" />

## Terminal

- windows: PowerShell
- macOS：iTerm2 (https://iterm2.com/)

## 💕Thanks

- https://github.com/alibaba/taobao-iphone-device
- https://github.com/Genymobile/scrcpy
