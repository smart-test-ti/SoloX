#encoding:utf-8
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import csv
import os
import re
import threading

import time

import sys
import traceback

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))
from mobileperf.android.tools.androiddevice import AndroidDevice
from mobileperf.common.utils import TimeUtils
from mobileperf.common.log import logger
from mobileperf.android.globaldata import RuntimeData
import sys



class TrafficUtils(object):
    @staticmethod
    def getUID(device, pkg):
        """"""
        uid = None
        _cmd = 'dumpsys package %s' % pkg
        out = device.adb.run_shell_cmd(_cmd)
        lines = out.replace('\r', '').splitlines()
        logger.debug("line length：" + str(len(lines)))
        if len(lines) > 0:
            for line in lines:
                if "Unable to find package:" in line:
                    logger.error(" trafficstat: Unable to find package : " + pkg)
                    continue
            adb_result = re.findall(u'userId=(\d+)', out)
            if len(adb_result) > 0:
                uid = adb_result[0]
                logger.debug("getUid for pck: " + pkg + ", UID: " + uid)
        else:
            logger.error(" trafficstat: Unable to find package : " + pkg)
        return uid

    @staticmethod
    def byte2kb(value):
        return round(value/1024.0,2)

    # def write
'''
现在可以获取到每个uid的整体的流量,包括上行和下行的流量，至于具体的移动流量还是wifi的流量由于不同的机型，网络接口的名称不统一，所以获取有问题，android系统有在
NetworkStatsService 中预留一个接口getMobileIfaces，返回了数据流量的所有网络接口，具体实现是注册一个观察者，只要其他的地方注册了数据的接口，就通知系统向这个mobile中
添加这个数据类型，从而可以获取到数据流量的所有类型，目前adb的方法没有找到办法可以做区分，可以在以后的java的sdk代码中实现wifi和数据的区分的代码，后续TODO
update:网络接口可以从cat /proc/net/xt_qtaguid/iface_stat就是不知道wifi和数据的怎么区分，后面TODO
'''
class TrafficSnapshot(object):
    '''
    当前从/proc/net/xt_qtaguid/stats获取的是从手机开机开始的流量，当手机重启后，所有的数据将被清零，所以可能得考虑数据的持久化
    '''
    def __init__(self, source, packagename, uid):
        self.source = source
        self.uid = uid
        self.packagename = packagename
        self.rx_uid_bytes = 0#/proc/net/xt_qtaguid/iface_stat第六个，表示下行数据
        self.rx_uid_packets = 0#第七个，上行的包个数
        self.tx_uid_bytes = 0#第八个
        self.tx_uid_packets = 0#第九个
        self.total_uid_bytes = 0#该uid从开机到现在的总流量，包含本地流量,目前使用的long，可能会溢出，需要优化
        self.total_uid_packets = 0
        self.lo_uid_bytes = 0#该uid的本地流量
        self.bg_bytes = 0#这个uid的后台流量
        self.fg_bytes = 0#这个uid从开机到现在开始的前台流量
        self._parse()


    def _parse(self):
        sp_lines = self.source.split('\n')
        for line in sp_lines:
            if self.uid and self.uid in line:
                # logger.debug("     target uid : "+str(self.uid))
                tart_list = line.split()
                tag = tart_list[2]
                # logger.debug("         tag is： " +tag)
                if tag == '0x0':#tag即acct_tag_hex这一列，默认是0，表示与这个uid关联的流量，有时候用户需要在自己的uid内添加一个其他
                    # tag表示这个模块中的子模块的流量，就可以通过setThreadTag
                    # logger.debug("        tart_list: " + str(tart_list))
                    self.rx_uid_bytes += int(tart_list[5])#不区分网络的类型，直接算总和,wifi和mobile, lo数据的总和
                    # logger.debug(self.rx_uid_bytes)
                    self.rx_uid_packets += int(tart_list[6])
                    self.tx_uid_bytes += int(tart_list[7])
                    self.tx_uid_packets += int(tart_list[8])
                    self.total_uid_bytes = self.tx_uid_bytes + self.rx_uid_bytes
                    self.total_uid_packets = self.tx_uid_packets + self.rx_uid_packets
                    if (tart_list[1] == 'lo'):#对应着iface这列，表示本地流量
                        self.lo_uid_bytes += int(tart_list[5] ) + int(tart_list[7])
                        # logger.debug("       lo_uid_bytes: " + str(self.lo_uid_bytes))
                    if(int(tart_list[4]) == 0):#统计后台流量
                        self.bg_bytes += int(tart_list[5] ) + int(tart_list[7])
                        # logger.debug("       backgroud data ： " +str(self.bg_bytes))
                    elif(int(tart_list[4]) == 1):#统计前台流量
                        self.fg_bytes += int(tart_list[5] ) + int(tart_list[7])
                        # logger.debug("        fg data: " +str(self.fg_bytes))

        logger.debug(" total uid  bytes : "+str(self.total_uid_bytes))

    def __repr__(self):
        return "TrafficSnapshot, " + "package: " +str(self.packagename) + " uid bytes: " + str(self.total_uid_bytes) + " uid pcket byte: " + str(self.total_uid_packets)

