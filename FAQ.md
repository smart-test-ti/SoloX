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

* 支持SurfaceView和gfxinfo（界面关闭surfaceview开关切换）两种方式，可以都切换尝试是否收集到数据；如果使用gpfinfo方式需要到手机设置：开发者 - GPU渲染模式 - adb shell dumpsys gfxinfo。
* 界面相对静止的fps预期就是0，请检查页面是否滑动和动态。
* 游戏类APP不支持，照理说SurfaceView的方式是可以收集的，但是用adb读取的数据基本没有。怀疑是要用原生api才能准确获取。

## 6️⃣ 为什么"python -m solox"会运行失败 ？

* solox 2.5.4及以上版本只支持python 10.0 +的版本（因为使用了python新的特性，10.0以下版本不支持），2.5.3及以下版本支持python3.0 ~3.9。
* 如果显示的是50003端口被占用，可以用自定义的方式启动  `python -m solox --host={ip} --port={port}` 。

## 7️⃣ 为什么感觉收集速度慢 ？

* 界面收集每个指标都会起一个进程来达到同时收集的目的；基本上PC的配置跟的上，速度没有太大问题；但是不同指标计算复杂度决定了速度，比如cpu计算+读取数据的时间最少是3秒，而电池的数据基本不需要计算就是秒回。
* 可以在勾选掉部分指标，也会达到加快速度的效果。
* 使用python api收集，会比界面的速度有明显的提升。
