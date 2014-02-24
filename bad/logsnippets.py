  ### Define custom loggers :) 
def main():

    logging.CAMERA = 5
    logging.addLevelName(logging.CAMERA, "CAMERA")

    logging.POSITION = 6
    logging.addLevelName(logging.POSITION, "POSITION")

    logging.MOVER = 4
    logging.addLevelName(logging.MOVER, "MOVER")


#   def camera( self, message, *args, **kws):
#     self.log(CAMERA, message, *args, **kws)
#
#   def position( self, message, *args, **kws):
#     self.log(POSITION, message, *args, **kws)
#
#   def mover( self, message, *args, **kws):
#     self.log(MOVER, message, *args, **kws)
#
    logging.camera = lambda msg, *args: log._log(logging.CAMERA, msg, args)
    logging.position = lambda msg, *args: log._log(logging.POSITION, msg, args)
    logging.mover = lambda msg, *args: log._log(logging.MOVER, msg, args)

    logging.Logger.camera = logging.camera
    logging.Logger.position = logging.position
    logging.Logger.mover = logging.mover



