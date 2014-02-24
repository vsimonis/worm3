import logging

logging.basicConfig(level = 5)
CAMERA = 5
logging.addLevelName(5, 'camera')
logger = logging.getLogger('inst')


for i in range(5):
    logger.log(CAMERA, 'gerrr')
