<p align="center">
  <a>DocForAndroid</a> | <a href="./README.md">README</a>
</p>

### CPU

- appCpu：测试进程CPU使用率
- systemCpu：整机CPU使用率

读取/proc/stat文件，我们可以看到下面的内容

```
cpu  2490696 175785 2873834 17973539 12823 680472 230184 0 0 0
cpu0 621631 33199 739364 12893642 10736 365458 86720 0 0 0
cpu1 623944 30576 688904 677748 609 145744 93230 0 0 0
cpu2 519768 33948 650022 685194 703 78117 23873 0 0 0
cpu3 499978 33082 547153 687802 650 81072 21360 0 0 0
cpu4 32586 4853 41910 774975 36 2097 1025 0 0 0
cpu5 30950 5003 40730 776693 19 2060 999 0 0 0
cpu6 99227 22708 109219 722048 23 3970 2140 0 0 0
cpu7 62610 12414 56531 755434 44 1952 836 0 0 0
intr 209333749 0 0 0 0 35952688 0 11796562 7 5 5 17537 80 2431 0 0 0 1069962 0 35 1334360 0 0 0 0 0 11 11 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 34984538 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 505 50695 1174791 345 0 0 0 11301652 24660 0 111 0 0 0 0 0 0 0 0 0 0 0 86153 54 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1099230 0 18 1814 0 0 23 514624 1300943 248469 0 0 0 0 0 97168 60709 1641967 609754 38618 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 519 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1556 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 18 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 5 0 0 0 3548401 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 18 0 0 163911 192365 0 0 0 0 1018 0 1 0 2 0 2 0 2 1 0 0 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 56891 4227 147 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 751521 0 0 200 0 0 0 0 0 0 0 0 0 0 0 0 0 27 26 26 0 34 50 330 34 0 0 0 0 0 0 0 0 1223 0 11 0 0 0 26
```
对于上述cpu数据来说，每行CPU的数字依次表示

```
user (14624) 从系统启动开始累计到当前时刻，处于用户态的运行时间 
nice (771) 从系统启动开始累计到当前时刻
system (8484) 从系统启动开始累计到当前时刻，处于核心态的运行时间 
idle (283052) 从系统启动开始累计到当前时刻，除IO等待时间以外的其它等待时间 
iowait (0) 从系统启动开始累计到当前时刻，IO等待时间
irq (0) 从系统启动开始累计到当前时刻，硬中断时间
softirq (62) 从系统启动开始累计到当前时刻，软中断时间
```
- 我们可以得到 cpu 运行时长为 cpu = user + nice + system + iowait + irq + softirq，而总时长为 cpu_total = cpu + idle
- 由于我们的采集间隔几乎等于1s，于是过去1s的设备整体 cpu 使用率为 (cpu - cpu_pre) / (cpu_total - cpu_total_pre)

通过读取/proc/pid/stat文件，我们可以看到下面的内容
```
6873 (a.out) R 6723 6873 6723 34819 6873 8388608 77 0 0 0 41958 31 0 0 25 0 3 0 5882654 1409024 56 4294967295 134512640 134513720 3215579040 0 2097798 0 0 0 0 0 0 0 17 0 0 0
```
```
pid=6873 进程(包括轻量级进程，即线程)号
comm=a.out 应用程序或命令的名字
task_state=R 任务的状态，R:runnign, S:sleeping (TASK_INTERRUPTIBLE), D:disk sleep (TASK_UNINTERRUPTIBLE), T: stopped, T:tracing stop,Z:zombie, X:dead
ppid=6723 父进程ID
pgid=6873 线程组号
sid=6723 c该任务所在的会话组ID
tty_nr=34819(pts/3) 该任务的tty终端的设备号，INT（34817/256）=主设备号，（34817-主设备号）=次设备号
tty_pgrp=6873 终端的进程组号，当前运行在该任务所在终端的前台任务(包括shell 应用程序)的PID。
task->flags=8388608 进程标志位，查看该任务的特性
min_flt=77 该任务不需要从硬盘拷数据而发生的缺页（次缺页）的次数
cmin_flt=0 累计的该任务的所有的waited-for进程曾经发生的次缺页的次数目
maj_flt=0 该任务需要从硬盘拷数据而发生的缺页（主缺页）的次数
cmaj_flt=0 累计的该任务的所有的waited-for进程曾经发生的主缺页的次数目
utime=41958 该任务在用户态运行的时间，单位为jiffies
stime=31 该任务在核心态运行的时间，单位为jiffies
cutime=0 累计的该任务的所有的waited-for进程曾经在用户态运行的时间，单位为jiffies
cstime=0 累计的该任务的所有的waited-for进程曾经在核心态运行的时间，单位为jiffies
priority=25 任务的动态优先级
nice=0 任务的静态优先级
num_threads=3 该任务所在的线程组里线程的个数
it_real_value=0 由于计时间隔导致的下一个 SIGALRM 发送进程的时延，以 jiffy 为单位.
start_time=5882654 该任务启动的时间，单位为jiffies
vsize=1409024（page） 该任务的虚拟地址空间大小
rss=56(page) 该任务当前驻留物理地址空间的大小
Number of pages the process has in real memory,minu 3 for administrative purpose.
这些页可能用于代码，数据和栈。
rlim=4294967295（bytes） 该任务能驻留物理地址空间的最大值
start_code=134512640 该任务在虚拟地址空间的代码段的起始地址
end_code=134513720 该任务在虚拟地址空间的代码段的结束地址
start_stack=3215579040 该任务在虚拟地址空间的栈的结束地址
kstkesp=0 esp(32 位堆栈指针) 的当前值, 与在进程的内核堆栈页得到的一致.
kstkeip=2097798 指向将要执行的指令的指针, EIP(32 位指令指针)的当前值.
pendingsig=0 待处理信号的位图，记录发送给进程的普通信号
block_sig=0 阻塞信号的位图
```
- 由于SoloX的采集间隔为1s，可以计算进程cpu使用率为 ((utime + stime) - (utime_pre + stime_pre)) / (cpu_total - cpu_total_pre)

