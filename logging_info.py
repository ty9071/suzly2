import logging
import traceback
import os

def set_logger(logdir, basename, level=logging.DEBUG):
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
#    basename = os.path.basename(__file__)
    logname = os.path.join(logdir, 'log' + basename + '.log')
    logger = logging.getLogger(__name__)
    logger.setLevel(level = level)
    handler = logging.FileHandler(logname)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('Start')
    return logger

if __name__ == '__main__':
    logdir = '../logs/logfiles/'
    basename = os.path.basename(__file__)
    logger = set_logger(logdir, basename)
    logger.info('1234')
