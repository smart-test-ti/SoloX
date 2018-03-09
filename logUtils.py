# -*- coding: utf-8 -*-

import os

import log4py

# import config

LOG_PATH = os.path.join(os.getcwd() + "/performance/log/")
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)


def log_init(device):
    loghd = log4py.Logger().get_instance(device)
    loghd.set_target("%sperformanceTest_%s.log" % (LOG_PATH, device))
    loghd.set_rotation(log4py.ROTATE_DAILY)
    loghd.set_loglevel(log4py.LOGLEVEL_NORMAL)
    return loghd
