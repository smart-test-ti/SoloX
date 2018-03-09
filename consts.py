# -*- coding: utf-8 -*-
import util


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


PERFORMANCE_MONITOR_PERIOD = 2
TASK_TYPE = enum(EntMobileTest=0, EntMobilePerformanceTest=1)
# print TASK_TYPE.reverse_mapping[1]
CURRENT_TASK_TYPE = TASK_TYPE.EntMobilePerformanceTest
PERFORMANCE_TCS = [
    "test.testcases.Performance.ChannelPerformance#goIntoChanelTest",
    "test.testcases.Performance.ChannelPerformance#swipePortraitChannelTest",
    "test.testcases.Performance.ChannelPerformance#rotateScreenTest",
    "test.testcases.Performance.ChannelPerformance#switchPageTest",
    "test.testcases.Performance.ChannelPerformance#sendMsgTest",
    "test.testcases.Performance.ChannelPerformance#longTimeInChanelTest",

    "test.testcases.Performance.HomePagePerformance#swipeDownRefreshTest",
    "test.testcases.Performance.HomePagePerformance#swipeUpTest",
    "test.testcases.Performance.HomePagePerformance#homePageTabTest",
    "test.testcases.Performance.HomePagePerformance#horizontalSwipeTest",

    "test.testcases.Performance.IMPerformance#sendMsgTest",
    "test.testcases.Performance.IMPerformance#sendPhotoTest",
    "test.testcases.Performance.IMPerformance#sendEmotionTest",
    "test.testcases.Performance.IMPerformance#sendRandomContentTest",

    "test.testcases.Performance.StartLivePerformance#startLiveTest",
    "test.testcases.Performance.StartLivePerformance#switchCameraTest",
    "test.testcases.Performance.StartLivePerformance#landScapeSwitchCameraTest",
    "test.testcases.Performance.StartLivePerformance#switchResolutionTest",
    "test.testcases.Performance.StartLivePerformance#switchPageTest",

    # "test.testcases.BVT.StartLiveTest#phoneLiveTest",
    # "test.testcases.BVT.StartLiveTest#focusTexBoxTest"

]

logcatCommand = "adb -s %s shell logcat -v time |grep TestRunner"
espressoLogName = "espresso_%s.log"
logcatLogName = "logcat_%s.log"
performanceDataFile = "performanceData_%s"
clearLogcatCammand = "adb -s %s shell logcat -c"
shareRootPath = "http://%s:%d/" % (util.getLocalIP("eth0"), 80)
