"""
Class containing methods to open, close and test serial connection
to EiBotBoard as well as methods to send commands to the motors

"""
import logging
import serial
import time
import eggbot_scanlinux
import sys

logger = logging.getLogger('eggbot')
#logger.setLevel(logging.DEBUG)
UMSTEP = 200

class easyEBB:
    def __init__( self, resolution = (1280,960), sizeMM = (7.9,5.8), stepMode = 5 ):
        """
        Initializes an easyEBB object
        """
        self.actualSerialPort = ''
        self.openSerial()

        ### Get size of window in mm and convert to um
        self.colUM = sizeMM[0] * 1000. #length of cols (x) in um
        self.rowUM = sizeMM[1] * 1000. #length of rows (y) in um
        
        logger.debug('Size in um:\tcol %0.3f\trow %0.3f' %
                     (self.colUM, self.rowUM) )

        ### Get size of window in pixels
        self.colNumPix = resolution[0] #length of rows in pixels
        self.rowNumPix = resolution[1] #length of cols in pixels

        logger.debug('Size in pix:\tcol %d\trow  %d' %
                     (self.colNumPix, self.rowNumPix) )

        self.pixUmStepConversions(stepMode)
        #self.enableMotors()
        
    def pixUmStepConversions( self, stepMode ):
        """ 
        Uses resolution and size in mm to convert pixel measurements 
        to steps (unit of servos)
        """
        ### Find center of window
        self.rowMid = int(self.rowNumPix // 2) 
        self.colMid = int(self.colNumPix // 2) 
        
        ### Get pixels per um ie (1 um = ? pixels )
        self.colPixSpacing = self.colNumPix / self.colUM 
        self.rowPixSpacing = self.rowNumPix / self.rowUM

        logger.debug('1 um = ? pixels\tcol %0.3f\trow %0.3f' %
                     (self.colPixSpacing, self.rowPixSpacing))
        
        ### Step mode settings
        self.stepOpts = {1: 1./16, 
                         2: 1./8, 
                         3: 1./4, 
                         4: 1./2, 
                         5: 1}
        self.stepMode = stepMode #from keys of stepOpts
        
        ### Get um per step (1 step = ? um)
        self.stepUM = ( UMSTEP * self.stepOpts[self.stepMode] )
        
        ### Get pixels per step ie (1 step = ? pixels)
        self.colPixStep = self.stepUM * self.colPixSpacing
        self.rowPixStep = self.stepUM * self.rowPixSpacing
        
        logger.info('1 step is ? pixels:\tcol: %0.3f\trow: %0.3f' % 
                    (self.colPixStep, self.rowPixStep))
        logger.info('Current stepMode value: %0.4f, EBB stepMode key: %d' % 
                    (self.stepOpts[self.stepMode], self.stepMode ))
        logger.info('1 step = ? um:  %0.4f' % self.stepUM )



    def wormPixToStep( self, colWormPix, rowWormPix ):
        """
        For checking validity of step instructions without
        sending move command. 
        Equivalent to center worm 
        """
        xInstPix = self.colMid - colWormPix
        yInstPix = self.rowMid - rowWormPix

        rowSteps = int(yInstPix / self.colPixStep)
        colSteps = int(xInstPix / self.rowPixStep)
        return colSteps, -rowSteps
        
   
    def centerWorm( self, duration, colWormPix, rowWormPix ):
         """
         Moves camera from current location to recenter the worm based
         on the worm's column (x) and row (y) position in the image
         given in pixels
         """
         
         logger.warning('Centering Worm')
         xInstPix = self.colMid - colWormPix
         yInstPix = self.rowMid - rowWormPix
         
         rowSteps = int(yInstPix / self.colPixStep)
         colSteps = int(xInstPix / self.rowPixStep)
         self.move( duration, colSteps, -rowSteps) #adjusted for orientation

        
    def move(self, duration, xstep, ystep):
        """
        Sends SM (move!) command to motor control board
         
        arguments
        duration -- time to complete movement (in ms)
        xstep -- step instructions x (col)
        ystep -- step instructions y (row)
        """ 
              
        #self.enableMotors()
        self.doCommand('SM,%d,%d,%d\r' %(duration, xstep, ystep))
        #self.disableMotors()
        logger.info('Command sent: move x:%d y:%d in steps' % (xstep, ystep))
        

    def openSerial( self ):
        """
        Opens a serial connection to the EiBotBoard
        """
        logging.info('Opening Serial Connection')
        self.serialPort = self.getSerialPort()
        if self.serialPort == None:
            logging.exception( "Servos: Unable to find serial port")
            sys.exit(0)
        
    def closeSerial( self ):
        """
        Closes the serial connection to the EiBotBoard
        """
        logging.info('Closing Serial Connection')
        try: 
            if self.serialPort:
                self.serialPort.flush()
                self.serialPort.close()
        finally:
            self.serialPort = None
            return

    def getSerialPort( self ):
        """
        Returns details of the serial connection
        """
        logging.debug('Get Serial Port Start')
        #try to connect to EBB devices
        for strComPort in eggbot_scanlinux.findEiBotBoards():
            logger.debug('trying to connect to EBB device: %s' % str(strComPort) )
            serialPort = self.testSerialPort( strComPort )
            if serialPort:
                self.actualSerialPort = strComPort
                return serialPort
        
        #if that fails, try any likely ports
        logger.debug('No EBB from scan_linux')
        for strComPort in eggbot_scanlinux.findPorts():
            serialPort = self.testSerialPort( strComPort )
            if serialPort:
                self.actualSerialPort = strComPort
                return serialPort

    def testSerialPort( self, strComPort ):
        """
        Return a serial connection to the EiBotBoard
        Note: Need to close serial connection
        """
        logger.debug('Testing Serial Port')
        try:
            serialPort = serial.Serial( strComPort, timeout = 1 )
        
            serialPort.setRTS()
            serialPort.setDTR()
            serialPort.flushInput()
            serialPort.flushOutput()

            time.sleep( 0.1 ) 

            logger.debug('Writing to board')
            serialPort.write( 'v\r' )
            strVersion = serialPort.readline()
            logger.debug('Board Returned %s, should start with EBB' % strVersion )
            
            if strVersion and strVersion.startswith( 'EBB' ):
                logger.debug('Found EBB')
                return serialPort
            logger.debug('Failed Testing  %s' % strVersion )
            serialPort.close()
        
        except serial.SerialException as e:
            logger.exception(str(e))
            

        return None

    def doCommand(self, cmd):
        """
        Sends a string command to EiBotBoard
        """
        try:
            self.serialPort.write( cmd ) 
            response = self.serialPort.readlines()
            #for line in response:
                #logger.debug(line)
        #except Exception as e:
        #    pass
        except AttributeError as e:
#            logger.exception("fail as no Connection to serial port")
            pass


    def disableMotors(self):
        """
        Disables both motors on EiBotBoard
        """
        logger.info('Servos Disabled')
        self.doCommand('EM,0,0\r')
    
    def enableMotors(self):
        """
        Disables both motors on EiBotBoard
        """
        logger.info('Servos Enabled')
        self.doCommand('EM,%d,%d\r' % ( self.stepMode, self.stepMode ))
        