class NetDevInfo(object):
    '''
    解析proc/net/dev 结果 解析/proc/%d/net/dev 结果 输出格式一样
    示例结果
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

    '''
    def __init__(self, source):
        self.source = source
        self.mobile_total = 0
        self.mobile_rx = 0
        self.mobile_tx = 0
        self.wifi_total = 0
        self.wifi_rx = 0
        self.wifi_tx = 0
        self.total = 0
        self.rx = 0
        self.tx = 0
        self._parse()


    def _parse(self):
        sp_lines = self.source.split('\n')
        for line in sp_lines:
            # wlan0: 1241508864 840739 0 0 0 0 0 7 7149177 73416 0 6 0 0 0 0
            # 获取其中 接受流量1241508864 发送流量7149177
            if "wlan0:" in line:
                items = line.split()
                self.wifi_rx = int(items[1])
                self.wifi_tx = int(items[9])
                self.wifi_total = self.wifi_rx + self.wifi_tx
                logger.debug("wifi_rx : "+items[1]+" wifi_tx : "+items[9]+" total wifi:"+str(self.wifi_total))
                # 移动 3 4 5G 流量
                # rmnet0: 362133448 298441 0 0 0 0 0 0 10641124 91012 0 0 0 0 0 0
            if "rmnet0:" in line:
                items = line.split()
                self.mobile_rx = int(items[1])
                self.mobile_tx = int(items[9])
                self.mobile_total = self.wifi_rx + self.wifi_tx
                logger.debug("mobile_rx : " + items[1] + " mobile_tx : " + items[9] + " total mobile:" + str(self.mobile_total))
            self.rx = self.wifi_rx + self.mobile_rx
            self.tx = self.wifi_tx + self.mobile_tx
            self.total = self.wifi_total + self.mobile_total

    def __repr__(self):
        return "NetDevInfo "

