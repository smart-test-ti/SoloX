# -*- coding: utf-8 -*-

import re
import subprocess
import threading
import time

import consts
import monitor
from adbTool import Adb
from espressoMonitor import clearLogcat
from espressoMonitor import getLogPath
from espressoMonitor import readStdout


class logcateThread(threading.Thread):
    def __init__(self, device, taskId, taskName, testResults, loghd, serial=None):
        threading.Thread.__init__(self);
        # self.running = True
        self.adb = Adb(serial=serial)
        self.logcatSubProcess = None
        self.device = device
        self.taskId = taskId
        self.taskName = taskName
        self.testResults = testResults
        self.appPid = 0
        self.loghd = loghd
        self.is_alive = False

    def stop(self):
        # self.running = False
        try:
            while self.is_alive and self.getAppPid() == self.appPid and self.getAppPid() != 0:
                self.loghd.info("logcate Thread still alive, wait ...")
                time.sleep(1)

            if self.logcatSubProcess.poll() == None:
                self.logcatSubProcess.terminate()
        except:
            pass

    def getAppPid(self):
        # self.appPid = self.adb.cmd("shell", "set", "`ps|grep com.duowan.mobile$`;", "echo", "$2").communicate()[0].decode("utf-8").strip()
        outputs = self.adb.cmd("shell", "top", "-m", "10", "-n", "1").communicate()[0].decode("utf-8").strip()
        r = "(\\d+).*\\s+%s[^:]" % "com.duowan.mobile"  # hardcode 手y
        m = re.search(r, outputs)
        # print outputs
        if m:
            return m.group(1)
        else:
            self.loghd.info("app still not get up")
            return 0

            # 执行用例中途会退出导致logcat抓取不全

    # def run(self):
    #     self.loghd.info("logcateThread run \n")
    #     self.is_alive = True
    #     clearLogcat(self.device)
    #     logcatLogfile=open(getLogPath(self.taskId,consts.logcatLogName %(self.taskName),self.device),'w+')

    #     self.logcatSubProcess=subprocess.Popen((consts.logcatCommand %self.device).split(),stdout=logcatLogfile,stderr=logcatLogfile)

    #     while ((not monitor.isTimeout(self.taskId,self.device)) and self.running):
    #         monitor.heart(self.taskId,self.device)
    #         time.sleep(1)

    #     logcatLogfile.close()
    #     self.is_alive = False          

    def run(self):
        self.loghd.info("logcateThread run \n")
        self.is_alive = True
        # 清楚logcat log
        clearLogcat(self.device)
        logcatLogfile = open(getLogPath(self.taskId, consts.logcatLogName % (self.taskName), self.device), 'w+')
        self.appPid = self.getAppPid()

        # == start logcat ==subprocess.PIPE
        self.logcatSubProcess = subprocess.Popen((consts.logcatCommand % self.device).split(), stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT)

        total = 0
        finishedIndex = 0
        timeInterval = 0.1

        # timeoutFlag=False

        # while ((not monitor.isTimeout(self.taskId,self.device)) and self.running):
        while (not monitor.isTimeout(self.taskId, self.device)):
            content = monitor.timeoutTask(self.taskId, self.device, readStdout, self.logcatSubProcess)
            if not content:
                time.sleep(timeInterval)
                continue
            logcatLogfile.write(content)
            logcatLogfile.flush()

            monitor.heart(self.taskId, self.device)

            if "1 failed" in content:
                self.testResults[self.taskName] = False

            # 结束内容出现，则结束当前logcate抓取线程
            # if "): finished:" in content:
            #     self.running = False
            #     break

            # avoid uiauto log
            filte = re.findall(r"run finished:\s+(\d+)\s+tests.+?(\d+)\s+ignored", content)
            if len(filte) and filte[0][0] != 3 and filte[0][1] != 0:
                # self.running = False
                self.loghd.info("logcat finish.")
                break
                # progress report
                # filte=re.findall(r"run started:\s+(\d+)\s+tests",content)
                # if filte:
                #     total=int(filte[0])
                #     # if step==3:
                #     #     total+=self.config.getTotal(self.taskId,self.device)
                #     config.setTotal(self.taskId,self.device,total)

                # if "): finished:" in content:
                #     finishedIndex+=1
                #     # if step==1:
                #     totalFinishedIndex=finishedIndex
                #     # if step==3:
                #     #     totalFinishedIndex=finishedIndex+config.getFinished(self.taskId,self.device)
                #     config.setFinished(self.taskId,self.device,totalFinishedIndex)
                #     progress=int(float(config.getFinished(self.taskId,self.device))/config.getTotal(self.taskId,self.device)*100)
                #     config.setProgress(self.taskId,self.device,progress)

                # filte=re.findall(r"run finished:\s+(\d+)\s+tests.+?(\d+)\s+ignored",content)

        self.is_alive = False
        # avoid uiauto log
        # if len(filte) and filte[0][0]!=3 and filte[0][1]!=0:
        # log(self.logfile,"logcat finish.")
        # monitor.clear(self.taskId,self.device)
        # break
        # else:
        #     # log(self.logfile,"============== %d timeout =============="%step)
        #     monitor.clear(self.taskId,self.device)
        #     timeoutFlag=True
