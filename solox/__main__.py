from __future__ import absolute_import
import multiprocessing
from .web import *



def main():
    try:
        pool = multiprocessing.Pool(processes=2)
        pool.apply_async(start_web)
        pool.apply_async(open_url)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print('stop solox success')


if __name__ == '__main__':
    main()