class TrafficCollecor(object):
    def __init__(self, device, packages, interval=1.0,timeout=24*60 * 60, traffic_queue = None):
        self.device = device
        self.packages = packages
        self._interval = interval
        self._timeout = timeout
        self._stop_event = threading.Event()
        self.traffic_queue = traffic_queue
        self.sdk_version = self.device.adb.get_sdk_version()

        #是否首次启动，默认是
        self.traffic_init = True
        self.traffic_init_dic = {}


    def start(self,start_time):
        logger.debug("INFO: TrafficCollecor  start...")
        self.collect_traffic_thread = threading.Thread(target=self._collect_traffic_thread,args=(start_time,))
        self.collect_traffic_thread.start()

    def _cat_traffic_data(self, packagename, uid):
        out = self.device.adb.run_shell_cmd("cat /proc/net/xt_qtaguid/stats")
        out.replace('\r', '')
        return TrafficSnapshot(out, packagename, uid)

    def _cat_traffic_device_dev(self):
        out = self.device.adb.run_shell_cmd("cat /proc/net/dev")
        # traffic_file = os.path.join(RuntimeData.package_save_path, 'traffic.txt')
        # with open(traffic_file, "a+", encoding="utf-8") as writer:
        #     writer.write(TimeUtils.getCurrentTime() + " cat /proc/net/dev info:\n")
        #     writer.write(out + "\n\n")
        out.replace('\r', '')
        return NetDevInfo(out)

    def _cat_traffic_pid_dev(self,pid):
        out = self.device.adb.run_shell_cmd("cat /proc/%d/net/dev"%pid)
        # traffic_file = os.path.join(RuntimeData.package_save_path, 'traffic.txt')
        # with open(traffic_file, "a+", encoding="utf-8") as writer:
        #     writer.write(TimeUtils.getCurrentTime() + " cat /proc/"+str(pid)+"/net/dev info:\n")
        #     writer.write(out + "\n\n")
        out.replace('\r', '')
        return NetDevInfo(out)

    def _collect_traffic_thread(self,start_time):
        # < android10 用/proc/net/xt_qtaguid/stats 获取uid 流量，Android10 找不到该文件
        if self.sdk_version < 29:
            self.get_traffic_with_stats()
        else:
            # android 10 用 /proc/net/dev  /proc/pid/net/dev 获取整机 pid wifi流量
            self.get_traffic_with_dev()

    def get_traffic_with_stats(self):
        end_time = time.time() + self._timeout
        uid = TrafficUtils.getUID(self.device, self.packages[0])
        traffic_list_title = (
        "datetime", "packagename", "uid", "uid_total(KB)", "uid_total_packets", "rx(KB)", "rx_packets", "tx(KB)",
        "tx_packets", "fg(KB)", "bg(KB)", "lo(KB)")
        traffic_file = os.path.join(RuntimeData.package_save_path, 'traffics_uid.csv')
        try:
            with open(traffic_file, 'a+') as df:
                csv.writer(df, lineterminator='\n').writerow(traffic_list_title)
                if self.traffic_queue:
                    traffic_file_dic = {'traffic_file': traffic_file}
                    self.traffic_queue.put(traffic_file_dic)
        except RuntimeError as e:
            logger.error(e)

        while not self._stop_event.is_set() and time.time() < end_time:
            try:
                before = time.time()
                logger.debug("----------------- into _collect_traffic_thread loop thread is : " + str(
                    threading.current_thread().name) + ", current uid is : " + str(uid))
                traffic_snapshot = self._cat_traffic_data(self.packages[0], uid)

                if traffic_snapshot.source == '' or traffic_snapshot.source == None:
                    continue  # 获取不到值的时候，直接不执行下面的代码了，缺一个
                    # retry_count = retry_count - 1
                    # if retry_count <= 0:
                    #     logger.debug("traffic, can't get traffic info, try six times, break...")
                    #     break

                if self.traffic_init:
                    self.traffic_init_dic = self.get_traffic_init_data(traffic_snapshot)
                    self.traffic_init = False
                traffic_snapshot = self.get_data_from_threadstart(traffic_snapshot)

                collection_time = time.time()
                logger.debug(" collection time in traffic is : " + str(collection_time))
                traffic_list_temp = [collection_time, traffic_snapshot.packagename, traffic_snapshot.uid,
                                     TrafficUtils.byte2kb(traffic_snapshot.total_uid_bytes),
                                     traffic_snapshot.total_uid_packets,
                                     TrafficUtils.byte2kb(traffic_snapshot.rx_uid_bytes),
                                     traffic_snapshot.rx_uid_packets,
                                     TrafficUtils.byte2kb(traffic_snapshot.tx_uid_bytes),
                                     traffic_snapshot.tx_uid_packets, TrafficUtils.byte2kb(traffic_snapshot.fg_bytes),
                                     TrafficUtils.byte2kb(traffic_snapshot.bg_bytes),
                                     TrafficUtils.byte2kb(traffic_snapshot.lo_uid_bytes)]
                logger.debug(traffic_list_temp)
                if self.traffic_queue:
                    self.traffic_queue.put(traffic_list_temp)

                if not self.traffic_queue:  # 为了本地单个文件单独运行
                    traffic_list_temp[0] = TimeUtils.formatTimeStamp(traffic_list_temp[0])
                    try:
                        with open(traffic_file, 'a+', encoding="utf-8") as f:
                            writer = csv.writer(f, lineterminator='\n')
                            writer.writerow(traffic_list_temp)
                    except RuntimeError as e:
                        logger.error(e)

                after = time.time()
                time_consume = after - before
                logger.debug(" -----------traffic timeconsumed: " + str(time_consume))
                # 校准时间，由于执行命令行需要耗时，需要将这个损耗加上去
                delta_inter = self._interval - time_consume
                if delta_inter > 0:
                    time.sleep(delta_inter)
            except RuntimeError as e:
                logger.error(" trafficstats RuntimeError ")
                logger.error(e)
            except Exception as e:
                logger.error("an exception hanpend in traffic thread , reason unkown! e: ")
                s = traceback.format_exc()
                logger.debug(s)
                if self.traffic_queue:
                    self.traffic_queue.task_done()

    def get_traffic_with_dev(self):
        end_time = time.time() + self._timeout
        traffic_title = ["datetime", "device_total(KB)", "device_receive(KB)", "device_transport(KB)"]
        traffic_file = os.path.join(RuntimeData.package_save_path, 'traffic.csv')
        for i in range(0, len(self.packages)):
            traffic_title.extend(["package", "pid", "pid_rx(KB)","pid_tx(KB)","pid_total(KB)"])
        if len(self.packages) > 1:
            traffic_title.append("total_proc_traffic(kB)")
        try:
            with open(traffic_file, 'a+') as df:
                csv.writer(df, lineterminator='\n').writerow(traffic_title)
        except RuntimeError as e:
            logger.error(e)
        self.device_init_net = None
        self.pck_init_net_list = []
        while not self._stop_event.is_set() and time.time() < end_time:
            try:
                before = time.time()
                logger.debug("--------- into _collect_traffic_thread loop thread is : " + str(threading.current_thread().name))
                device_cur_net = self._cat_traffic_device_dev()

                if device_cur_net.source == '' or device_cur_net.source == None:
                    continue

                if self.traffic_init:
                    self.device_init_net = device_cur_net
                    # self.traffic_init = False
                device_grow = self.get_net_from_begin(self.device_init_net,device_cur_net)
                collection_time = time.time()
                logger.debug(" collection time in traffic is : " + str(collection_time))
                net_row = [collection_time, TrafficUtils.byte2kb(device_grow.total),
                           TrafficUtils.byte2kb(device_grow.rx),
                           TrafficUtils.byte2kb(device_grow.tx)]
                self.total_pck_net = 0
                for i in range(0, len(self.packages)):
                    pid = self.device.adb.get_pid_from_pck(self.packages[i])
                    pck_net_info = self._cat_traffic_pid_dev(pid)
                    if not pck_net_info.source:
                        logger.error("package net dev failed %s:"%self.packages[i])
                        continue
                    if self.traffic_init:
                        self.pck_init_net_list.append(pck_net_info)
                        if i == len(self.packages)-1:
                            self.traffic_init = False
                    pck_grow = self.get_net_from_begin(self.pck_init_net_list[i],pck_net_info)
                    self.total_pck_net = self.total_pck_net + pck_grow.wifi_total
                    net_row.extend([self.packages[i],pid,TrafficUtils.byte2kb(pck_grow.rx),
                                    TrafficUtils.byte2kb(pck_grow.tx),TrafficUtils.byte2kb(pck_grow.total)])

                if len(self.packages)>1:
                    net_row.append(TrafficUtils.byte2kb(self.total_pck_net))

                if self.traffic_queue:
                    self.traffic_queue.put(net_row)
                if not self.traffic_queue:  # 为了本地单个文件单独运行
                    net_row[0] = TimeUtils.formatTimeStamp(net_row[0])
                    try:
                        with open(traffic_file, 'a+', encoding="utf-8") as f:
                            writer = csv.writer(f, lineterminator='\n')
                            writer.writerow(net_row)
                    except RuntimeError as e:
                        logger.error(e)
                logger.debug(net_row)
                after = time.time()
                time_consume = after - before
                logger.debug(" -----------traffic timeconsumed: " + str(time_consume))
                # 校准时间，由于执行命令行需要耗时，需要将这个损耗加上去
                delta_inter = self._interval - time_consume
                if delta_inter > 0:
                    time.sleep(delta_inter)
            except RuntimeError as e:
                logger.error(" trafficstats RuntimeError ")
                logger.error(e)
            except Exception as e:
                logger.error("an exception hanpend in traffic thread , reason unkown! e: ")
                s = traceback.format_exc()
                logger.debug(s)
                if self.traffic_queue:
                    self.traffic_queue.task_done()

    def get_traffic_init_data(self,traffic_snapshot):
        #将首次启动的流量的相关的数据存放在字典中，以便将流量的起始点定位这个线
        # 程启动的时候（我们现在从手机中抓出来的数据是从手机开机作为起始点来算的）
        traffic_data_dic = {}
        # if self.traffic_init:#
        traffic_data_dic['package'] = traffic_snapshot.packagename
        traffic_data_dic['total'] = traffic_snapshot.total_uid_bytes
        traffic_data_dic['total_packets'] = traffic_snapshot.total_uid_packets
        traffic_data_dic['rx'] = traffic_snapshot.rx_uid_bytes
        traffic_data_dic['rx_packets'] = traffic_snapshot.rx_uid_packets
        traffic_data_dic['tx'] = traffic_snapshot.tx_uid_bytes
        traffic_data_dic['tx_packets'] = traffic_snapshot.tx_uid_packets
        traffic_data_dic['fg'] = traffic_snapshot.fg_bytes
        traffic_data_dic['bg'] = traffic_snapshot.bg_bytes
        traffic_data_dic['lo'] = traffic_snapshot.lo_uid_bytes
        logger.debug(traffic_data_dic)
        return traffic_data_dic

    def get_data_from_threadstart(self, traffic_snapshot):
        # 获取从当前线程开始的流量值
        traffic_snapshot.total_uid_bytes = traffic_snapshot.total_uid_bytes - self.traffic_init_dic['total'] if (traffic_snapshot.total_uid_bytes - self.traffic_init_dic['total']) >= 0 else 0
        traffic_snapshot.total_uid_packets = traffic_snapshot.total_uid_packets - self.traffic_init_dic['total_packets'] if (traffic_snapshot.total_uid_packets - self.traffic_init_dic['total_packets'] ) >= 0 else 0
        traffic_snapshot.rx_uid_bytes = traffic_snapshot.rx_uid_bytes - self.traffic_init_dic['rx'] if (traffic_snapshot.rx_uid_bytes - self.traffic_init_dic['rx']) >= 0 else 0
        traffic_snapshot.rx_uid_packets = traffic_snapshot.rx_uid_packets - self.traffic_init_dic['rx_packets'] if (traffic_snapshot.rx_uid_packets - self.traffic_init_dic['rx_packets']) >= 0 else 0
        traffic_snapshot.tx_uid_bytes = traffic_snapshot.tx_uid_bytes - self.traffic_init_dic['tx'] if (traffic_snapshot.tx_uid_bytes - self.traffic_init_dic['tx']) >= 0 else 0
        traffic_snapshot.tx_uid_packets = traffic_snapshot.tx_uid_packets - self.traffic_init_dic['tx_packets'] if (traffic_snapshot.tx_uid_packets - self.traffic_init_dic['tx_packets']) >= 0 else 0
        traffic_snapshot.fg_bytes = traffic_snapshot.fg_bytes - self.traffic_init_dic['fg'] if (traffic_snapshot.fg_bytes - self.traffic_init_dic['fg']) >=0 else 0
        traffic_snapshot.bg_bytes = traffic_snapshot.bg_bytes - self.traffic_init_dic['bg'] if (traffic_snapshot.bg_bytes - self.traffic_init_dic['bg']) >=0 else 0
        traffic_snapshot.lo_uid_bytes = traffic_snapshot.lo_uid_bytes - self.traffic_init_dic['lo'] if (traffic_snapshot.lo_uid_bytes - self.traffic_init_dic['lo']) >= 0 else 0
        logger.debug(traffic_snapshot)
        return traffic_snapshot

    def get_net_from_begin(self,begin_net_info,current_net_info):
        # 获取从当前开始的流量增值
        net_info = NetDevInfo("")
        net_info.total = current_net_info.total - begin_net_info.total
        net_info.rx = current_net_info.rx - begin_net_info.rx
        net_info.tx = current_net_info.tx - begin_net_info.tx
        return net_info

    def stop(self):
        logger.debug("INFO: TrafficCollecor  stop...")
        if (self.collect_traffic_thread.isAlive()):
            self._stop_event.set()
            self.collect_traffic_thread.join(timeout=1)
            self.collect_traffic_thread = None
            if self.traffic_queue:
                self.traffic_queue.task_done()