### Memory

- TotalPss: 应用实际占用物理内存
- NativePss: native内存
- DalvikPss: java内存(OOM的原因)

通过adb shell dumpsys meminfo pid，我们可以获得如下内容
```
Applications Memory Usage (in Kilobytes):
Uptime: 543447125 Realtime: 543469686
** MEMINFO in pid 23178 [com.huawei.browser:sandboxed_process0:com.huawei.browser.sandbox.SandboxedProcessService0:6] **
                   Pss  Private  Private  SwapPss     Heap     Heap     Heap
                 Total    Dirty    Clean    Dirty     Size    Alloc     Free
                ------   ------   ------   ------   ------   ------   ------
  Native Heap       99       96        0     2028     6656     4327     2328
  Dalvik Heap        4        0        0      754     3078     1030     2048
 Dalvik Other        4        4        0      366
        Stack        8        8        0       26
    Other dev        4        0        4        0
     .so mmap      535        4        0      319
    .jar mmap      114        0        0        0
    .apk mmap        2        0        0        0
    .dex mmap      622        0        4     2617
    .oat mmap      409        0        0        0
    .art mmap      259       16        0     2183
   Other mmap       14        0        0        6
      Unknown       28       28        0      455
        TOTAL    10856      156        8     8754     9734     5357     4376
 App Summary
                       Pss(KB)
                        ------
           Java Heap:       16
         Native Heap:       96
                Code:        8
               Stack:        8
            Graphics:        0
       Private Other:       36
              System:    10692
               TOTAL:    10856       TOTAL SWAP PSS:     8754
```

### Network

- recv：被测应用的下行流量
- send：被测应用的上行流量

通过读取 /proc/pid/net/dev文件，我们可以获得如下数据，其中wlan0表示wifi流量，rmnet0表示sim卡流量
```
解析/proc/%d/net/dev示例结果
Inter-|   Receive                                                |  Transmit
face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
rmnet4:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun03:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_r_ims01:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun02:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
dummy0:       0       0    0    0    0     0          0         0     1610      23    0    0    0     0       0          0
rmnet2:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun11:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_ims00:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun10:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_emc0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun13:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun00:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun04:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet5:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
wlan0: 1241518561  840807    0    0    0     0          0         7  7225770   73525    0    6    0     0       0          0
rmnet_r_ims00:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet3:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun01:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
sit0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun14:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
ip_vti0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
ip6tnl0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet1:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
ip6_vti0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_r_ims11:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_r_ims10:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet6:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
rmnet_tun12:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
lo: 3796620     292    0    0    0     0          0         0  3796620     292    0    0    0     0       0          0
rmnet_ims10:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
```

### FPS&Jank

- fps：用户可见的每秒显示帧数
- jank：卡顿发生次数

