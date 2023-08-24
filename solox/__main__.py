from __future__ import absolute_import
from logzero import logger
import platform
import fire as fire

def checkPyVer():
    versions = platform.python_version().split('.')
    if int(versions[0]) < 3 or int(versions[1]) < 10:
        logger.error('python version must be 3.10+ ,your python version is {}'.format(platform.python_version()))
        logger.info('https://github.com/smart-test-ti/SoloX/blob/master/README.md#requirements')
        return False
    return True    

if __name__ == '__main__':
    check = checkPyVer()
    if check:
        from solox.web import main
        fire.Fire(main)    
