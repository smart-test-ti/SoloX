#!/usr/bin/python
# encoding=utf-8

"""
@Author  :  Lijiawei
@Date    :  2022/6/19
@Desc    :  adb line.
@Update  :  2022/7/14 by Rafa chen
"""
import os
import platform
import stat
import subprocess

STATICPATH = os.path.dirname(os.path.realpath(__file__))
DEFAULT_ADB_PATH = {
    "Windows": os.path.join(STATICPATH, "adb", "windows", "adb.exe"),
    "Darwin": os.path.join(STATICPATH, "adb", "mac", "adb"),
    "Linux": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-x86_64": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-armv7l": os.path.join(STATICPATH, "adb", "linux_arm", "adb"),
}


def make_file_executable(file_path):
    """
    If the path does not have executable permissions, execute chmod +x
    :param file_path:
    :return:
    """
    if os.path.isfile(file_path):
        mode = os.lstat(file_path)[stat.ST_MODE]
        executable = True if mode & stat.S_IXUSR else False
        if not executable:
            os.chmod(file_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True
    return False


def builtin_adb_path():
    """
    Return built-in adb executable path

    Returns:
        adb executable path

    """
    system = platform.system()
    machine = platform.machine()
    adb_path = DEFAULT_ADB_PATH.get('{}-{}'.format(system, machine))
    proc = subprocess.Popen('adb devices', stdout=subprocess.PIPE, shell=True)
    result = proc.stdout.read()
    if not isinstance(result, str):
        result = str(result, 'utf-8')
    if result and "command not found" not in result:
        adb_path = "adb"
        return adb_path

    if not adb_path:
        adb_path = DEFAULT_ADB_PATH.get(system)
    if not adb_path:
        raise RuntimeError("No adb executable supports this platform({}-{}).".format(system, machine))

    # overwrite uiautomator adb
    if "ANDROID_HOME" in os.environ:
        del os.environ["ANDROID_HOME"]
    if system != "Windows":
        # chmod +x adb
        make_file_executable(adb_path)
    return adb_path


class ADB(object):

    def __init__(self):
        self.adb_path = builtin_adb_path()

    def shell(self, cmd, deviceId):
        run_cmd = f'{self.adb_path} -s {deviceId} shell {cmd}'
        result = subprocess.Popen(run_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[
            0].decode("utf-8").strip()
        return result


adb = ADB()
