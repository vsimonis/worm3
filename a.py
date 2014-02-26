import logging
import optparse

from managers import WindowManager, CaptureManager
from finder import WormFinder
from easyEBB import easyEBB
import numpy as np
import cv2
import utils
import time
import cv

logger = logging.getLogger('tracker')

class Tracker ( object ):
    
    def __init__( self, method, src ):

        ### Sensitivity of tracker params
        self._sampleFreq = 0.1 #in sec
        
        ### Arguments for finder
        self.finderArgs = {
            'method' : method,
            'gsize' :  45,
            'gsig' : 9,
            'window' : 3,
            'boundRow' : 200,
            'boundCol' : 200,
            'MAXONEFRAME': 1000,
            'REFPING' : 30,
            'MAXREF': 1000
            }
            

        ### Camera params
        self.changeRes = True
        source = {0:0, 1:1, 2:'led_move1.avi', 3:'screencast.avi', 4:'screencast 1.avi'}
        self.captureSource = source[int(src)]
        #self.captureSource = 1
        
        ### Debugging params
        self.cambug = True

        ### Timing initialization
        self._startTime = time.time()
        self._lastCheck = self._startTime - self._sampleFreq

        ### Display params
        self.mirroredPreview = False 


        ### Initialize Objects
        ##### Standard
        self._windowManager = WindowManager( 'Tracker', self.onKeypress )

        self._captureManager = CaptureManager( 
            cv2.VideoCapture(self.captureSource), 
            self._windowManager, 
            self.mirroredPreview)

        self._wormFinder = WormFinder( **self.finderArgs )
        


        ##### Debugging
        self._bugWindowManager = WindowManager( 'Debugger', self.onKeypress )

    def run( self ):
        self._windowManager.createWindow()
        
        if self.isDebug:
            self._bugWindowManager.createWindow()
        
        if self.cambug and self.changeRes:
            self._captureManager.setProps()
        
        while self._windowManager.isWindowCreated:    
            self._captureManager.enterFrame()
            frame = self._captureManager.frame

            if self.cambug:
                self._captureManager.getProps()

            if time.time() - self._lastCheck >= self._sampleFreq:
                ###### LAZY ######
                if self.finderArgs['method'] == 'lazy':
                    ### Possibly move this to a different thread :(
                    self.localSub = self._wormFinder.processFrame( frame )
                    self._wormFinder.decideMove()                
                    self._lastCheck = time.time()
                    
                    if self.isDebug:
                        subN = np.zeros(self.localSub.shape)
                        cv2.normalize(self.localSub, 
                                      subN, 0, 255, cv2.NORM_MINMAX)            
                        self.localSub = subN.astype(np.uint8) #uint8
                        self._bugWindowManager.show(self.localSub)
                
                ###### FULL ######
                if self.finderArgs['method'] == 'full':
                    a = time.time()
                    self.localSub = self._wormFinder.processFrame( frame )
                    #print 'TIME: %d' % (time.time() - a)
                    self._wormFinder.decideMove()                
                    self._lastCheck = time.time()                    
                    if self.isDebug:
                        self._bugWindowManager.show(self.localSub)

            if self.isDebug:
                self._wormFinder.drawDebuggingPoint( frame )                
                self._wormFinder.drawDebuggingPoint( self.localSub )
            self._captureManager.exitFrame()
            self._windowManager.processEvents()

    @property
    def isDebug( self ):
        return logger.getEffectiveLevel() <= logging.WARNING

    def onKeypress ( self, keycode ):
        '''
        Keypress options
        <SPACE> --- screenshot
        < TAB > --- start/stop recording screencast
        < ESC > --- quit

        '''

        if keycode == 32: #space
            self._captureManager.writeImage('screenshot.png')
        elif keycode == 9: #tab
            if not self._captureManager.isWritingVideo:
                self._captureManager.startWritingVideo(
                    'worm%s.avi' % time.ctime(time.time()) , 
                    cv2.cv.CV_FOURCC('M','J','P','G'))
            else:
                self._captureManager.stopWritingVideo()
        elif keycode == 27: #escape
            self._windowManager.destroyWindow()
            self._wormFinder.servos.disableMotors()
            self._wormFinder.servos.closeSerial()

        if keycode == 8: #backspace
            if self.isDebug:
                logger.setLevel(logging.INFO)
            else:
                logger.setLevel(logging.DEBUG)

def main():
    logger = logging.getLogger('tracker')
    LOGGING_LEVELS = {'critical': logging.CRITICAL,
             'error': logging.ERROR,
             'warning': logging.WARNING,
             'info': logging.INFO,
             'debug': logging.DEBUG}

    parser = optparse.OptionParser()
    parser.add_option('-l', '--logging-level', help='Logging level')
    parser.add_option('-f', '--logging-file', help='Logging file name')
    parser.add_option('-m', '--tracker-method', help='Name of tracker: lazy, full')
    parser.add_option('-s', '--source', help='video source')

    (options, args) = parser.parse_args()

    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
    
    if options.tracker_method is None:
        method = 'lazy'
    else:
        method = options.tracker_method          

    if options.source is None:
        source = 'led_move1.avi'
    else:
        source = options.source
        
    logging.basicConfig(level=logging_level, filename=options.logging_file,
                 format='%(asctime)s\t%(levelname)s\t%(name)s\t\t%(message)s',
                 datefmt='%Y-%m-%d %H:%M:%S')

    t = Tracker(method,source)
    t.run()

if __name__ == '__main__':
    main()
#    Tracker().run()