#### FPS
```
SurfaceFlinger 接受来自多个数据源的数据缓冲区数据，通过GPU合成并发送给显示设备。这是我们通常描述的 fps，也是客户真实可视可体验到的的帧数数据。

在安卓系统中，WindowManagerService 会对每一个 contentView 创建相关的UI载体Surface，SurfaceFlinger 主要负责将这个 Surface 渲染到手机屏幕上。

除了 Android 主窗口的焦点Activity 与相对应的 ContentView 之外，还存在一种特殊的 SurfaceView, 他会独享一个 Surface，这个 Surface 独立渲染非常高效，支持 OpenglES 渲染。也就是说可能会出现两类窗口fps。一个是Activity窗口帧率和SurfaceView窗口帧率。

一般来说，游戏、视频类应用都是通过这种 SurfaceView 来进行绘制，为了能够尽可能准确的获取被测应用的帧率，我们默认优先获取 SurfaceView 的 FPS。

然后，再通过dumpsys SurfaceFlinger --latency SurfaceView com.youku.phone/com.youku.ui.activity.DetailActivity 可以准确获取到视频窗口的帧绘制信息。

采用以上方法统计 fps 通常会有以下疑问：

SurfaceFlinger必须始终显示内容，所以当上层并没有新的缓存数据时，SurfaceFlinger会继续显示当前数据，因此通过这种方法统计出来的 fps 值一般较低，静态页面可能为0，这样的 fps 值是否具有迷惑性；
比如上图的视频应用只有 25fps，我们滑动时可能都有 40+ fps，这个数据能说明什么样的问题；
fps 波动范围这么大，fps 值怎样才可以描述应用的流畅程度。
```

- 视觉惯性
```
视觉预期帧率，用户潜意识里认为下帧也应该是当前帧率，比如我们玩游戏一直是60帧，用户潜意识里认为下帧也应该是60帧率。刷新一直是25帧，用户潜意识里认为下帧也应该是25帧率。但是如果60帧一下跳变为25帧，就会产生明显的卡顿感。
```
- 电影帧
```
电影帧率一般是24帧。电影帧单帧耗时为 1000ms/24≈41.67ms。电影帧率是一个临界点。低于这个帧率，人眼可以感觉出画面的不连续性。
```

#### JANK

既然 fps 无法完整的描述应用的流畅度，那么是否可以有一个指标表示应用的流畅程度，换言之，能否描述应用的卡顿程度。答案是 jank。

理解 jank，就一定要理解 google 设计的三重缓存机制（如下）。三重缓存指的是A、B、C三个缓存结构，当 GPU 未能在一次 VSync 时间内完成B的处理，此时display、gpu、cpu 同时在处理A、B、C三个缓存，实现资源最大化的利用。

我们可以通过 dumpsys gfxinfo packageName 获取到的 janky frames如下。这里的Janky frames是当一帧的时间大于16.67ms时，就计为一次 Janky frame。


从上文提到的三重缓存机制我们可以进行分析，B先导致了一次视觉上的jank，C理论上也是jank（跨VSync），但是由于此时屏幕上显示的是B，C虽然delay了一帧，但是 C 看起来仍然是紧跟着B显示在屏幕上，而且 A 顺利的在16.67ms完成了绘制，实际上用户视觉上只少看了一帧，而Janky frames 是 2。我们发现，当 Janky frames 高达近 40% 甚至 50% 时，我们依然感受不到卡顿，这个值并不是理想中的反映流畅度的指标。

```
Applications Graphics Acceleration Info:
Uptime: 171070276 Realtime: 962775383
** Graphics info for pid 13422 [com.zhongduomei.rrmj.society] **
Stats since: 152741070392878ns
Total frames rendered: 110
Janky frames: 7 (6.36%)
50th percentile: 9ms
90th percentile: 13ms
95th percentile: 18ms
99th percentile: 36ms
Number Missed Vsync: 2
Number High input latency: 0
Number Slow UI thread: 6
Number Slow bitmap uploads: 3
Number Slow issue draw commands: 0
```

基于以上考虑，我们重新定义 jank 的计算方式：

- 视觉连续性问题：帧时长 > 前三帧平均时长*2
- 卡顿问题：帧时长 > 电影帧时长 * 2

假设应用按照电影帧 41.67ms 运行，若帧时长大于 2*41.67ms，意味着在缓存机制下，依然必现一次卡顿问题。

### Battery

- Level：电量
- Temperature：电池温度

adb shell dumpsys battery

```
AC powered: false
USB powered: true
Wireless powered: false
Max charging current: 500000         # 最大充电电流
Max charging voltage: 5000000      #最大充电电压
Charge counter: 1973820				#
status: 2										#电池状态：2：充电状态 ，其他数字为非充电状态   
health: 2									#电池健康状态：只有数字2表示good
present: true								#电池是否安装在机身
level: 67									#当前电量百分比
scale: 100								#最大电量百分比
voltage: 4066						#当前电压
temperature: 330					#当前温度，单位为0.1摄氏度(要除以10)
technology: Li-ion

```



