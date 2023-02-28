<p align="center">
  <a>中文</a> | <a href="./README.md">English</a> | <a href="./DocForAndroid.md">DocForAndroid</a>
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
<a href="https://pypistats.org/packages/solox" target="__blank"><img src="https://img.shields.io/pypi/dm/solox"></a>

<br>
</p>

## 简介

SoloX - Android/iOS性能数据实时采集工具。

我们致力于解决低效、繁琐的测试执行，我们的目标是【Simple Test in SoloX】

<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1662348054846-b0164165-e83a-443e-9a05-8c1f9ddb355f.png?x-oss-process=image%2Fresize%2Cw_1500%2Climit_0"  width="100%" >

## 安装
```
1.Python:3.6+ 
2.pip install -U solox
3.pip install -i  https://mirrors.ustc.edu.cn/pypi/web/simple -U solox (在国内推荐使用镜像下载)

注意: 如果Windows用户需要测试ios，先安装并启动iTunes
```

## 启动SoloX
### 默认
```shell
python -m solox
```
### 自定义

```shell
python -m solox --host={ip} --port=50003
```

## 使用python收集
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

## 使用api收集 
### 1.后台启动服务

```
# solox version >= 2.1.5

macOS/Linux: nohup python3 -m solox &
Windows: start /min python3 -m solox &
```

### 2.通过api请求性能数据
```
http://{ip}:50003/apm/collect?platform=Android&deviceid=ca6bd5a5&pkgname=com.bilibili.app.in&apm_type=cpu

apm_type in ['cpu','memory','network','fps','battery']
```

## 对比模式
- 2-devices: 在两部不同的手机上测试同一个应用
- 2-apps: 在具有相同配置的两部手机上测试两个不同的应用程序

<img src="https://cdn.nlark.com/yuque/0/2022/png/153412/1662348055024-96e38b5e-d6b4-4a06-8070-0707e2fbcd99.png?x-oss-process=image%2Fresize%2Cw_1500%2Climit_0"  width="100%">

## 推荐浏览器

<img src="https://cdn.nlark.com/yuque/0/2023/png/153412/1677553244189-eae85324-fc00-4504-82a0-d669cd0b4c5c.png" alt="Edge" width="24px" height="24px" />
<img src="https://cdn.nlark.com/yuque/0/2023/png/153412/1677553244198-96ce5709-f33f-4038-888f-f330d1f74450.png" alt="Chrome" width="24px" height="24px" />
<img src="https://cdn.nlark.com/yuque/0/2023/png/153412/1677553244204-6fbda427-e143-48eb-9785-cd9bded6e7c0.png" alt="Safari" width="24px" height="24px" />


## 感谢

- https://github.com/alibaba/taobao-iphone-device

## 交流
- Gmail: rafacheninc@gmail.com


