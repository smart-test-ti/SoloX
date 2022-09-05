#!/usr/bin/env python
# coding:utf-8
"""
Name : FpsInfo.py
Author  :
Contect :
Time    : 2020/7/21 14:26
Desc:
"""


class FpsInfo(object):
    def __init__(self, time, total_frames, fps, pkg_name, window_name, jankys_ary, jankys_more_than_16,
                 jankys_more_than_166):
        # 采样数据时的时间戳
        self.time = time
        # 2s内取到总帧数
        self.total_frames = total_frames
        # fps
        self.fps = fps
        # 测试应用包名
        self.pkg_name = pkg_name
        # 窗口名
        self.window_name = window_name
        # 掉帧具体时间集合
        self.jankys_ary = jankys_ary
        # 掉帧数目,大于16.67ms
        self.jankys_more_than_16 = jankys_more_than_16
        # 卡顿数目,大于166.7ms
        self.jankys_more_than_166 = jankys_more_than_166

