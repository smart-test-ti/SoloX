# -*- coding: utf-8 -*-
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
'''
封装adb基本操作
'''

import re
import os
import time
import threading
import subprocess
import sys
import platform
import traceback

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))
from datetime import datetime,timedelta
from mobileperf.common.log import logger
from mobileperf.common.utils import TimeUtils,FileUtils
from mobileperf.android.globaldata import RuntimeData

class ADB(object):
    '''本地ADB
    '''
    os_name = None
    adb_path = None
    
    def __init__(self, device_id=None):
        self._adb_path = ADB.get_adb_path()     # adb.exe程序的绝对路径
        self._device_id = device_id     # 设备id adb serialNum
        self._need_quote = None
        self._logcat_handle=[]
        self._system_version = None
        self._sdk_version = None
        self._phone_brand = None
        self._phone_model = None
        self._os_name = None
        self.before_connect = True
        self.after_connect = True
        
    @property    
    def DEVICEID(self):
        return self._device_id
    
    @staticmethod
    def get_adb_path():
        '''返回adb.exe的绝对路径。优先使用指定的adb，若环境变量未指定，则返回当前脚本tools目录下的adb
        
        :return: 返回adb.exe的绝对路径
        :rtype: str
        '''
        if ADB.adb_path:
            return ADB.adb_path
        ADB.adb_path = os.environ.get('ADB_PATH')
        if ADB.adb_path != None and ADB.adb_path.endswith('adb.exe'):
            return ADB.adb_path
        # 判断系统默认adb是否可用，如果系统有配，默认优先用系统的，避免5037端口冲突
        proc = subprocess.Popen('adb devices', stdout=subprocess.PIPE, shell=True)
        result = proc.stdout.read()
        logger.debug(result)
        if not isinstance(result, str):
            result = str(result,'utf-8')
        # 说明自带adb  windows上返回结果不是这样 另外有可能第一次执行，adb会不正常
        if result and "command not found" not in result:
            ADB.adb_path = "adb"
            logger.debug("system have adb")
            return ADB.adb_path
        logger.debug("system have no adb")
        cur_path = os.path.dirname(os.path.abspath(__file__))
        ADB.os_name = platform.system()
        logger.debug("platform :" + ADB.os_name)
        if ADB.os_name == "Windows":
            ADB.adb_path = os.path.join(cur_path, u'adb.exe')
        elif ADB.os_name == "Darwin":
            ADB.adb_path = os.path.join(cur_path, "platform-tools-latest-darwin", "platform-tools", "adb")
        else:
            ADB.adb_path = os.path.join(cur_path, "platform-tools-latest-linux", "platform-tools", "adb")
        return ADB.adb_path

    @staticmethod
    def get_os_name():
        if ADB.os_name:
            return ADB.os_name
        ADB.os_name = platform.system()
        return ADB.os_name

    @staticmethod
    def is_connected(device_id):
        '''
                    检查设备是否连接上
        '''
        if device_id in ADB.list_device():
            return True
        else:
            return False

    @staticmethod
    def list_device():
        '''获取设备列表

        :return: 返回设备列表
        :rtype: list
        '''
        proc = subprocess.Popen("adb devices", stdout=subprocess.PIPE, shell=True)
        result = proc.stdout.read()
        if not isinstance(result, str):
            result = result.decode('utf-8')
        result = result.replace('\r', '').splitlines()
        logger.debug("adb devices:")
        logger.debug(result)
        device_list = []
        for device in result[1:]:
            if len(device) <= 1 or not '\t' in device: continue
            if device.split('\t')[1] == 'device':
                # 只获取连接正常的
                device_list.append(device.split('\t')[0])
        return device_list

    @staticmethod
    def recover():
        if ADB.checkAdbNormal():
            logger.debug("adb is normal")
            return
        else:
            logger.error("adb is not normal")
            ADB.kill_server()
            ADB.start_server()

    @staticmethod
    def checkAdbNormal():
        sub = subprocess.Popen("adb devices", stdout=subprocess.PIPE, shell=True)
        adbRet = str(sub.stdout.read(),"utf-8")
        sub.wait()
        logger.debug("adb device ret:%s" % adbRet)
        if not adbRet:
            logger.debug("devices list maybe is empty")
            return True
        else:
            if "daemon not running." in adbRet:
                logger.warning("daemon not running.")
                return False
            elif "ADB server didn't ACK" in adbRet:
                logger.warning("error: ADB server didn't ACK,kill occupy 5037 port process")
                return False
            else:
                return True

    @staticmethod
    def kill_server():
        logger.warning("kill-server")
        os.system("adb kill-server")

    @staticmethod
    def start_server():
        ADB.killOccupy5037Process()
        logger.warning("fork-server")
        os.system("adb fork-server server -a")

    @staticmethod
    def killOccupy5037Process():
        if ADB.get_os_name() == "Windows":
            sub = subprocess.Popen('netstat -ano|findstr \"5037\"', stdout=subprocess.PIPE, shell=True)
            ret = sub.stdout.read()
            sub.wait()
            if not ret:
                logger.debug("netstat is empty")
                return
            lines = ret.splitlines()
            for line in lines:
                if "LISTENING" in line:
                    logger.debug(line)
                    pid = line.split()[-1]
                    sub = subprocess.Popen('tasklist |findstr %s' % pid, stdout=subprocess.PIPE, shell=True)
                    ret = sub.stdout.read()
                    sub.wait()
                    process = ret.split()[0]
                    logger.debug("pid:%s ,process:%s occupy 5037 port" % (pid, process))
                    #                 DDMS会用到adb 杀了adb会导致 IDE调试或控制台可能不正常，后面需要改环境变量
                    subprocess.Popen("taskkill /T /F /PID %s" % pid, stdout=subprocess.PIPE, shell=True)
                    logger.debug("kill process %s" % process)
                    break
            else:
                logger.debug("don't have process occupy 5037")

    def _timer(self, process, timeout):
        '''进程超时器，监控adb同步命令执行是否超时，超时强制结束执行。当timeout<=0时，永不超时

        :param Popen process: 子进程对象
        :param int timeout: 超时时间
        '''
        num = 0
        while process.poll() == None and num < timeout * 10:
            num += 1
            time.sleep(0.1)
        if process.poll() == None:
            logger.warning("%d process timeout,force close" % process.pid)
            process.terminate()

    def _run_cmd_once(self, cmd, *argv, **kwds):
        '''执行一次adb命令：cmd

        :param str cmd: 命令字符串
        :param list argv: 可变参数
        :param dict kwds: 可选关键字参数 (超时/异步)
        :return: 执行adb命令的子进程或执行的结果
        :rtype: Popen or str
        '''
        import locale
        import codecs
        if self._device_id:
            cmdlet = [self._adb_path, '-s', self._device_id, cmd]
        else:
            cmdlet = [self._adb_path, cmd]
        for i in range(len(argv)):
            arg = argv[i]
            if not isinstance(argv[i], str):
                arg = arg.decode('utf8')
            cmdlet.append(arg)
        #        logger.debug('ADB cmd:' + " ".join(cmdlet))
        #         logger.debug(cmdlet)
        cmdStr = " ".join(cmdlet)
        logger.debug(cmdStr)
        process = None
        #       windows上 不要传cmdStr 目录有空格，会报错
        #         if ADB.os_name == "Windows":
        #             process = subprocess.Popen(cmdlet, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True)
        # #       mac上传list会报错:Android Debug Bridge version
        #         else:
        #         windows ["adb devices"] 提示没有命令 ，改为str执行
        process = subprocess.Popen(cmdStr, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   shell=True)
        if "sync" in kwds and kwds['sync'] == False:
            # 异步执行命令，不等待结果，返回该子进程对象
            return process
        before = time.time()
        timeout = 10
        if "timeout" in kwds:
            timeout = kwds['timeout']
        if timeout != None and timeout > 0:
            # timeout = None 或者小于等于0时，一直等待执行结果
            threading.Thread(None, self._timer, (process, timeout))
        (out, error) = process.communicate()
        # 执行错误 mac  out无输出 error有输出 返回值非0
        # 执行错误 windows out有输出 error没有输出，返回值0
        if process.poll() != 0:  # 返回码为非0，表示命令未执行成功返回
            # logger.logError("adb执行出错或超时，出错命令是：\n%s"%cmdlet)
            if error and len(error) != 0:
                logger.debug("adb error info:\n%s" % error)
            if "no devices/emulators found" in str(out) or "no devices/emulators found" in str(error):
                logger.error("no devices/emulators found,please reconnect phone,make sure adb shell normal")
                return ""
            #               退出整个进程
            if "killing" in str(out) or "killing" in str(error):
                logger.error(
                    "adb 5037 port is occupied,please stop the process occupied 5037 port,make sure adb devices normal")
                return ""
            if "device not found" in str(out) or "device not found" in str(error):
                logger.error("device not found,please reconnect phone,make sure adb devices normal")
                self.before_connect = False
                self.after_connect = False
                return ""
            if "offline" in str(out) or "offline" in str(error):
                logger.error("device offline,please reconnect phone,make sure adb devices normal")
                return ""
            if "more than one" in str(out) or "more than one" in str(error):
                logger.error("more than one device,please input device serialnum!")
                # sys.exit(1)
            if "Android Debug Bridge version" in str(out) or "Android Debug Bridge version" in str(error):
                logger.error("adb cmd error!:" + out)
                # sys.exit(1)
        if str(out, "utf-8") == '':
            # logger.debug("out is empty ,use error")
            out = error
        self.after_connect = True
        after = time.time()
        time_consume = after - before
        logger.info(cmdStr + " time consume: " + str(time_consume))
        if not isinstance(out, str):
            try:
                out = str(out, "utf8")
            except Exception as e:
                out = repr(out)
        return out.strip()

    def run_adb_cmd(self, cmd, *argv, **kwds):
        '''尝试执行adb命令

        :param str cmd: 命令字符串
        :param list argv: 可变参数
        :param dict kwds: 可选关键字参数 (超时/异步)
        :return: 执行adb命令的子进程或执行的结果
        :rtype: Popen or str
        '''
        retry_count = 3  # 默认最多重试3次
        if "retry_count" in kwds:
            retry_count = kwds['retry_count']
        while retry_count > 0:
            ret = self._run_cmd_once(cmd, *argv, **kwds)
            if ret != None:
                break
            retry_count = retry_count - 1
        return ret

    def run_shell_cmd(self, cmd, **kwds):
        '''执行 adb shell 命令
        '''
        # 如果失去连接后，adb又正常连接了
        if not self.before_connect and self.after_connect:
            cpu_uptime_file = os.path.join(RuntimeData.package_save_path, "uptime.txt")
            with open(cpu_uptime_file, "a+",encoding = "utf-8") as writer:
                writer.write(TimeUtils.getCurrentTimeUnderline() + " /proc/uptime:" + self.run_adb_cmd("shell cat /proc/uptime") + "\n")
            self.before_connect = True
        ret = self.run_adb_cmd('shell', '%s' % cmd, **kwds)
        # 当 adb 命令传入 sync=False时，ret是Poen对象
        if ret == None:
            logger.error(u'adb cmd failed:%s ' % cmd)
        return ret

    def _check_need_quote(self):
        cmd = 'su -c ls -l /data/data'
        result = self.run_shell_cmd(cmd)
        if result.find('com.android.phone') >= 0:
            self._need_quote = False
        else:
            self._need_quote = True

    def _logcat_thread_func(self, save_dir, process_list, params=""):
        '''获取logcat线程
                '''
        self.append_log_line_num = 0
        self.file_log_line_num = 0
        self.log_file_create_time = None
        logs = []
        logger.debug("logcat_thread_func")
        log_is_none = 0
        while self._logcat_running:
            try:
                log = self._log_pipe.stdout.readline().strip()
                if not isinstance(log, str):
                    try:
                        log = str(log,"utf8")
                    except Exception as e:
                        log = repr(log)
                        logger.error('str error:'+log)
                        logger.error(e)
                if log:
                    log_is_none = 0
                    # logger.debug(log)
                    logs.append(log)
                    # if self._log_pipe.poll() != None:
                    #     logger.debug('process:%s have exited' % self._log_pipe.pid)
                    #     if self._logcat_running :
                    #         self._log_pipe = self.run_shell_cmd('logcat ' + params, sync=False)
                    #     else :
                    #         break
                    for _handle in self._logcat_handle:
                        try:
                            _handle(log)
                        except Exception as e:
                            logger.error("an exception happen in logcat handle log , reason unkown!, e:")
                            logger.error(e)

                    self.append_log_line_num = self.append_log_line_num + 1
                    self.file_log_line_num = self.file_log_line_num + 1
                    # if self.append_log_line_num > 1000:
                    if self.append_log_line_num > 100:
                        if not self.log_file_create_time:
                            self.log_file_create_time = TimeUtils.getCurrentTimeUnderline()
                        logcat_file = os.path.join(save_dir,
                                                'logcat_%s.log' % self.log_file_create_time)
                        self.append_log_line_num = 0
                        self.save(logcat_file, logs)
                        logs = []
                    # 新建文件
                    if self.file_log_line_num > 600000:
                    # if self.file_log_line_num > 200:
                        self.file_log_line_num = 0
                        self.log_file_create_time = TimeUtils.getCurrentTimeUnderline()
                        logcat_file = os.path.join(save_dir, 'logcat_%s.log' % self.log_file_create_time)
                        self.save(logcat_file, logs)
                        logs = []
                else:
                    log_is_none = log_is_none + 1
                    if log_is_none % 1000 == 0:
                        logger.info("log is none")
                        self._log_pipe = self.run_shell_cmd('logcat -v threadtime ' + params, sync=False)
            except:
                logger.error("an exception hanpend in logcat thread, reason unkown!")
                s = traceback.format_exc()
                logger.debug(s)

    def save(self, save_file_path, loglist):
        logcat_file = os.path.join(save_file_path)
        with open(logcat_file, 'a+',encoding="utf-8") as logcat_f:
            for log in loglist:
                logcat_f.write(log + "\n")


    def start_logcat(self, save_dir, process_list=[], params=''):
        '''运行logcat进程

        :param list process_list: 要捕获日志的进程名或进程ID列表，为空则捕获所有进程,输入 ['system_server']可捕获系统进程的日志
        :param str params: 参数
        '''
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        if hasattr(self, '_logcat_running') and self._logcat_running == True:
            logger.warning('logcat process have started,not need start')
            return
        # sdk 26一下可以执行logcat -c的操作， 8.0以上的系统不能执行，会报"failed to clear the 'main' log"的错 图兰朵没问题
        # if self.get_sdk_version() <  26:
        try:  # 有些机型上会报permmison denied，但是logcat -c的代码仍会部分执行，所以加try 保护
            self.run_shell_cmd('logcat -c ' + params)  # 清除缓冲区
        except RuntimeError as e:
            logger.warning(e)
        self._logcat_running = True  # logcat进程是否启动
        self._log_pipe = self.run_shell_cmd('logcat -v threadtime ' + params, sync=False)
        self._logcat_thread = threading.Thread(target=self._logcat_thread_func, args=[save_dir, process_list, params])
        self._logcat_thread.setDaemon(True)
        self._logcat_thread.start()

    def stop_logcat(self):
        '''停止logcat进程
        '''
        self._logcat_running = False
        logger.debug("stop logcat")
        if hasattr(self, '_log_pipe'):
            if self._log_pipe.poll() == None:  # 判断logcat进程是否存在
                self._log_pipe.terminate()

    def wait_for_device(self, timeout=180):
        '''等待设备连接
        '''
        if not self.run_adb_cmd("wait-for-device", timeout=180):
            logger.warning("adb wait-for-device timeout")
            return False
        return True

    def bugreport(self, save_path):
        '''adb bugreport ~/Downloads/bugreport.zip
        '''
        result = self.run_adb_cmd('bugreport', save_path, timeout=180)
        return result

    def push_file(self, src_path, dst_path):
        '''拷贝文件到手机中

        :param str src_path: 原文件路径
        :param str dst_path: 拷贝到的文件路径
        :return: 执行adb push命令的子进程或执行的结果
        :rtype: Popen or str
        '''
        file_size = os.path.getsize(src_path)
        # 处理路径空格，加上双引号
        if " " in src_path:
            src_path = '"' + src_path + '"'
        for i in range(3):
            result = self.run_adb_cmd('push', src_path, dst_path, timeout=30)
            if result.find('No such file or directory') >= 0:
                logger.error('file:%s not exist' % src_path)
            if ('%d' % file_size) in result:
                return result
        logger.error(u'push file failed:%s' % result)

    def pull_file(self, src_path, dst_path):
        '''从手机中拉取文件
        '''
        result = self.run_adb_cmd('pull', src_path, dst_path, timeout=180)
        if result and 'failed to copy' in result:
            logger.error("failed to pull file:" + src_path)
        return result

    def pull_file_between_time(self, src_path, dst_path, start_timestamp, end_timestamp):
        '''
        提取/data/anr 目录下 在起止时间戳之间的文件
        :return:
        '''
        # 在PC上创建目录
        dst_path = os.path.join(dst_path, src_path.split("/")[-1])
        FileUtils.makedir(dst_path)
        for src_file_path in self.list_dir_between_time(src_path, start_timestamp, end_timestamp):
            self.pull_file(src_file_path, dst_path)

    def screencap_out(self,pc_save_path):
        result = self.run_adb_cmd('exec-out screencap -p %s'%pc_save_path, timeout=20)
        return result

    def screencap(self,save_path):
        result = self.run_shell_cmd('screencap -p %s'%save_path, timeout=20)
        return result

    def delete_file(self, file_path):
        '''删除手机上文件
        '''
        self.run_shell_cmd('rm %s' % file_path)

    def delete_folder(self, folder_path):
        '''删除手机上的目录
        '''
        self.run_shell_cmd('rm -R %s' % folder_path)

    def check_path_size(self, folder_path, ratio):
        '''检测手机上目录空间占比，超过多少比例
        '''
        out = self.run_shell_cmd('df %s' % folder_path)
        logger.debug(out)
        if out:
            lines = out.replace('\r', '').splitlines()
            occupy_ratio = lines[1].split()[4].replace("%", "")
            logger.debug(occupy_ratio)
            if int(occupy_ratio) > ratio:
                return True
        # df /data
        # Filesystem 1K - blocks Used Available Use% Mounted on
        # /dev/block/mmcblk0p22 1822444 752240 1070204 42% /data
        return False

    def is_exist(self, path):
        '''
        判断文件或文件夹是否存在
        :param path:
        :return:
        '''
        result = self.run_shell_cmd('ls -l %s' % path)
        if not result:
            return False
        result = result.replace('\r\r\n', '\n')
        if 'No such file or directory' in result:
            return False
        return True

    def mkdir(self, folder_path):
        '''
        在设备上创建目录
        :param folder_path:
        :return:
        '''
        self.run_shell_cmd('mkdir %s' % folder_path)

    def list_dir(self, dir_path):
        '''列取目录下文件 文件夹
        返回 文件名 列表
        '''
        result = self.run_shell_cmd('ls -l %s' % dir_path)
        if not result:
            return ""
        result = result.replace('\r\r\n', '\n')
        if 'No such file or directory' in result:
            logger.error('文件(夹) %s 不存在' % dir_path)
        file_list = []
        for line in result.split('\n'):
            items = line.split()
            # total 180 去掉total这行
            if items[0] != "total" and len(items) != 2:
                file_list.append(items[-1])
        return file_list

    def list_dir_between_time(self, dir_path, start_time, end_time):
        '''列取目录下 起止时间点之间的文件
            start_time end_time 时间戳
            返回文件绝对路径 列表
        '''
        # ls - l
        # -rwxrwx--- 1 root root 19897899 2018-12-27 18:02 com.alibaba.ailabs.ar.fireeye2_dumpheap_2018_12_27_18_02_52.hprof

        result = self.run_shell_cmd('ls -l %s' % dir_path)
        if not result:
            return ""
        result = result.replace('\r\r\n', '\n')
        if 'No such file or directory' in result:
            logger.error('文件(夹) %s 不存在' % dir_path)
        file_list = []

        re_time = re.compile(r'\S*\s+(\d+-\d+-\d+\s+\d+:\d+)\s+\S+')

        for line in result.split('\n'):
            items = line.split()
            match = re_time.search(line)
            if match:
                last_modify_time = match.group(1)
                logger.debug(last_modify_time)
                last_modify_timestamp = TimeUtils.getTimeStamp(last_modify_time, "%Y-%m-%d %H:%M")
                # logger.debug(last_modify_timestamp)
                if start_time < last_modify_timestamp and last_modify_timestamp < end_time:
                    logger.debug("append file:" + items[-1])
                    file_list.append('%s/%s' % (dir_path, items[-1]))
        return file_list

    def is_overtime_days(self, filepath, days=7):
        result = self.run_shell_cmd('ls -l %s' % filepath)
        if not result:
            return False
        result = result.replace('\r\r\n', '\n')
        if 'No such file or directory' in result:
            logger.error('文件(夹) %s 不存在' % filepath)
            return False
        re_time = re.compile(r'\S*\s+(\d+-\d+-\d+\s+\d+:\d+)\s+\S+')
        match = re_time.search(result)
        if match:
            last_modify_time = match.group(1)
            logger.debug(last_modify_time)
            last_modify_timestamp = TimeUtils.getTimeStamp(last_modify_time, "%Y-%m-%d %H:%M")
            # logger.debug(last_modify_timestamp)
            if last_modify_timestamp < (time.time() - days * 24 * 60 * 60):
                logger.debug(filepath + " is overtime days:" + str(days))
                return True
            else:
                logger.debug(filepath + " is not overtime days:" + str(days))
                return False
        logger.debug(filepath + " not have match time formatter")
        return False

    def start_activity(self, activity_name, action='', data_uri='', extra={}, wait=True):
        '''打开一个Activity
        '''
        if action != '':  # 指定Action
            action = '-a %s ' % action
        if data_uri != '':
            data_uri = '-d %s ' % data_uri
        extra_str = ''
        for key in extra.keys():  # 指定额外参数
            extra_str += '-e %s %s ' % (key, extra[key])
        W = ''
        if wait: W = '-W'  # 等待启动完成才返回

        result = self.run_shell_cmd('am start %s -n %s %s %s %s' % (W, activity_name, action, data_uri, extra_str),
                                    timeout=30, retry_count=1)
        ret_dict = {}
        for line in result:
            if ': ' in line:
                key, value = line.split(': ')
                ret_dict[key] = value
        return ret_dict

    def get_focus_activity(self):
        '''
        通过dumpsys window windows获取activity名称  window名?
        '''
        activity_name = ''
        activity_line = ''
        activity_line_split = ''
        dumpsys_result = self.run_shell_cmd('dumpsys window windows')
        dumpsys_result_list = dumpsys_result.split('\n')
        for line in dumpsys_result_list:
            if line.find('mCurrentFocus') != -1:
                activity_line = line.strip()
        #      Android

        #         Android 8.0 mCurrentFocus的输出行
        #         mCurrentFocus=Window{2f4cb8b u0 com.google.android.apps.photos/com.google.android.apps.photos.home.HomeActivity}
        if activity_line:
            activity_line_split = activity_line.split(' ')
        else:
            return activity_name
        logger.debug('dumpsys window windows命令activity_line_split结果: %s' % activity_line_split)
        if len(activity_line_split) > 1:
            if activity_line_split[1] == 'u0':
                activity_name = activity_line_split[2].rstrip('}')
            else:
                activity_name = activity_line_split[1]
        return activity_name

    def get_foreground_process(self):
        '''
        :return: 当前前台进程名,对get_focus_activity的返回结果加以处理
        '''
        focus_activity = self.get_focus_activity()
        if focus_activity:
            return focus_activity.split("/")[0]
        else:
            return ""

    def get_current_activity(self):
        '''获取当前activity名
        '''
        if self.get_sdk_version() < 26:  # android8.0以下优先选择dumpsys activity top获取当前的activity
            current_activity = self.get_top_activity_with_activity_top()
            if current_activity:
                return current_activity
            current_activity = self.get_top_activity_with_usagestats()
            if current_activity:
                return current_activity
            return None
        else:  # android 8.0以上优先根据dumsys usagestats来获取当前的activity
            current_activity = self.get_top_activity_with_usagestats()
            if current_activity:
                return current_activity
            current_activity = self.get_top_activity_with_activity_top()
            if current_activity:
                return current_activity

    def get_top_activity_with_activity_top(self):
        '''通过dumpsys activity top 获取当前activity名
        '''
        ret = self.run_shell_cmd("dumpsys activity top")
        if not ret:
            return None
        lines = ret.split("\n")
        top_activity = ""
        for line in lines:
            if "ACTIVITY" in line:
                line = line.strip()
                logger.debug("dumpsys activity top info line :" + line)
                activity_info = line.split()[1]
                if "." in line:
                    top_activity = activity_info.replace("/", "")
                else:
                    top_activity = activity_info.split("/")[1]
                logger.debug("dump activity top activity:" + top_activity)
                return top_activity
        return top_activity

    def get_top_activity_with_usagestats(self):
        '''通过dumpsys usagestats获取当前activity名
        '''
        top_activity = ""
        ret = self.run_shell_cmd("dumpsys usagestats")
        if not ret:
            return None
        last_activity_line = ""
        lines = ret.split("\n")
        for line in lines:
            if "MOVE_TO_FOREGROUND" in line:
                last_activity_line = line.strip()
        logger.debug("dumpsys usagestats MOVE_TO_FOREGROUND lastline :" + last_activity_line)
        if len(last_activity_line.split("class=")) > 1:
            top_activity = last_activity_line.split("class=")[1]
            if " " in top_activity:
                top_activity = top_activity.split()[0]
        logger.debug("dumpsys usagestats top activity:" + top_activity)
        return top_activity

    # turandot测试通过
    # android手机测试通过
    def get_pid_from_pck(self, package_name):
        '''
        从ps信息中通过匹配包名，获取进程pid号，对于双开应用统计值会返回两个不同的pid后面再优化
        :param pckname: 应用包名
        :return: 该进程的pid
        '''
        # 跟 get_process_pids 有点区别 这个返回主进程名的pid
        pckinfo_list = self.get_pckinfo_from_ps(package_name)
        if pckinfo_list:
            return pckinfo_list[0]["pid"]

    def get_pckinfo_from_ps(self, packagename):
        '''
            从ps中获取应用的信息:pid,uid,packagename
            :param packagename: 目标包名
            :return: 返回目标包名的列表信息
            '''
        ps_list = self.list_process()
        pck_list = []
        for item in ps_list:
            if item["proc_name"] == packagename:
                pck_list.append(item)
        return pck_list

    def get_process_stack(self, package_name, save_path):
        '''
        :param package_name: 进程名
        :param save_path: 堆栈文件保持路径
        :return: 无
        '''
        pid = self.get_pid_from_pck(package_name)
        return self.run_shell_cmd("debuggerd -b %s > %s" % (pid, save_path))

    def get_process_stack_from_pid(self, pid, save_path):
        '''
        :param package_name: 进程名
        :param save_path: 堆栈文件保存路径
        :return: 无
        '''
        return self.run_shell_cmd("debuggerd -b %s > %s" % (pid, save_path))

    def dumpheap(self, package, save_path):
        heapfile = "/data/local/tmp/%s_dumpheap_%s.hprof" % (package, TimeUtils.getCurrentTimeUnderline())
        self.run_shell_cmd("am dumpheap %s %s" % (package, heapfile))
        time.sleep(10)
        self.pull_file(heapfile,save_path)

    def dump_native_heap(self, package, save_path):
        native_heap_file = "/data/local/tmp/%s_native_heap_%s.txt" % (package, TimeUtils.getCurrentTimeUnderline())
        self.run_shell_cmd("am dumpheap -n %s %s" % (package, native_heap_file))

    def clear_data(self, packagename):
        '''清除指定包的 用户数据
        '''
        return self.run_shell_cmd("pm clear %s" % packagename)

    def stop_package(self, packagename):
        '''杀死指定包的进程
        '''
        return self.run_shell_cmd("am force-stop %s" % packagename)

    def input(self, string):
        return self.run_shell_cmd("input text %s" % string)

    def ping(self, address, count):
        return self.run_shell_cmd("shell ping -c %d %s" % (count, address), timeout=None)

    def get_system_version(self):
        '''获取系统版本，如：4.1.2
        '''
        if not self._system_version:
            self._system_version = self.run_shell_cmd("getprop ro.build.version.release")
        return self._system_version

    def get_genie_uuid(self):
        '''获取天猫精灵uuid，如：F51823A6DCC13AA8FDFAA78B3D124DC3
        '''
        uuid = self.run_shell_cmd("getprop ro.genie.uuid")
        if uuid:
            return uuid
        else:
            return ""

    def get_genie_wifi(self):
        '''获取天猫精灵wifi mac 地址，如：38:d2:ca:b7:00:6d
        '''
        wifi_mac = self.run_shell_cmd("cat /sys/class/net/wlan0/address")
        if wifi_mac:
            return wifi_mac
        else:
            return ""

    def get_package_ver(self, package):
        '''获取应用版本信息
        '''
        package_ver = self.run_shell_cmd("dumpsys package " + package)
        if package_ver:
            return package_ver
        else:
            return ""

    def get_sdk_version(self):
        '''获取SDK版本，如：16
        '''
        if not self._sdk_version:
            self._sdk_version = int(self.run_shell_cmd('getprop ro.build.version.sdk'))
        return self._sdk_version

    def get_phone_brand(self):
        '''获取手机品牌  如：Mi Samsung OnePlus
        '''
        if not self._phone_brand:
            self._phone_brand = self.run_shell_cmd('getprop ro.product.brand')
        return self._phone_brand

    def get_phone_model(self):
        '''获取手机型号  如：A0001 M2S
        '''
        if not self._phone_model:
            self._phone_model = self.run_shell_cmd('getprop ro.product.model')
        return self._phone_model

    def get_screen_size(self):
        '''获取屏幕大小  如：5.5 可能获取不到
        '''
        return self.run_shell_cmd('getprop ro.product.screensize')

    def get_wm_size(self):
        '''获取屏幕分辨率  如：Physical size:1080*1920
        '''
        return self.run_shell_cmd('wm size')

    def get_cpu_abi(self):
        '''获取系统的CPU架构信息

        :return: 返回系统的CPU架构信息
        :rtype: str
        '''
        return self.run_shell_cmd('getprop ro.product.cpu.abi')

    def find_tag_index(self, tag, line):
        '''查找指定的 tag 在一行中以空白分隔的下标
        '''
        tag = tag.strip()
        data = line.split()
        index = 0
        for item in data:
            if tag.lower() == item.lower():
                return index
            index = index + 1

    def get_device_imei(self):
        '''获取手机串号
        '''
        result = self.run_shell_cmd('dumpsys iphonesubinfo')
        result = result.replace('\r\r\n', '\n')
        for line in result.split('\n'):
            if line.find('Device ID') >= 0:
                return line.split('=')[1].strip()
        logger.error('获取imei号失败：%r' % result)

    def get_process_pids(self, process_name):
        '''查找包含指定进程名的进程PID
        '''
        pids = []
        process_list = self.list_process()
        for process in process_list:
            if process['proc_name'] == process_name:
                pids.append(process['pid'])
        return pids

    def is_process_running(self, process_name):
        '''判断进程是否存活
        '''
        process_list = self.list_process()
        for process in process_list:
            if process['proc_name'] == process_name:
                return True
        return False

    def get_uid(self, app_name):
        '''获取APP的uid
        '''
        result = self.run_shell_cmd('cat /data/system/packages.list')
        result = result.replace('\r\r\n', '\n')
        for line in result.split('\n'):
            items = line.split(' ')
            if items[0] == app_name:
                return items[1]
        return None

    def getUID(self, pkg):
        '''
        获取app的uid
        :param pkg:
        :return:
        '''
        uid = None
        _cmd = 'dumpsys package %s' % pkg
        out = self.run_shell_cmd(_cmd)
        lines = out.replace('\r', '').splitlines()
        if len(lines) > 0:
            for line in lines:
                if "Unable to find package:" in line:
                    return None
            adb_result = re.findall(u'userId=(\d+)', out)
            if len(adb_result) > 0:
                uid = adb_result[0]
                logger.debug("getUid for pck: " + pkg + ", UID: " + uid)
        else:
            return None
        return uid

    def is_app_installed(self, package):
        '''
        判断app是否安装
        '''
        if package in self.list_installed_app():
            return True
        else:
            return False

    def list_installed_app(self):
        '''
                        获取已安装app列表
        :return: 返回app列表
        :rtype: list
        '''
        result = self.run_shell_cmd('pm list packages')
        result = result.replace('\r', '').splitlines()
        logger.debug(result)
        installed_app_list = []
        for app in result:
            if not 'package' in app: continue
            if app.split(':')[0] == 'package':
                # 只获取连接正常的
                installed_app_list.append(app.split(':')[1])
        logger.debug(installed_app_list)
        return installed_app_list

    def list_process(self):
        '''获取进程列表
        '''
        # <= 7.0 用ps, >=8.0 用ps -A android8.0 api level 26
        result = None
        if self.get_sdk_version() < 26:
            result = self.run_shell_cmd('ps')  # 不能使用grep
        else:
            result = self.run_shell_cmd('ps -A')  # 不能使用grep
        result = result.replace('\r', '')
        lines = result.split('\n')
        busybox = False
        if lines[0].startswith('PID'): busybox = True

        result_list = []
        for i in range(1, len(lines)):
            items = lines[i].split()
            if not busybox:
                if len(items) < 9:
                    err_msg = "ps命令返回格式错误：\n%s" % lines[i]
                    if len(items) == 8:
                        result_list.append({'uid':items[0],'pid': int(items[1]), 'ppid': int(items[2]),
                                            'proc_name': items[7],'status': items[-2]})
                    else:
                        logger.error(err_msg)
                else:
                    result_list.append({'uid': items[0],'pid': int(items[1]), 'ppid': int(items[2]),
                                        'proc_name': items[8],'status': items[-2]})
            else:
                idx = 4
                cmd = items[idx]
                if len(cmd) == 1:
                    # 有时候发现此处会有“N”
                    idx += 1
                    cmd = items[idx]
                idx += 1
                if cmd[0] == '{' and cmd[-1] == '}': cmd = items[idx]
                ppid = 0
                if items[1].isdigit(): ppid = int(items[1])  # 有些版本中没有ppid
                result_list.append({'pid': int(items[0]), 'uid': items[1],'ppid': ppid,
                                    'proc_name': cmd,'status': items[-2]})
        return result_list

    def kill_process(self, process_name):
        '''杀死包含指定进程
        '''
        pids = self.get_process_pids(process_name)
        if pids:
            self.run_shell_cmd('kill ' + ' '.join([str(pid) for pid in pids]))
        return len(pids)

    def wait_proc_exit(self, proc_list, timeout=10):
        '''等待指定进程退出
        :param proc_list: 进程名列表
        '''
        if not isinstance(proc_list, list):
            logger.error('proc_list参数要求list类型')
        time0 = time.time()
        while time.time() - time0 < timeout:
            flag = True
            proc_list = self.list_process()
            for proc in proc_list:
                if proc['proc_name'] in proc_list:
                    flag = False
                    break
            if flag == True: return True
            time.sleep(1)
        return False

    def forward(self, port1, port2, type='tcp'):
        '''端口转发
        :param port1: PC上的TCP端口
        :type port1:  int
        :param port2: 手机上的端口或LocalSocket地址
        :type port2:  int或String
        :param type:  手机上的端口类型
        :type type:   String，LocalSocket地址使用“localabstract”
        '''
        ret = self.run_adb_cmd('forward', 'tcp:%d' % port1, '%s:%s' % (type, port2))
        if ret == None:
            return False
        return True

    def reboot(self, boot_type=None):
        '''重启手机
        boot_type: "bootloader", "recovery", or "None".
        '''
        if not boot_type:
            self.run_adb_cmd('reboot ' + boot_type)
        else:
            self.run_adb_cmd('reboot')

    def _copy_set_propex(self):
        cpu_abi = self.get_cpu_abi()
        dstpath = r'/data/local/tmp/setpropex'
        srcpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), u'tools', cpu_abi, u'setpropex')
        self.push_file(srcpath, dstpath)

    def set_secure_property(self):
        '''通过setpropex设置手机安全属性(发布版手机默认安全属性无法打开ViewServer)
        '''
        self._copy_set_propex()
        self.run_shell_cmd('chmod 777 /data/local/tmp/setpropex', timeout=10)
        self.run_shell_cmd('./data/local/tmp/setpropex ro.secure 0', timeout=10)
        self.run_shell_cmd('./data/local/tmp/setpropex ro.debuggable 1', timeout=10)

    def _install_apk(self, apk_path, over_install=True, downgrade=False):
        '''
        '''
        timeout = 3 * 60  # TODO: 确认3分钟是否足够
        tmp_path = '/data/local/tmp/' + os.path.split(apk_path)[-1]
        self.push_file(apk_path, tmp_path)
        cmdline = 'pm install %s %s %s' % ('-r -t' if over_install else '', "-d" if downgrade else "", tmp_path)
        ret = ''
        for i in range(3):
            # TODO: 处理一些必然会失败的情况，如方法数超标之类的问题
            try:
                ret = self.run_shell_cmd(cmdline, retry_count=1, timeout=timeout)  # 使用root权限安装，可以在小米2S上不弹出确认对话框
                logger.debug(ret)
                if i > 1 and 'INSTALL_FAILED_ALREADY_EXISTS' in ret:
                    # 出现至少一次超时，认为安装完成
                    ret = 'Success'
                    break

                if 'INSTALL_PARSE_FAILED_NO_CERTIFICATES' in ret or \
                        'INSTALL_FAILED_INSUFFICIENT_STORAGE' in ret:
                    raise RuntimeError('安装应用失败：%s' % ret)

                if 'INSTALL_FAILED_UID_CHANGED' in ret:
                    logger.error(ret)
                    # /data/data目录下存在文件夹没有删除
                    # package_name = self._get_package_name(apk_path)
                    # dir_path = '/data/data/%s' % package_name
                    # for _ in range(3):
                    #     # 防止删除没有成功
                    #     self.delete_folder(dir_path)
                    #     if 'No such file or directory' in self.run_root_shell_cmd('ls -l %s' % dir_path): break
                    continue
                if 'Success' in ret or 'INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES' in ret or \
                        'INSTALL_FAILED_ALREADY_EXISTS' in ret: break
            except:
                if i >= 2:
                    logger.warning('install app failed')
                    ret = self.run_shell_cmd(cmdline, timeout=timeout)  # 改用非root权限安装
                    logger.debug(ret)
                    if ret and 'INSTALL_FAILED_ALREADY_EXISTS' in ret:
                        ret = 'Success'
        try:
            self.delete_file('/data/local/tmp/*.apk')
        except:
            pass
        return ret

    def install_apk(self, apk_path, over_install=True, downgrade=False):
        '''安装应用
            apk_path 安装包路径
            over_install:是否覆盖暗账
            downgrade:是否允许降版本安装
        '''
        if not over_install:
            # package_name = self._get_package_name(apk_path)
            # self.uninstall_apk(package_name)  # 先卸载，再安装
            result = self._install_apk(apk_path, over_install, downgrade)
        else:
            result = self._install_apk(apk_path, over_install, downgrade)
        # logger.debug(result)
        if 'INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES' in result:
            # 必须卸载安装
            return self.install_apk(apk_path, False, False)
        elif 'INSTALL_FAILED_ALREADY_EXISTS' in result:
            # 卸载成功依然有可能在安装时报这个错误
            return self.install_apk(apk_path, False, True)
        return result.find('Success') >= 0

    def uninstall_apk(self, pkg_name):
        '''卸载应用
        '''
        result = self.run_adb_cmd('uninstall %s' % pkg_name, timeout=30)
        return result.find('Success') >= 0


