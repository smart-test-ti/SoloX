# -*- coding: utf-8 -*-

import os
import re
import smtplib
from email.header import Header
from email.mime.text import MIMEText

import config
import consts

# from logUtils import loghd

# ==================================
# Need to modify info
# ==================================

passRate = 100
index = 0

# ==================================
mail_host = "mail.yy.com"
mail_user = "CI_YY"
mail_user1 = "CI_YY@yy.com"
mail_pass = "qazxsw21ci1"
mail_postfix = "yy.com"

mailto = ["liuweizhi@yy.com", "chenriming@yy.com", "luoyanjie@yy.com", "jianghao1@yy.com"]
mailcc = ["chenriming@yy.com"]
# --------------------------------------------------------


tempTestDataVersion = None
tempTestDataTime = None
tempTestDataUrl = None

totalPassNum = 0
totalFailedNum = 0
totalSkipNum = 0

resultDic = {}


# --------------------------------------------------------
def durationsToStr(time):
    if "." in time:
        time = time.split(".")[0]
    duration = int(time)

    durationSecond = duration % 60
    durationMin = int(duration / 60 % 60)
    durationHour = int(duration / 60 / 60)

    if durationHour != 0:
        durationString = "%d时%d分%d秒" % (durationHour, durationMin, durationSecond)
    elif durationMin != 0:
        durationString = "%d分%d秒" % (durationMin, durationSecond)
    elif durationSecond != 0:
        durationString = "%d秒" % (durationSecond)
    else:
        print "duration is 0!"
    # logfile2.write("duration is 0!\n")

    return durationString


# --------------------------------------------------------

eMailSubjectNew = "Android YYLive 性能测试报告 [%s: %s]---"

headData = {
    "version": 0,  # 20151019-35906-r
    "time": 0,  # 2015-10-19,15:45:05
    "title": "性能测试用例",  # Android YY P0 自动化用例
    "cell": "xiaomi4",  # htc m8w(5.0.2) , samung note 2 (4.4.2) , moto x pro ( 5.0.2)
    # version
    "url": 0,  # http://repo.yypm.com/dwbuild/mobile/android/entmobile/entmobile-android_develop/
}


def makeHeadData(devices):
    headData["version"] = tempTestDataVersion
    headData["time"] = tempTestDataTime
    headData["url"] = tempTestDataUrl
    headData["cell"] = ','.join([config.getDeviceName(device) for device in devices])

    return head % (headData["version"],
                   headData["time"],
                   headData["title"],
                   headData["cell"],
                   headData["version"],
                   headData["url"],)


head = '''
<body>
<h2>Android YYLive 性能测试报告  [%s]</h2>

<p style="font-family: 'Lucida Sans Unicode', 'Lucida Grande', sans-serif; font-size: 14px;">
测试时间: %s
<br>
测试范围: %s
<br>
测试手机: %s
<br>
<b>测试版本: %s</b>
<br>
版本路径: %s
</p>'''

killTaskBody = '''
<p style="font-family: Lucida Sans Unicode, Lucida Grande, sans-serif;">
<table  border="0" >
<tr>
    <th bgcolor="#FF8888">
      <div>
        <a> </a>
      </div>
      任务执行失败：%s
    </th>
</tr>
<tr>
    <th>任务信息:<a href=%s>%s</a></th>
</tr>
</table>
'''

# --------------------------------------------------------

# <br>测试耗时: %s
performanceLine = '''
<tr bgcolor="%s">
	<th width="150">%s</th>
	<th width="150">%s</th>
	<th width="150"><a href="%s">%s</a> <a href="%s">%s</a></th>
	<th width="150" ><a href="%s">%s</a></th>
	<th width="150" ><a href="%s">%s</a>  <a href="%s">%s</a></th>
 </tr>
 '''


def findColor():
    global index
    index += 1
    if index % 2 == 1:
        return "#d2d5d8"
    return ""


