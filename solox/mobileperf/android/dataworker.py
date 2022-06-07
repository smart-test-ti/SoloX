#encoding:utf-8
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import csv
import os
import threading
import time
import sys
import copy
import json

import queue
import traceback

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))
from mobileperf.common.utils import TimeUtils,FileUtils
from mobileperf.common.log import logger
from mobileperf.android.upload import perf_queue
from mobileperf.android.globaldata import RuntimeData

class DataWorker(object):
    def __init__(self, queuedic):
        self.queuedic = queuedic
        self.fps_queue = self.get_fps_queue()
        self.cpu_queue = self.get_cpu_queue()
        self.mem_queue = self.get_mem_queue()
        self.power_queue = self.get_power_queue()
        self.traffic_queue = self.get_traffic_queue()
        self.activity_queue = self.get_activity_queue()
        self.fd_queue = self.get_fd_queue()
        self.thread_queue = self.get_thread_queue()
        self.fps_filename = ''
        self.power_filename = ''
        self.traffic_filename = ''
        self.cpu_filename = ''
        self.mem_filename = ''
        self.activity_file = ''
        self.fd_file = ''
        self.thread_file = ''
        self._stop_event = threading.Event()
        self.timestamp = time.time()
        self.interval = 2
        self.first_time = True
        self.perf_data = {"task_id":"","activity": [],'launch_time':[],'cpu':[],"mem":[],
                             'traffic':[], "fluency":[],'power':[],"fd":[],"thread":[]}

    def start(self, interval, start_time):
        self.interval = interval
        self.starttime = start_time
        self.dataworker_thread = threading.Thread(target=self._handle_data_thread)
        self.dataworker_thread.start()
        logger.debug("DataWorker started...")

    def stop(self):
        if self.dataworker_thread.isAlive():
            self._stop_event.set()
            self.dataworker_thread.join(timeout=1)
            self.dataworker_thread = None
        logger.debug("DataWorker stopped ")


    def get_cpu_queue(self):
        return self._get_queue('cpu_queue')

    def get_mem_queue(self):
        return self._get_queue('mem_queue')

    def get_power_queue(self):
        return self._get_queue('power_queue')

    def get_traffic_queue(self):
        return self._get_queue('traffic_queue')

    def get_fps_queue(self):
        return  self._get_queue('fps_queue')

    def get_fd_queue(self):
        return  self._get_queue('fd_queue')

    def get_thread_queue(self):
        return  self._get_queue('thread_queue')

    def get_activity_queue(self):
        return self._get_queue('activity_queue')

    def _get_queue(self, key):
        if self.queuedic:
            return self.queuedic[key]
        else:
            raise RuntimeError('no %s queue exist,please creat'%key)

    def _handle_data_thread(self):
        '''
        该方法在独立线程中运行，是一个消费者，负责处理所有的生产者搜集的数据
        :return: 
        '''
        time.sleep(1)
        while not self._stop_event.is_set():
            try:
                # 消息队列会一直阻塞直到 取到数据为止，如果生产者的线程发生了异常，则需要生产者线程会往对应的queue发出一个task_done以结束队列
                # power 数据处理
                self.perf_data = {"task_id":"","activity":[],'launch_time':[],'cpu':[],"mem":[],
                    'traffic':[], "fluency":[],'power':[],"fd":[],"thread":[]}
                try:
                    power_data = self.power_queue.get()
                    if isinstance(power_data, list):
                        self.timestamp = power_data[0]
                    logger.debug("dataworker logger timestamp: " + str(self.timestamp))
                    logger.info("now collecting data")
                    self._get_power_save(power_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker power queue Empty")

                # traffic数据的处理
                try:
                    traffic_data = self.traffic_queue.get(timeout=2)
#                     logger.debug(traffic_data)
                    self._get_traffic_save(traffic_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker traffic queue Empty")

                #fps数据的处理
                try:
                    fps_data = self.fps_queue.get(timeout=2)
                    self._get_fps_save(fps_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker fps queue Empty")

                #cpu数据处理
                try:
                    cpu_data = self.cpu_queue.get(timeout = 2)
#                     logger.debug(cpu_data)
                    self._get_cpu_save(cpu_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker cpu queue Empty")

                #mem 数据处理
                try:
                    mem_data = self.mem_queue.get(timeout=2)
#                     logger.debug(mem_data)
                    self._get_mem_save(mem_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker mem queue Empty")

                try:
                    fd_data = self.fd_queue.get(timeout=2)
                    # logger.debug("fd_data")
                    # logger.debug(fd_data)
                    self._get_fd_save(fd_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker fd_data queue Empty")

                try:
                    thread_data = self.thread_queue.get(timeout=2)
                    # logger.debug("thread_data")
                    # logger.debug(thread_data)
                    self._get_thread_save(thread_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker thread queue Empty")

                try:
                    activity_data = self.activity_queue.get(timeout = 2)
                    self._get_activity_save(activity_data, self.timestamp)
                except queue.Empty:
                    logger.debug("dataworker activity queue Empty")

            except Exception as e:
                logger.error(e)
                s = traceback.format_exc()
                logger.debug(s)  # 将堆栈信息打印到log中
            #logger.info("dataworker interval: " + str(self.interval))
            #               封装后最后统一放入 perf_queue中
            logger.debug("perf_str put in queue:"+json.dumps(self.perf_data))
            # 没有启动上报线程，避免无限增长
            # perf_queue.put(self.perf_data)
            time.sleep(self.interval)
                
    def _get_fps_save(self, fps_data, timestamp):
        if isinstance(fps_data, dict):
            self.fps_filename = fps_data['fps_file']
            logger.debug("fps_filename: " + str(self.fps_filename))
        else:
            try:
                '''0            1           2    3
                fps_data: ("datetime", "activity","fps", "jank")
                对应的值是:[formatter(collection_time), activity,fps,jank],
              '''
                fps_data[0] = timestamp
                dic = {"time": fps_data[0] * 1000, "activity":fps_data[1],"fps": fps_data[2], "jank": fps_data[3]}
                self.perf_data['fluency'].append(dic)
                with open(self.fps_filename, 'a+') as writer:
                    logger.debug("dataworker write fps data in  dataworker。fps timestamp: " + str(fps_data[0]))
                    fps_data[0] = TimeUtils.formatTimeStamp(fps_data[0])
                    tmp_dic = copy.deepcopy(dic)
                    tmp_dic["time"] = fps_data[0]
                    logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    writer_p.writerow(fps_data)

            except Exception as e:
                s = traceback.format_exc()
                logger.error(s)  # 将堆栈信息打印到log中
                logger.error("fps save error")            
                
                
    def _get_cpu_save(self, cpu_data, timestamp):
        if isinstance(cpu_data, dict):
            self.cpu_filename = cpu_data['cpu_file']
            logger.debug("cpu_filename: " + str(self.cpu_filename))
        else:
            try:
                '''              0            1           2          3          4                5        6       7        8            9
                cpu_data: ("datetime", " cpu_rate%", "user%", "system%", "all_jiffies","packagename", "pid", "uid", "pck_jiffies", "pid_cpu%")
                对应的值是:[collection_time, cpu_info.cpu_rate, cpu_info.user_rate, cpu_info.system_rate, cpu_info.cpu_jiffs, cpu_pck_info.pckagename,
                               cpu_pck_info.pid, cpu_pck_info.uid,cpu_pck_info.p_cpu_jiffs, cpu_pck_info.p_cpu_rate],
                               
              '''
                cpu_data[0] = timestamp
                dic = {"time": cpu_data[0] * 1000, "total": cpu_data[1], "cpu_jiffies": cpu_data[4],
                     "user": cpu_data[2], "sys": cpu_data[3],
                     "pck_jiffies": cpu_data[8],
                     "pid_cpu": cpu_data[9]
                     }
                self.perf_data['cpu'].append(dic)
                with open(self.cpu_filename, 'a+') as writer:
                    logger.debug("write cpu data in  dataworker mem timestamp: " + str(cpu_data[0]))
                    cpu_data[0] = TimeUtils.formatTimeStamp(cpu_data[0])
                    tmp_dic = copy.deepcopy(dic)
                    tmp_dic["time"] = cpu_data[0]
                    logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    # logger.debug("------------------ dataworker          cpudate: " + str(cpu_data))
                    writer_p.writerow(cpu_data)

            except Exception as e:
                logger.error('cpu save error')
                s = traceback.format_exc()
                logger.error(s)

    def _get_mem_save(self, mem_data,timestamp):
        if isinstance(mem_data, dict):
            self.mem_filename = mem_data['mem_file']
            logger.debug("mem_filename: " + str(self.mem_filename))
        else:
            try:
                '''              0           1                     2              3           4        5               6
               mem_data: ("datatime", "total_ram(KB)", "free_ram(KB)", "pckagename", "pid", "pid_pss(KB)", "pid_alloc_heap(KB)")
               对应的值是：[formatTimeStamp(collection_time), cpu_info.cpu_rate, cpu_info.user_rate, cpu_info.system_rate, cpu_info.cpu_jiffs, cpu_pck_info.pckagename,
                               cpu_pck_info.pid, cpu_pck_info.uid,cpu_pck_info.p_cpu_jiffs, cpu_pck_info.p_cpu_rate]
                '''
                mem_data[0] = timestamp
                dic = {"time": mem_data[0] * 1000, "total": mem_data[1],
                     "free": mem_data[2],
                     "pss": mem_data[5],
                     "heap": mem_data[6]
                     }
                self.perf_data['mem'].append(dic)
                
                with open(self.mem_filename, 'a+') as writer:
                    logger.debug("write mem data in  dataworker。。。。。。 mem timestamp: " + str(mem_data[0]))
                    if isinstance(mem_data[0], float):
                        mem_data[0] = TimeUtils.formatTimeStamp(mem_data[0])
                        tmp_dic = copy.deepcopy(dic)
                        tmp_dic["time"] = mem_data[0]
                        logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    # logger.debug("------------------ dataworker          memdata: " + str(mem_data))
                    writer_p.writerow(mem_data)

            except Exception as e:
                logger.error('mem save error')
                s = traceback.format_exc()
                logger.debug(s)

    def _get_fd_save(self, fd_data, timestamp):
        if isinstance(fd_data, dict):
            self.fd_file = fd_data['fd_file']
            logger.debug("fd_file: " + str(self.fd_file))
        else:
            try:
                '''              0           1        2        3 
               fd_data: ("datatime", "pckagename", "pid", "fd num")
               对应的值是：[formatTimeStamp(collection_time), packagename, pid,fd_num]
                '''
                fd_data[0] = timestamp
                dic = {"time": fd_data[0] * 1000, "package": fd_data[1],
                       "pid": fd_data[2],
                       "fd": fd_data[3]
                       }
                self.perf_data['fd'].append(dic)

                with open(self.fd_file, 'a+') as writer:
                    logger.debug("write fd data in  dataworker。。。。。。 fd timestamp: " + str(fd_data[0]))
                    if isinstance(fd_data[0], float):
                        fd_data[0] = TimeUtils.formatTimeStamp(fd_data[0])
                        tmp_dic = copy.deepcopy(dic)
                        tmp_dic["time"] = fd_data[0]
                        logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    writer_p.writerow(fd_data)

            except Exception as e:
                logger.error('fd save error')
                s = traceback.format_exc()
                logger.debug(s)

    def _get_thread_save(self, thread_data, timestamp):
        if isinstance(thread_data, dict):
            self.thread_file = thread_data['thread_file']
            logger.debug("thread_file: " + str(self.thread_file))
        else:
            try:
                '''              0           1        2        3 
               thread_data: ("datatime", "pckagename", "pid", "thread num")
               对应的值是：[formatTimeStamp(collection_time), packagename, pid,thread_num]
                '''
                thread_data[0] = timestamp
                dic = {"time": thread_data[0] * 1000, "package": thread_data[1],
                       "pid": thread_data[2],
                       "thread": thread_data[3]
                       }
                self.perf_data['thread'].append(dic)

                with open(self.thread_file, 'a+') as writer:
                    logger.debug("write thread data in  dataworker。。。。。。 thread timestamp: " + str(thread_data[0]))
                    if isinstance(thread_data[0], float):
                        thread_data[0] = TimeUtils.formatTimeStamp(thread_data[0])
                        tmp_dic = copy.deepcopy(dic)
                        tmp_dic["time"] = thread_data[0]
                        logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    writer_p.writerow(thread_data)

            except Exception as e:
                logger.error('thread save error')
                s = traceback.format_exc()
                logger.debug(s)


    def _get_power_save(self, power_data, timestamp):
        if isinstance(power_data, dict):
            self.power_filename = power_data['power_file']
            logger.debug("dataworker power_filename: " + str(self.power_filename))
        else:
            try:
                '''                 0         1      2             3              4
                power_data: ("datetime","level","voltage(V)","tempreture(C)","current(mA)")
                example: [collection_time, device_power_info.level, device_power_info.voltage,
                                       device_power_info.temp, device_power_info.current]
                '''
                power_data[0] = timestamp
                dic = {"time": power_data[0] * 1000, "level": power_data[1],
                        "vol": power_data[2], "temp": power_data[3],"current": power_data[4]}
                self.perf_data['power'].append(dic)

                with open(self.power_filename, 'a+') as writer:
                    logger.debug("write power data in dataworker。。。。。。 timestamp:" + str(power_data[0]))
                    if isinstance(power_data[0], float):
                        power_data[0] = TimeUtils.formatTimeStamp(power_data[0])
                        tmp_dic = copy.deepcopy(dic)
                        tmp_dic["time"] = power_data[0]
                        logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    # logger.debug("------------------ dataworker          power data: " + str(power_data))
                    writer_p.writerow(power_data)
            except Exception as e:
                logger.error('power save error')
                s = traceback.format_exc()
                logger.debug(s)


    def _get_traffic_save(self, traffic_data, timestamp):
        if isinstance(traffic_data, dict):
            self.traffic_filename = traffic_data['traffic_file']
            logger.debug("dataworker traffic_filename: " + str(self.traffic_filename))
        else:
            try:
                '''                    0        1            2       3                   4                5          6           7        8           9         10      11
                traffic_data: ("datetime","packagename","uid","uid_total(KB)", "uid_total_packets", "rx(KB)", "rx_packets","tx(KB)","tx_packets","fg(KB)","bg(KB)","lo(KB)")
                example： [collection_time, traffic_snapshot.packagename, traffic_snapshot.uid,TrafficUtils.byte2kb(traffic_snapshot.total_uid_bytes), traffic_snapshot.total_uid_packets,
                                      TrafficUtils.byte2kb(traffic_snapshot.rx_uid_bytes),traffic_snapshot.rx_uid_packets, TrafficUtils.byte2kb(traffic_snapshot.tx_uid_bytes),
                                          traffic_snapshot.tx_uid_packets, TrafficUtils.byte2kb(traffic_snapshot.fg_bytes), TrafficUtils.byte2kb(traffic_snapshot.bg_bytes),
                                           TrafficUtils.byte2kb(traffic_snapshot.lo_uid_bytes)]
                '''
                traffic_data[0] = timestamp
                dic = {"time": traffic_data[0] * 1000,
                                             "total": traffic_data[3],
                                             "total_packets": traffic_data[4],
                                             "rx": traffic_data[5],
                                             "rx_packets": traffic_data[6],
                                             "tx": traffic_data[7],
                                             "tx_packets": traffic_data[8],
                                             "fg": traffic_data[9],
                                             "bg": traffic_data[10],
                                             "lo": traffic_data[11]}
                self.perf_data['traffic'].append(dic)

                with open(self.traffic_filename, 'a+') as writer:
                    logger.debug("write traffic data in dataworker traffic data timestamp: " + str(traffic_data[0]))
                    if isinstance(traffic_data[0], float):
                        traffic_data[0] = TimeUtils.formatTimeStamp(traffic_data[0])
                        tmp_dic = copy.deepcopy(dic)
                        tmp_dic["time"] = traffic_data[0]
                        logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    # logger.debug("------------------ dataworker          trafficdata: " + str(traffic_data))
                    writer_p.writerow(traffic_data)
            except Exception as e:
                logger.error("traffic save error")
                s = traceback.format_exc()
                logger.debug(s)

    def _get_activity_save(self, activity_data, timestamp):
        if self.first_time:
            activity_title = ("datetime", "current_activity")
            self.first_time = False
            self.activity_file = os.path.join(RuntimeData.package_save_path, 'current_activity.csv')
            try:
                with open(self.activity_file,'a+') as af:
                    csv.writer(af, lineterminator='\n').writerow(activity_title)
            except Exception as e:
                logger.error("file not found: " + str(self.activity_file))
        else:
            try:
                activity_data[0] = timestamp
                dic = {"time": activity_data[0] * 1000,"name": activity_data[1]}
                self.perf_data['activity'].append(dic)
                
                with open(self.activity_file, 'a+') as writer:
                    if isinstance(activity_data[0], float):
                        activity_data[0] = TimeUtils.formatTimeStamp(activity_data[0])
                        tmp_dic = copy.deepcopy(dic)
                        tmp_dic["time"] = activity_data[0]
                        logger.debug(tmp_dic)
                    writer_p = csv.writer(writer, lineterminator='\n')
                    writer_p.writerow(activity_data)
                    
            except Exception as e:
                logger.error("activity save error ")
                s = traceback.format_exc()
                logger.debug(s)


