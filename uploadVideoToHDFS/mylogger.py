# coding=utf-8
'''
Created on 2016.10.7

@author: Gyy
'''
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('monitor')
logger.setLevel(logging.DEBUG)

fh = RotatingFileHandler('../monitor.log',maxBytes="10*1024*1024", backupCount=3)
ch = logging.StreamHandler()


formatter ='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
datefmt = '%a, %d %b %Y %H:%M:%S'

fh.setFormatter(logging.Formatter(fmt=formatter, datefmt=datefmt))
ch.setFormatter(logging.Formatter(fmt=formatter, datefmt=datefmt))

logger.addHandler(fh)
logger.addHandler(ch)
