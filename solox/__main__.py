from __future__ import absolute_import
import multiprocessing
from .web import *
from logzero import logger


def main():
    try:
        pool = multiprocessing.Pool(processes=2)
        pool.apply_async(open_url)
        pool.apply_async(main)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        logger.info('stop solox success')

if __name__ == '__main__':
    main()

