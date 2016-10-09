import logging


logger = logging.getLogger('monitor')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('../monitor.log')
ch = logging.StreamHandler()


formatter ='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
datefmt = '%a, %d %b %Y %H:%M:%S'

fh.setFormatter(logging.Formatter(fmt=formatter, datefmt=datefmt))
ch.setFormatter(logging.Formatter(fmt=formatter, datefmt=datefmt))

logger.addHandler(fh)
logger.addHandler(ch)