def makePerformanceResultLine(logMapping, picMapping, espressoLogMapping, performanceMapping, testResults,
                              deviceName=''):
    # print logMapping
    # print picMapping
    # print espressoLogMapping
    performanceLines = ""
    for testCase in consts.PERFORMANCE_TCS:
        testCase = testCase.replace("#", ".")
        if testResults.has_key(testCase):
            performanceLines += performanceLine % (
                findColor(),
                testCase,
                testResults[testCase],
                performanceMapping[testCase] + ".jpg",
                "性能图",
                performanceMapping[testCase] + ".csv",
                "数据下载",
                picMapping[testCase],
                "截图" if testResults[testCase] == False else "无截图",
                logMapping[testCase],
                "logcat" if logMapping.has_key(testCase) else "无logcat日志",
                espressoLogMapping[testCase] if espressoLogMapping.has_key(testCase) else None,
                "junit" if espressoLogMapping.has_key(testCase) else "",)
        else:
            performanceLines += performanceLine % (
                findColor(),
                testCase,
                "False",
                "",
                "性能图",
                ""
                "数据下载",
                "",
                "无截图",
                "",
                "无logcat日志",
                "None",
                "",)
    return performanceLines


contentPerformance = '''
<table border="0">
  <tr>
    <th colspan="5" bgcolor="#a0a0a0">
    Failed TestCase Detail
    </th>
  </tr>
  
    <tr>
      <th width="110">测试用例</th>
      <th width="110" >测试结果</th>
      <th width="110">性能数据</th>
      <th width="140">失败截图</th>
      <th width="140">失败日志</th>
    </tr>
  %s
</table>
<h4>用例描述后续完善</h4>
'''

contentTail = '''
<br>
<br>
<h4>Thanks</h4>

</body></p>
'''


def analysis(devices, taskId):
    temp = data.split(": started:")
    temp = temp[1:]

    for i in range(2):
        item = temp[i]
        # print item

        itemList = re.findall(r"(.+?)\((.+?)\)", item)
        itemList = itemList[0]
        itemTest = itemList[0].strip()
        itemClass = itemList[1].split(".")[-1].strip()
        # print itemClass,itemTest
        itemStatus = 0
        name = itemClass + '.' + itemTest
        if "begin exception" in item:
            failFile = open(filePath + '/' + itemTest + ".txt", "w+")
            failFile.write(item)
            failFile.close()

            logUrl = sharePath + "/" + itemTest + ".txt"
            picUrl = sharePath + "/espresso/" + itemTest + ".jpg"

            logFile = filePath + "/" + itemTest + ".txt"
            picFile = filePath + "/espresso/" + itemTest + ".jpg"

            if os.path.isfile(logFile):
                logMapping[name] = logUrl
            else:
                logMapping[name] = None

            if os.path.isfile(picFile):
                picMapping[name] = picUrl
            else:
                picMapping[name] = None

            itemStatus = 1
        createData(resulte, itemClass, itemTest, itemStatus)
        match = re.search('\[用例:(.{1,200})\]', item)
        caseName = 'null'
        if match:
            caseName = match.group(1)
        caseNameMapping[name] = caseName


def makePerformanceHtml(devices, taskId, testResults):
    # 邮件头部数据
    html = makeHeadData(devices)

    # 组装邮件内容
    logMapping = {}
    picMapping = {}
    espressoLogMapping = {}  # {class.case:name}
    performanceMapping = {}  # {class.case:name}
    # def getLogName(taskId,device,logName):
    # logPath =  os.path.join("share",taskId,device,logName)
    sharePath = os.path.join(consts.shareRootPath, taskId, devices[0])

    # 从手机拉取截图
    filePath = os.path.join("share", taskId, devices[0], config.resultPath)
    if not os.path.exists(filePath):
        os.mkdir(filePath)
    os.popen(config.pullCommand % (devices[0], filePath)).read()

    for testCase in consts.PERFORMANCE_TCS:
        testCase = testCase.replace("#", ".")
        logMapping[testCase] = os.path.join(sharePath, consts.logcatLogName % (testCase))
        picMapping[testCase] = os.path.join(sharePath, "result", "espresso", testCase.split(".")[-1] + ".jpg")
        espressoLogMapping[testCase] = os.path.join(sharePath, consts.espressoLogName % (testCase))
        performanceMapping[testCase] = os.path.join(sharePath, consts.performanceDataFile % (testCase))

    html += contentPerformance % makePerformanceResultLine(logMapping, picMapping, espressoLogMapping,
                                                           performanceMapping, testResults, devices[0])

    # 删除手机中保存的截图文件
    os.popen(config.removeFolderCommand % (devices[0], "//sdcard//espresso")).read()

    # 加上邮件尾部
    return html + contentTail


