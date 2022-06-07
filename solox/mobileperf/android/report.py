# encoding: utf-8
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
import os
from datetime import datetime

from mobileperf.android.excel import Excel
from mobileperf.common.log import logger
from mobileperf.common.utils import TimeUtils

class Report(object):
    def __init__(self, csv_dir, packages=[]):
        os.chdir(csv_dir)
        # 需要画曲线的csv文件名
        self.summary_csf_file={"cpuinfo.csv":{"table_name":"pid_cpu",
                                          "x_axis":"datatime",
                                          "y_axis":"%",
                                          "values":["pid_cpu%","total_pid_cpu%"]},
                               "meminfo.csv":{"table_name":"pid_pss",
                                          "x_axis":"datatime",
                                          "y_axis":"mem(MB)",
                                          "values":["pid_pss(MB)","total_pss(MB)"]},
                               "pid_change.csv": {"table_name": "pid",
                                           "x_axis": "datatime",
                                           "y_axis": "pid_num",
                                           "values": ["pid"]},
                               }
        self.packages = packages
        if len(self.packages)>0:
            for package in self.packages:
                pss_detail_dic ={"table_name":"pss_detail",
                                          "x_axis":"datatime",
                                          "y_axis":"mem(MB)",
                                          "values":["pss","java_heap","native_heap","system"]
                }
                #        文件名太长会导致写excel失败
                self.summary_csf_file["pss_%s.csv"%package.split(".")[-1].replace(":","_")]= pss_detail_dic
        logger.debug(self.packages)
        logger.debug(self.summary_csf_file)
        logger.info('create report for %s' % csv_dir)
        file_names = self.filter_file_names(csv_dir)
        logger.debug('%s' % file_names)
        if file_names:
            book_name = 'summary_%s.xlsx' % TimeUtils.getCurrentTimeUnderline()
            excel = Excel(book_name)
            for file_name in file_names:
                logger.debug('get csv %s to excel' % file_name)
                values = self.summary_csf_file[file_name]
                excel.csv_to_xlsx(file_name,values["table_name"],values["x_axis"],values["y_axis"],values["values"])
            logger.info('wait to save %s' % book_name)
            excel.save()
    #
    def filter_file_names(self, device):
        csv_files = []
        logger.debug(device)
        for f in os.listdir(device):
            if os.path.isfile(os.path.join(device, f)) and os.path.basename(f) in self.summary_csf_file.keys():
               logger.debug(os.path.join(device, f))
               csv_files.append(f)
        return csv_files
        #return [f for f in os.listdir(device) if os.path.isfile(os.path.join(device, f)) and os.path.basename(f) in self.summary_csf_file.keys()]

if __name__ == '__main__':
# 根据csv生成excel汇总文件
    from mobileperf.android.globaldata import RuntimeData
    RuntimeData.packages = ["com.alibaba.ailabs.genie.smartapp","com.alibaba.ailabs.genie.smartapp:core","com.alibaba.ailabs.genie.smartapp:business"]
    RuntimeData.package_save_path = "/Users/look/Downloads/mobileperf-turandot-shicun-2-13/results/com.alibaba.ailabs.genie.smartapp/2020_02_13_22_58_14"
    report = Report(RuntimeData.package_save_path,RuntimeData.packages)
    report.filter_file_names(RuntimeData.package_save_path)
