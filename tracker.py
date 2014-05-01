import logging
import optparse
import sys

from managers import WindowManager, CaptureManager
from finder import WormFinder
from easyEBB import easyEBB
import numpy as np
import cv2
import utils
import time


logt = logging.getLogger('')

class Tracker ( object ):
    
    def __init__( self, method, src ):

        ### Sensitivity of tracker params
        self._sampleFreq = 0.1 #in sec
        
        ### Set Camera params
        #self.resolution = (640, 480 )
        self.resolution = (1080, 1080)
        source = {
            0:0, 
            1:1, 
            2:'led_move1.avi', 
            3:'screencast.avi', 
            4:'screencast 1.avi',
            5: 'shortNoBox.avi',
            6: 'longNoBox.avi',
            7: 'H299.avi'
            }
        self.color = False
        self.captureSource = source[int(src)]
        
        ### Timing initialization
        self._startTime = time.time()
        self._lastCheck = self._startTime - self._sampleFreq

        ### Display params
        self.mirroredPreview = False


        ### Initialize Objects       

        ##### Windows

        self._windowManager = WindowManager( 'Tracker', self.onKeypress )

        ### Capture -- resolution set here
        self._captureManager = CaptureManager( 
            cv2.VideoCapture(self.captureSource), 
            self._windowManager, 
            self.mirroredPreview, self.resolution)

        actualCols, actualRows = self._captureManager.getResolution()
        ## from here on out use this resolution 
        
        ### Arguments for finder
        self.finderArgs = {
            'method' : method,
            'gsize' :  45,
            'gsig' : 9,
            'window' : 3,
            'boundBoxRow' : 150,
            'boundBoxCol' : 150,
            'limRow' : 60,
            'limCol' : 60,
            'MAXONEFRAME': 500,
            'REFPING' : 600000,
            'MAXREF': 1000,
            'capCols':actualCols,
            'capRows': actualRows,
            'color' : False
            }

        self._wormFinder = WormFinder( **self.finderArgs )     

        ##### Debugging
        self._bugWindowManager = WindowManager( 'Debugger', self.onKeypress )



    def run( self ):

        self._windowManager.createWindow()

        if self.isDebug and self.finderArgs['method'] != 'test':
            self._bugWindowManager.createWindow()

        while self._windowManager.isWindowCreated:    
            
            self._captureManager.enterFrame()
            t1 = time.time()
            # Get frame
            frame = self._captureManager.frame

            if not self._captureManager.gotFrame:
                self.shutDown()
                break

            if time.time() - self._lastCheck >= self._sampleFreq:
                
                ###### SURF & SIFT  ######
                if self.finderArgs['method'] == 'surf' or self.finderArgs['method'] == 'sift' or self.finderArgs['method'] == 'mser':
                    self.localSub = self._wormFinder.processFrame( frame )
                    self._bugWindowManager.show(self.localSub)
                    
                ###### LAZY ######
                if self.finderArgs['method'] == 'lazy' or  self.finderArgs['method'] == 'lazyc' or self.finderArgs['method'] == 'lazyd':
                    ### Possibly move this to a different thread :(
                    self.localSub = self._wormFinder.processFrame( frame )
                    self._wormFinder.decideMove()                
                    self._lastCheck = time.time()
                    
                    if self.isDebug and self.color:
                        #print self.localSub
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
                if self.finderArgs['method'] == 'lazy':
                    self._wormFinder.drawDebuggingPoint( frame )                
                if self.finderArgs['method'] == 'lazyc':
                    if not self.color:
                        self._wormFinder.drawDebuggingPointCroppedBW( frame )       
                    else:
                        self._wormFinder.drawDebuggingPointCropped( frame )       

                if self.finderArgs['method'] == 'lazyd':
                    self._wormFinder.drawDebuggingPointCroppedDemo( frame )

                if self.finderArgs['method'] == 'test' or self.finderArgs['method'] == 'conf': 
                    if self.color:
                        self._wormFinder.drawDebug( frame )
                    else:
                        self._wormFinder.drawDebugBW( frame )
            self._captureManager.exitFrame()
            self._windowManager.processEvents()
            #logt.info('frame processing took: %0.6f' % (time.time() - t1))
    @property
    def isDebug( self ):
        return logt.getEffectiveLevel() <= logging.INFO

    def shutDown( self ):
        self._windowManager.destroyWindow()
        #if not self.isDebug:
        if self._captureManager.isWritingVideo:
            self._captureManager.stopWritingVideo()
        try:
#            self._wormFinder.writeOut('%s-%s' % (self.finderArgs['method'], self.captureSource))
            self._wormFinder.servos.disableMotors()
            self._wormFinder.servos.closeSerial()
        except Exception as e:
            logt.exception(str(e))

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
                    'worm%s.avi' % time.strftime("%Y_%m_%d-%H-%M-%S", time.localtime(time.time())),
                    cv2.cv.CV_FOURCC('M','J','P','G'))
            else:
                self._captureManager.stopWritingVideo()

        elif keycode == 27: #escape
            self.shutDown()
            
def main():

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
        method = 'lazyc'
    else:
        method = options.tracker_method          

    if options.source is None:
        source = 0
    else:
        source = options.source
        
    ## Set up logging
    logging.basicConfig(
        level=logging_level, 
        filename=options.logging_file,
        format='%(asctime)s\t%(levelname)s\t%(name)s\t\t%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logt = logging.getLogger('')
    t = Tracker(method,source)
    
    t.run()

if __name__ == '__main__':
    main()

