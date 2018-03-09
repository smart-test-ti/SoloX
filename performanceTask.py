# -*- coding: utf-8 -*-

import subprocess
import threading
import time
from imp import reload

import consts
import email_performance
import logUtils
import monitor
import progress
import pushConfig
import taskHelper
from appMonitor import app_monitor
from config import clientPackage
from config import getDeviceName
from config import installFlag
from config import pyLogName
from config import RESULT
from espressoMonitor import clearLog
from espressoMonitor import clearLogcat
from espressoMonitor import getLogPath
from espressoMonitor import installApk
from espressoMonitor import mkdir
from espressoMonitor import pullMobileLog
from espressoMonitor import startEspressoCommand_Format
from espressoMonitor import startUiauto
from espressoMonitor import unlock
from logcateThread import logcateThread
from taskHelper import keyConfig
from taskHelper import keyTaskId
from util import TAG

lock = threading.Lock()
# TAG = lambda name:'[%s]' % name
allTaskProgress = {}  # all 类型的任务只上报一个手机
# deviceState = {}#{deviceID:{taskId:xx,config:xx}}
testStatus = {}


class performanceThread(threading.Thread):
    def __init__(self, device, taskId, appUrl, emails, config, deviceState):
        threading.Thread.__init__(self);
        self.device = device
        self.taskId = taskId
        self.appUrl = appUrl.strip()
        self.emails = emails
        self.logfile = open(getLogPath(taskId, pyLogName % 'all', device), 'a+')
        self.config = config
        pushConfig.pushRTxt(taskId, device)
        self.testResults = {}
        self.totalFailedNum = 0
        self.totalPassNum = 0
        self.totalSkipNum = 0
        self.deviceState = deviceState
        self.loghd = logUtils.log_init(getDeviceName(device).strip('\n'))

    def sendEmail(self, devices, taskId, emails, isDecomposoble):
        # == email ==
        email_performance.mail(devices, taskId, emails, isDecomposoble, self.testResults)
        # try:            
        #     email_performance.mail(devices,taskId,emails,isDecomposoble,self.testResults)
        #     loghd.info("mail in email_performance sccess!")
        # except Exception,e:
        #     loghd.info("mail in email_performance error: %s" %e)

    def computeCaseResult(self):
        for k, v in self.testResults.items():
            if v == False:
                self.totalFailedNum += 1
            else:
                self.totalPassNum += 1

    def completeTask(self):
        self.computeCaseResult()
        passNum = self.totalPassNum
        failedNum = self.totalFailedNum
        skipNum = self.totalSkipNum
        totalNum = passNum + failedNum + skipNum
        taskHelper.update_progress(self.logfile, self.taskId, 100)
        taskHelper.complete_task(self.logfile, self.taskId, totalNum, passNum, failedNum, skipNum, {})
        self.resetResult()

    def resetResult(self):
        self.totalPassNum = 0
        self.totalSkipNum = 0
        self.totalFailedNum = 0

    def resetDeviceState(self):
        if self.deviceState.has_key(self.device):
            del self.deviceState[self.device]
            pushConfig.recycleConfig(self.config)
        progress.clear(self.taskId, self.device)
        if allTaskProgress.has_key(self.taskId) and allTaskProgress[self.taskId] == self.device:
            del allTaskProgress[self.taskId]

    def run(self):
        self.loghd.info("---------start thread for %s with task:%s---------" % (self.device, self.taskId),
                        TAG(self.taskId, self.device))

        self.deviceState[self.device] = {keyTaskId: self.taskId, keyConfig: self.config}
        taskHelper.execute_task(self.logfile, self.taskId)
        startResult = self.startTest()
        # startResult=RESULT.success
        # testStatus[self.device]=True

        if startResult != RESULT.success:
            self.loghd.info('---------run test %s FAILED-----' % TAG(self.taskId, self.device))
            taskHelper.kill_task(self.logfile, self.taskId)
            self.resetDeviceState()
            # espressoMonitor.killTaskEmail([self.device],self.taskId,self.emails,startResult)
            self.sendEmail([self.device], self.taskId, self.emails, False)
            return

        if testStatus[self.device]:
            time.sleep(30)
            # log(self.logfile,"send email for device:"+self.device)
            # if not isDebugMode:
            global lock
            lock.acquire()
            isUpdateErrorList = True
            # 当运行All时，只上报一个失败详情
            if allTaskProgress.has_key(self.taskId) and allTaskProgress[self.taskId] != self.device:
                isUpdateErrorList = False
            self.sendEmail([self.device], self.taskId, self.emails, False)
            self.loghd.info("complete task:" + self.taskId)
            self.completeTask()
            lock.release()

        self.resetDeviceState()
        self.logfile.close()
        self.loghd.info("---------end thread for %s with task:%s---------" % (self.device, self.taskId))

    def startTest(self):
        self.loghd.info("startTest")

        # clearLog
        clearLog(self.device)

        config = open(getLogPath(self.taskId, pyLogName, self.device) % self.device, 'w+')
        self.loghd.info("startTest device:%s taskId:%s" % (self.device, self.taskId))
        testStatus[self.device] = False
        # startTestFlag=True

        # == Uiauto ==
        uiauto = startUiauto(self.device, self.logfile)
        time.sleep(20)
        unlock(self.device, self.logfile)

        self.loghd.info("unlock screen finish")

        # == installApk ==
        if installFlag:
            if not installApk(self.device, self.logfile, self.taskId):
                uiauto.stop()
                return RESULT.installFailed

        unlock(self.device, self.logfile, True)

        self.loghd.info("install app finish")

        self.loghd.info("EntMobilePerformanceTest")
        if not self.entMobilePerformanceTest():
            uiauto.stop()
            # self.logfile.close()
            return RESULT.timeout

        uiauto.stop()
        # self.logfile.close()

        testStatus[self.device] = True
        pullMobileLog(self.taskId, self.device,self.logfile)
        return RESULT.success


        # espressoLogfile.close()          

    def entMobilePerformanceTest(self):
        # clearLogcat
        result = False

        clearLogcat(self.device)
        mkdir(self.device)

        self.loghd.info("============== performanceTest start ==============")
        monitor.start(self.taskId, self.device)

        # waitForInstallCompeleted(self.device)

        # 开始执行测试用例
        result = self.runTCs(self.device, self.taskId)

        time.sleep(10)
        monitor.clear(self.taskId, self.device)

        # 文件转码
        # translate_dir(getLogPath(taskId,'',device))

        self.loghd.info("============== performanceTest finish ==============")
        return result

    def runTCs(self, device, taskId):
        # espressoLogfile=open(getLogPath(self.taskId,espressoLogName %(1,self.device),self.device),'w+')
        # 用于计算测试的进度
        i = 0

        # if sys.modules.has_key("consts"):
        #     del sys.modules['consts']   #unimport
        #     print "del consts module"
        # import consts
        reload(consts)

        for testCase in consts.PERFORMANCE_TCS:
            i = i + 1
            excuteTestCase = testCase
            testCase = testCase.replace("#", ".")
            self.loghd.info(
                "monitor.isTimeout(self.taskId,self.device)=%s" % monitor.isTimeout(self.taskId, self.device))

            # unlock屏幕，有时候中途手机会锁屏
            unlock(self.device, self.logfile, True)

            if not monitor.isTimeout(self.taskId, self.device):
                # performanceLogfile=open(getLogPath(taskId,consts.performanceDataFile %(task),device),'w+')    
                self.loghd.info(testCase);

                # 启动logcate抓取进程
                self.testResults[testCase] = True
                logcateT = logcateThread(self.device, self.taskId, testCase, self.testResults, self.loghd, device)
                logcateT.start()

                # 启动性能数据抓取进程
                performanceDataP = app_monitor(consts.PERFORMANCE_MONITOR_PERIOD,
                                               getLogPath(taskId, consts.performanceDataFile % (testCase), device),
                                               clientPackage, self.loghd, device)
                performanceDataP.start()

                # 等待10s后再执行性能测试用例
                time.sleep(10)

                # 启动运行测试用例
                espressoLogfile = open(getLogPath(self.taskId, consts.espressoLogName % (testCase), self.device), 'w+')
                excuteTcCmd = "adb -s %s shell " + startEspressoCommand_Format % ("-e class " + excuteTestCase)
                self.loghd.info(excuteTcCmd);
                espressoSubProcess = subprocess.Popen((excuteTcCmd % device).split(), stdout=espressoLogfile,
                                                      stderr=espressoLogfile).wait()
                espressoLogfile.close()

                # 停止log和数据抓取线程
                logcateT.stop()
                performanceDataP.stop()
                # while performanceDataP.is_alive():
                #     print "performanceDataP still alive, wait....."
                #     time.sleep(1)     

                # 更新测试进度
                taskHelper.update_progress(self.logfile, self.taskId, 100 * i / len(consts.PERFORMANCE_TCS))

        if monitor.isTimeout(self.taskId, self.device):
            return False
        else:
            return True
