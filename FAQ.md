## 1️⃣ SoloX和Perfdog对比 ？

优势

* 功能更加丰富：PK模式、设置执行时长、访问其他PC端的移动设备、丰富的本地化报告展现和分发。
* 使用更加灵活：自定义部署、支持api收集更好的融入CI流程。
* 免费：开源代码，如果不满足你现在需求，可以自由二次开发（perfdog很贵，但是品质值得）。

劣势

* 数据准确性不足：perfdog采用的方式是安装一个监听app在测试设备上，用原生的api收集性能数据再返回给工具端，这种方式肯定是更靠谱的（数据准确才是最重要的，条件允许我建议使用perfdog）

## 2️⃣ 如何使用SoloX ?

1. 点击Connect连接移动设备（第一次会自动连接，如果选择框显示了设备信息表示连接成功）。
2. 选择需要测试的包名。
3. 选择包名对应的进程（一个app有可能有多个进程，比如微信小程序，如果没有进程说明这个app没有在运行）。
4. 点击Start开始收集性能指标。
5. 点击Stop结束收集，生成报告跳转到报告管理页。

## 3️⃣ 性能指标计算方法 ?

* Android：[https://github.com/smart-test-ti/SoloX/blob/master/DocForAndroid.md]()
* iOS：[https://github.com/alibaba/taobao-iphone-device](https://github.com/alibaba/taobao-iphone-device)

## 4️⃣ 为什么手机已经连接电脑，但是还是显示连接失败 ？

* Android：使用的是adb连接，solox自带有adb环境，但不一定适配每一台电脑；可以在自己的终端敲打adb devices测试是否连接上设备。
* iOS：使用的是tidevice连接，如果连接失败可以参考官方文档（[https://github.com/alibaba/taobao-iphone-device](https://github.com/alibaba/taobao-iphone-device)）

## 5️⃣ 为什么Android的FPS经常会为0 ？

* 支持SurfaceView和gfxinfo（界面关闭surfaceview开关切换）两种方式，可以都切换尝试是否收集到数据；如果使用gfxinfo方式需要到手机设置：开发者 - GPU渲染模式 - adb shell dumpsys gfxinfo。
* 界面相对静止的fps预期就是0，请检查页面是否滑动和动态。
* 游戏类的APP大部分机器不支持，多使用华为的机器。

## 6️⃣ 为什么"python -m solox"会运行失败 ？

* solox 2.5.4及以上版本只支持python 3.10 +的版本（因为使用了python新的特性，3.10以下版本不支持），2.5.3及以下版本支持python3.0 ~3.9。
* 如果显示的是50003端口被占用，可以用自定义的方式启动  `python -m solox --host={ip} --port={port}` 。
* socket.gaierror: [Errno 8] nodename nor servname provided, or not known ：https://github.com/smart-test-ti/SoloX/issues/198

## 7️⃣ 为什么感觉收集速度慢 ？

* 界面收集每个指标都会起一个进程来达到同时收集的目的；基本上PC的配置跟的上，速度没有太大问题；但是不同指标计算复杂度决定了速度，比如cpu计算+读取数据的时间最少是3秒，而电池的数据基本不需要计算就是秒回。
* 可以在勾选掉部分指标，也会达到加快速度的效果。
* 使用python api收集，会比界面的速度有明显的提升。

## 8️⃣ 如何无线连接设备 ？

* Android：pc和移动设备需要在同一个网络，然后通过adb connect的方式设置成功后，无须usb连接在solox界面点击connect就会看到设备；具体方式可以网上查，很多教程。
* iOS：不支持。

## 9️⃣ 如何部署SoloX ？

核心就是让“python -m solox”这条命令在后台执行就可以。有很多种方式nohup、docker、Gunicorn等（可以网上查）

最简单的就是“nohup python -m solox &”。

## 1️⃣0️⃣ SoloX部署在云机器，远程访问本地的移动设备 ？

需要在连接移动设备的PC机器起solox的服务，然后将host配置在SoloX设置页的Anget中（右上角红点的设置按钮可查看）；

可以不用在同一个局域网，但是要保证本地的网络防火墙是放开的，可以让云机器访问。

## 1️⃣1️⃣ SoloX如何获取微信小程序的性能 ？

在进程选择框中找到appbrand开头的进程就小程序的，选中该进程点击Start即可收集。

## 1️⃣2️⃣ Start-up Time如何使用 ？

* Android：首先打开目标app的启动到达界面，接着在Start-up Time弹窗点击按钮“Get current activity"。如果要测试热启动就直接点Start按钮，如果测试冷启动就杀掉app点击Start按钮。
* iOS：事先要装好模块“pip install py-ios-device”，然后点击Start（由于windows安装会报错，解决繁琐，solox没有自带该模块）。

## 1️⃣3️⃣ 为什么分析页截图会出现明显的遮层 ？

这个和浏览器有关，调用的是浏览器的截图功能。

## 1️⃣4️⃣ 分析页显示流量数据汇总值和Chart图中有出入 ？

头部汇总的数据是根据记录结束和开始数据的差值得到的，chart中的数据也是准确的，表示的是记录那一秒的流量损耗，但不是每一秒都有记录，所以用chart中相加的话会少于实际总损耗。

## 1️⃣5️⃣ 为什么Android和iOS的电池统计指标不一致 ？

* Android：基本上新版本的系统已经不能通过adb的方式拿到能耗数据了，目前提供电量和温度两个指标其实已经足够；电量收集时solox会在执行前断开充电，执行结束才恢复充电。
* iOS：选择能耗的方式来评估性能，这里可能会觉得充电会影响，但是我们测试是要和竞品对比，在相同条件下对比能耗即可，无需关注充电的影响。

## 1️⃣6️⃣ 如果iOS收集不到数据显示tidevice报错，怎么解决 ？

* 插拔usb重新连接，多次尝试。
* 更换设备，tidevice还是有一定的兼容性。
* 检查tidevice的版本，不能自己安装最新版本，只能用solox自带的，因为部分代码二次开发过。
* 如果日志中提示是支持包下载失败，可以自行到（https://github.com/filsv/iOSDeviceSupport）这里下载放到这个路径 ~/.tidevice/device-support/

## 1️⃣7️⃣ 为什么Android不支持收集GPU数据？

目前只支持部分高通芯片的设备（小米、oppo、vivo多点）。

## 1️⃣8️⃣ 如何在收集过程种录制APP的屏幕？

* 目前支持Android端。
* 界面收集：在首页打开“Record Screen”开关，点击Start开始收集数据并同时录制视频，结束后Report管理页会显示播放按钮。
* Python API收集：record=True。
* Mac电脑录制视频，请检查Scrcpy是否安装成功，可以自行安装：brew install scrcpy。

## 1️⃣9️⃣ Android哪些指标依赖app的进程需要存活？

* Cpu、Memory、Network、FPS
* 界面如果不选择进程就点击Start收集，那么默认使用的是这个包名的主进程。
* 界面选择了app的某个进程收集，如果收集过程中将app杀掉，然后再恢复后自动使用的是主进程，有可能和你界面选择的进程不一致。

## 2️⃣0️⃣ Android/iOS最高支持的系统版本？

- Android: 6.0+
- iOS: https://github.com/filsv/iOSDeviceSupport，这个路径有的都支持，因为是外网可能会下载失败，可以自行下载支持包放在本地~/.tidevice/device-support/
