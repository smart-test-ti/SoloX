from __future__ import absolute_import
import fire as fire
from solox import __version__
from solox.web import main

if __name__ == '__main__':
    
    fire.Fire(main)