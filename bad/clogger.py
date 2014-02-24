import logging


class vLog (object):
  
  def __init__ (self):
    logging.CAMERA = 5
    logging.addLevelName(logging.CAMERA, "CAMERA")

    logging.POSITION = 6
    logging.addLevelName(logging.POSITION, "POSITION")

    logging.MOVER = 4
    logging.addLevelName(logging.MOVER, "MOVER")


    def camera( self, message, *args, **kws):
      self.log(CAMERA, message, *args, **kws)

    def position( self, message, *args, **kws):
      self.log(POSITION, message, *args, **kws)

    def mover( self, message, *args, **kws):
      self.log(MOVER, message, *args, **kws)


    logging.Logger.camera = camera
    logging.Logger.position = position
    logging.Logger.mover = mover



    