class AndroidDevice():
    '''封装Android设备基本操作
    '''

    def __init__(self, device_id=None):
        self.adb = None
        self.is_local = AndroidDevice.is_local_device(device_id)
        #         现阶段暂时直接使用本地定义的adb
        if self.is_local:
            self.adb = ADB(device_id)

    @staticmethod
    def is_local_device(device_id):
        '''通过device_id判断是否本地设备
           -本地真机设备，device_id格式为：serialNumber
           -本地虚拟设备，device_id格式为：hostname:portNumber
           -远程设备，device_id格式为：hostname:serialNumber
        '''
        if not device_id:
            return True
        pattern = re.compile(r'([\w|\-|\.]+):(.+)')
        mat = pattern.match(device_id)
        if not mat or (mat.group(2).isdigit() and int(mat.group(2)) > 1024 and int(mat.group(2)) < 65536):
            return True
        else:
            return False

    @staticmethod
    def list_local_devices():
        '''获取设备列表
        '''
        return ADB.list_device()


if __name__ == '__main__':
    device = AndroidDevice("WST4DYVWKBFEV8Q4")
    cmd = "cat /sys/class/net/wlan0/address"
    cmd = "ls /data/local/tmp"
    # ret  = device.adb.run_shell_cmd(cmd)
    # ret  = device.adb.push_file("/Users/look/Desktop/audio_auto_test/autoTestPlatform_Gagent/results/2020_02_22_20_27_27中文/2020_02_22_20_27的副本.ogg","/sdcard/ogg")
    # ret  = device.adb.push_file("/Users/look/Desktop/audio_auto_test/autoTestPlatform_Gagent/results/2020_02_22_20_23_50 0/2020_02_22_20_3.ogg","/sdcard/ogg")
    # print(ret)
    # if "om.alibaba.ailabs.genie.smartap" in ret:
    #     print("true")
    # logger.debug(device.adb.get_genie_wifi())
    # print device.adb.get_cpu_abi()
    # print device.adb.get_device_imei()
    # print device.adb.get_system_version()
    # print device.adb.list_installed_app()
    # print device.adb.get_focus_activity()
    # print device.adb.get_current_activity()
    # foreground_process = device.adb.get_foreground_process()

    current_time = time.time()
    ogg_path = "/Users/look/Desktop/audio_auto_test/autoTestPlatform_Gagent/results"
    results_file_list = os.listdir(ogg_path)
    import shutil

    for result_file in results_file_list:
        # 获取文件创建时间戳
        result_path = os.path.join(ogg_path, result_file)
        create_timestamp = os.path.getctime(result_path)
        # 如果超过一天时间，清理
        if current_time - create_timestamp > 24 * 60 * 60:
            logger.debug("rm :" + result_path)
            shutil.rmtree(result_path)