class TrafficMonitor(object):
    def __init__(self, device_id, packages, interval = 1.0, timeout=10 * 60, traffic_queue = None):
        self.device = AndroidDevice(device_id)
        self.stop_event = threading.Event()
        self.packages = packages
        self.traffic_colloctor = TrafficCollecor(self.device, self.packages, interval, timeout, traffic_queue)

    def start(self,start_time):
        if not RuntimeData.package_save_path:
            RuntimeData.package_save_path = os.path.join(os.path.abspath(os.path.join(os.getcwd(), "../..")),'results', self.packages[0], start_time)
            if not os.path.exists(RuntimeData.package_save_path):
                os.makedirs(RuntimeData.package_save_path)
        self.start_time = start_time
        self.traffic_colloctor.start(start_time)
        logger.debug("INFO: TrafficMonitor has started...")

    def stop(self):
        self.traffic_colloctor.stop()
        logger.debug("INFO: TrafficMonitor has stopped...")


    def _get_traffic_collector(self):
        return self.traffic_colloctor

    def save(self):
        '''
        默认保存，保存在当前目录的results/TrafficInfos文件夹下
        :return:
        '''
        pass

if __name__ == "__main__":
    monitor = TrafficMonitor("UYT5T18615007121", ["com.taobao.taobao"], 2)
    monitor.start(TimeUtils.getCurrentTime())
    time.sleep(60)
    monitor.stop()


