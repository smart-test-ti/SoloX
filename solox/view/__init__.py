from __future__ import absolute_import
import os
import json
import time
import datetime
import shutil
from flask import Blueprint
from flask import render_template
from flask import request
from ..public.apm import *
from ..public.common import *
from logzero import logger
from math import fsum
import traceback
import platform
import re





d = Devices()


