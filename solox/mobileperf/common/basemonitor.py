# -*- coding: utf-8 -*-
'''
@author:     look

@copyright:  1999-2020 Alibaba.com. All rights reserved.

@license:    Apache Software License 2.0

@contact:    390125133@qq.com
'''
''' Monitor 基础能力
'''

import logging

logger = logging.getLogger(__name__)


class Monitor(object):
    '''性能测试数据采集能力基类
    '''

    def __init__(self, **kwargs):
        '''构造器

        :param dict kwargs: 配置项
        '''
        self.config = kwargs  # 配置项
        self.matched_data = {}  # 采集到匹配的性能数据

    def start(self):
        '''子类中实现该接口，开始采集性能数据'''
        logger.warn("请在%s类中实现start方法" % type(self))

    def clear(self):
        '''清空monitor保存的数据'''
        self.matched_data = {}

    def stop(self):
        '''子类中实现该接口，结束采集性能数据，如果后期需要解析性能数据，需要保存数据文件'''
        logger.warn("请在%s类中实现stop方法" % type(self))


    def save(self):
        '''保存数据
        '''
        logger.warn("请在%s类中实现save方法" % type(self))

if __name__ == '__main__':
    pass