def send_mail(to_list, cc_list, content, subject):
    Sender = "YYLive Automated Testing" + "<" + mail_user + "@" + mail_postfix + ">"

    # plain text html
    msg = MIMEText(content, _subtype='html', _charset='utf-8')
    msg['Subject'] = Header(subject, charset='utf-8')
    msg['From'] = Sender
    msg['To'] = ";".join(to_list)

    if len(to_list) > 3:
        msg['CC'] = ";".join(cc_list)
        to_list += cc_list
    # logfile2=open("email.log",'a+')
    try:
        server = smtplib.SMTP()
        server.connect(mail_host)
        # logfile2.write("connect=======%s\n" % subject)

        server.login(mail_user1, mail_pass)
        # logfile2.write("login=======%s\n" % subject)

        server.sendmail(Sender, to_list, msg.as_string())
        # logfile2.write("send=======%s\n" % subject)
        # logfile2.close()
        server.close()
        return True
    except Exception, e:
        # loghd.info('email exception',str(e))
        return False


def getTestInfo(taskId, device):
    tempTestDataFile = open(os.path.join('share', taskId, "testInfo"))
    tempTestData = tempTestDataFile.readlines()
    global tempTestDataVersion, tempTestDataTime, tempTestDataUrl
    tempTestDataVersion = tempTestData[0].strip()
    tempTestDataTime = tempTestData[1].strip()
    tempTestDataUrl = tempTestData[2].strip()
    tempTestDataFile.close()


def killTaskEmail(devices, taskId, emails, taskResult):
    getTestInfo(taskId, devices[0])
    makeHeadData(devices)
    headHtml = head % (headData["version"],
                       headData["time"],
                       headData["title"],
                       headData["cell"],
                       headData["version"],
                       headData["url"],)
    from config import RESULT
    if taskResult == RESULT.timeout:
        msg = '超时'
    elif taskResult == RESULT.installFailed:
        msg = '安装失败'
    from analysis2 import shareRootPath
    taskFolder = shareRootPath + os.path.join("share", taskId)
    bodyHtml = killTaskBody % (msg, taskFolder, taskFolder)
    subject = eMailSubjectNew % (taskId, config.getDeviceName(devices[0]))
    subject += "BLOCK"
    html = headHtml + bodyHtml
    send_mail(mailto + emails, mailcc, html, subject)


def mail(devices, taskId, emails, isDecomposable, testResults):
    global index
    index = 0
    getTestInfo(taskId, devices[0])
    if not isDecomposable:
        html = makePerformanceHtml(devices, taskId, testResults)
    else:
        html = makeDecomposableHtml(taskId)
    subject = eMailSubjectNew % (taskId, config.getDeviceName(devices[0]))
    # if passRate == 100:
    # 	subject += "PASS"
    # else:
    # 	subject += "FAILED"
    send_mail(mailto + emails, mailcc, html, subject)


def resetResult():
    global totalFailedNum, totalPassNum, totalSkipNum
    totalPassNum = 0
    totalSkipNum = 0
    totalFailedNum = 0


if __name__ == '__main__':
    # pass
    # devices=["ZX1G2268R4"]
    # devices=["ZX1G2268R4"]
    # mail(devices,"1",[])
    # send_mail(mailto_list,mailcc_list,makeHtml(devices),(eMailSubjectNew %tempTestDataVersion))
    # analysisDecomposoable("1001")
    # killTaskEmail(["DLQ0215C14023970"],'1000',[],1)
    mail(['PBV7N16419016161'], '126118', [], True, True)
