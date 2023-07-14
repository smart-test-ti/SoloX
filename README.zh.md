<p align="center">
  <a>中文</a> | <a href="./README.md">English</a> | <a href="./FAQ.md">FAQ</a>
</p>

<p align="center">
<a href="#">
<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1643364757640-b4529458-ec8d-42cc-a2d8-c0ce60fdf50f.png" alt="SoloX" width="150">
</a>
<br>
<br>

</p>
<p align="center">
<a href="https://pypi.org/project/solox/" target="__blank"><img src="https://img.shields.io/pypi/v/solox" alt="solox preview"></a>
<a href="https://pepy.tech/project/solox" target="__blank"><img src="https://static.pepy.tech/personalized-badge/solox?period=total&units=international_system&left_color=grey&right_color=orange&left_text=downloads"></a>
<br>
</p>

## 🔎简介

SoloX - Android/iOS性能数据的实时采集工具。

我们致力于解决低效、繁琐的测试执行问题，我们的目标是在【Simple Test In SoloX】

![preview](https://github.com/smart-test-ti/SoloX/assets/24454096/79964f92-de3a-435f-b6ab-3d39ac8da425)

## 📦环境

- 安装 Python 3.10 + [**Download**](https://www.python.org/downloads/)
- 安装 adb和配置好环境变量 (SoloX自带的adb不一定适配你的电脑，建议自己安装) [**Download**](https://developer.android.com/studio/releases/platform-tools)

💡 Python 3.6 ~ 3.9 , 请安装solox版本低于2.5.4.

💡 如果Windows用户需要测试iOS，请先安装Itunes. [**参考**](https://github.com/alibaba/taobao-iphone-device)

## 📥安装

### 默认

```shell
pip install -U solox (指定版本：pip install solox==2.6.8)
```

### 镜像

```shell
pip install -i  https://mirrors.ustc.edu.cn/pypi/web/simple -U solox
```

💡 如果你的网络无法通过 [pip install -U solox] 下载, 可以尝试使用镜像下载，但是可能不是最新版本.

## 🚀启动

### 默认

```shell
python -m solox
```

### 自定义

```shell
python -m solox --host={ip} --port={port}
```

## 🏴󠁣󠁩󠁣󠁭󠁿使用python收集

```python

from solox.public.apm import APM
from solox.public.common import Devices

d = Devices()
pids = d.getPid(deviceId='ca6bd5a5', pkgName='com.bilibili.app.in') # for android

apm = APM(pkgName='com.bilibili.app.in',platform='Android', deviceId='ca6bd5a5', 
          surfaceview=True, noLog=True, pid=None)
# apm = APM(pkgName='com.bilibili.app.in', platform='iOS') only supports one device
# surfaceview： False = gfxinfo (手机开发者 - GPU渲染模式 - adb shell dumpsys gfxinfo)
# noLog : False (为false时才会存储测试数据到log文件中)

# ************* 收集单个性能指标 ************* #
cpu = apm.collectCpu() # %
memory = apm.collectMemory() # MB
flow = apm.collectFlow(wifi=True) # KB
fps = apm.collectFps() # HZ
battery = apm.collectBattery() # level:% temperature:°C current:mA voltage:mV power:w
gpu = apm.collectGpu() # % only supports ios

# ************* 收集全部的性能指标 ************* #
apm = APM(pkgName='com.bilibili.app.i',platform='Android', deviceId='ca6bd5a5', 
          surfaceview=True, noLog=False, pid=None, duration=20) # duration : 秒 （持续执行时间）
# apm = APM(pkgName='com.bilibili.app.in', platform='iOS',  noLog=False, duration=20)  
if __name__ == '__main__':
     apm.collectAll() # 会生成HTML报告
```

## 🏴󠁣󠁩󠁣󠁭󠁿使用API收集

### 后台启动服务

```
# solox version >= 2.1.5

macOS/Linux: nohup python3 -m solox &
Windows: start /min python3 -m solox &
```

### 通过api请求数据

```shell
Android: http://{ip}:{port}/apm/collect?platform=Android&deviceid=ca6bd5a5&pkgname=com.bilibili.app.in&target=cpu
iOS: http://{ip}:{port}/apm/collect?platform=iOS&pkgname=com.bilibili.app.in&target=cpu

target in ['cpu','memory','network','fps','battery','gpu']
```

## 🔥功能

* **无需ROOT/越狱:** Android设备无需ROOT，iOS设备无需越狱。高效解决Android & iOS性能测试分析难题。
* **数据完整性:** 可提供FPS、Jank、CPU、GPU、Memory、Battery 、Network等性能参数，这些您都可以轻松获得。
* **美观的报告看板:** 报告看板，您可以随时随地存储、可视化、编辑、管理和下载使用任何版本的SoloX收集的所有测试数据。
* **好用的监控设置:** 支持在监控过程中设置告警值、收集时长、访问其他PC机器的移动设备。
* **比对模式:** 支持两台移动设备同时对比测试。

  - 🌱2-devices: 使用两台不同的设备测试同一个app。
  - 🌱2-apps: 使用两台配置相同的设备测试两个不同的app。
* **API收集性能数据:** 支持python、API收集性能数据，帮助用户轻松集成在CI/CD流程。

## 浏览器

<img src="https://cdn.nlark.com/yuque/0/2023/png/153412/1677553244198-96ce5709-f33f-4038-888f-f330d1f74450.png" alt="Chrome" width="50px" height="50px" />

## 终端

- windows: PowerShell
- macOS：iTerm2 (https://iterm2.com/)

## 💕感谢

- https://github.com/alibaba/taobao-iphone-device
