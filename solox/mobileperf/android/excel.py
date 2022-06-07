# encoding: utf-8
'''
@author:     Juncheng Chen

@copyright:  1999-2015 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    juncheng.cjc@outlook.com
'''
import csv,os,sys

BaseDir=os.path.dirname(__file__)
sys.path.append(os.path.join(BaseDir,'../..'))
from mobileperf.android.globaldata import RuntimeData
from mobileperf.extlib import xlsxwriter
from mobileperf.common.log import logger

class Excel(object):

    def __init__(self, excel_file):
        self.excel_file = excel_file
        self.workbook = xlsxwriter.Workbook(excel_file)
        self.color_list = ["blue", "green", "red", "yellow","purple"]

    def add_sheet(self, sheet_name, x_axis, y_axis, headings, lines):
        worksheet = self.workbook.add_worksheet(sheet_name)
        worksheet.write_row('A1', headings)
        for i, line in enumerate(lines, 2):
            worksheet.write_row('A%d' % i, line)
        columns = len(headings)
        rows = len(lines)
        if columns > 1 and rows > 1:
            chart = self.workbook.add_chart({'type': 'line'})
            for j in range(1, columns):
                chart.add_series({'name':       [sheet_name, 0, j],
                                  'categories': [sheet_name, 1, 0, rows, 0],
                                  'values':     [sheet_name, 1, j, rows, j]})
            chart.set_title ({'name': sheet_name.replace('.', ' ').title()})
            chart.set_x_axis({'name': x_axis})
            chart.set_y_axis({'name': y_axis})
            worksheet.insert_chart('B3', chart, {'x_scale': 2, 'y_scale': 2})
    
    def save(self):
        self.workbook.close()

    def csv_to_xlsx(self, csv_file, sheet_name, x_axis,y_axis, y_fields=[]):
        '''
        把csv的数据存到excel中，并画曲线
        csv_file csv 文件路径 表格名
        sheet_name 图表名
        x_axis 横轴名 和 表中做横轴字段名
        y_axis 纵轴名
        y_fields 纵轴表中数据字段名 ，可以多个
        '''
        filename = os.path.splitext(os.path.basename(csv_file))[0]
        logger.debug("filename:"+filename)
        worksheet = self.workbook.add_worksheet(filename)  # 创建一个sheet表格
        with open(csv_file, 'r') as f:
            read = csv.reader(f)
            # 行数
            l = 0
            # 表头
            headings = []
            for line in read:
                # print(line)
                r = 0
                for i in line:
                    # print(i)
                    if self.is_number(i):
                        worksheet.write(l, r, float(i))  # 一个一个将单元格数据写入
                    else:
                        worksheet.write(l, r,i)
                    r = r + 1
                if l==0:
                    headings=line
                l = l + 1
                # 列数
            columns = len(headings)
        # 求出展示数据索引
        indexs=[]
        # 求出系列名所在索引
        series_index=[]
        for columu_name in y_fields:
            indexs.extend([i for i, v in enumerate(headings) if v == columu_name])
        series_index.extend([i for i, v in enumerate(headings) if v == "package"])
        logger.debug("series_index")
        logger.debug(series_index)
        if columns > 1 and l>2:
            chart = self.workbook.add_chart({'type': 'line'})
            # 画图
            i =0
            for index in indexs:
                if "pid_cpu%" == headings[index] or "pid_pss(MB)" == headings[index]:
                    chart.add_series({
                        # 这个是series 系列名 包名
                        'name': [filename,1,series_index[i]],
                        'categories': [filename, 1, 0, l - 1, 0],
                        'values': [filename, 1, index, l - 1, index],
                        'line':{'color': self.color_list[index%len(self.color_list)]}
                    })
                    i = i+1
                else:
                    chart.add_series({
                        'name': [filename, 0, index],
                        'categories': [filename, 1, 0, l - 1, 0],
                        'values': [filename, 1, index, l - 1, index],
                        'line': {'color': self.color_list[index % len(self.color_list)]}
                    })
            # 图表名
            chart.set_title ({'name':sheet_name})
            chart.set_x_axis({'name': x_axis})
            chart.set_y_axis({'name': y_axis})
            worksheet.insert_chart('L3', chart, {'x_scale': 2, 'y_scale': 2})


    def is_number(self,s):
        try:
            float(s)
            return True
        except ValueError:
            pass

        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except (TypeError, ValueError):
            pass

        return False

if __name__ == '__main__':
    book_name = 'summary.xlsx'
    excel = Excel(book_name)
    # excel.csv_to_xlsx("mem_infos_10-42-38.csv","meminfo","datetime","mem(MB)",["pid_pss(MB)","pid_alloc_heap(MB)"])
    excel.csv_to_xlsx("/Users/look/Desktop/project/mobileperf-mac/results/com.alibaba.ailabs.genie.launcher/2019_03_05_23_55_28/cpuinfo.csv",
                      "pid_cpu","datetime","%",["pid_cpu%","total_pid_cpu%"])
    excel.save()
