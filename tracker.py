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

        self._rawWindow = WindowManager( 'RawFeed', self.onKeypress )

        ### Capture -- resolution set here
        self._cap = CaptureManager( 
            cv2.VideoCapture(self.captureSource), 
            self._rawWindow, 
            self.mirroredPreview, self.resolution)

        actualCols, actualRows = self._cap.getResolution()
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
        self._overlayWindow = WindowManager( 'Overlay', self.onKeypress )
        self.motorsOn = False






    def run( self ):

        # Show windows
        self._rawWindow.createWindow()
        self._overlayWindow.createWindow()

        while self._rawWindow.isWindowCreated:
            self._cap.enterFrame()
            frame = self._cap.frame

            # Probably not useful, removes errors when playing from video
#            if not self._captureManager.gotFrame:
#                self.shutDown()
#                break

            # Display raw frame to rawWindow
            
            t1 = time.time()
            # Get frame
            frame = self._cap.frame

            # Show frame to raw feed
            self._rawWindow.show(frame)

            # If tracking is enabled or motors are on, start tracking
            
            if time.time() - self._lastCheck >= self._sampleFreq and self.motorsOn :
                if self.finderArgs['method'] == 'lazyc':
                    self.gaussian = self._wormFinder.processFrame( frame )
                    self.overlayImage = frame
                    self._wormFinder.decideMove()
                    self._lastCheck = time.time()
                    self._overlayWindow.show(self.overlayImage)
                    self._wormFinder.drawDebuggingPointCroppedBW( self.overlayImage )       
                    

                if self.finderArgs['method'] == 'test' or self.finderArgs['method'] == 'conf': 
                    if self.color:
                        self._wormFinder.drawDebug( frame )
                    else:
                        self._wormFinder.drawDebugBW( frame )

            self._cap.exitFrame()
            self._rawWindow.processEvents()
            #logt.info('frame processing took: %0.6f' % (time.time() - t1))
    
    @property
    def isDebug( self ):
        return logt.getEffectiveLevel() <= logging.INFO

    def shutDown( self ):
        self._rawWindow.destroyWindow()
        #if not self.isDebug:
        if self._cap.isWritingVideo:
            self._cap.stopWritingVideo()
        try:
#            self._wormFinder.writeOut('%s-%s' % (self.finderArgs['method'], self.captureSource))
            self._wormFinder.servos.disableMotors()
            self._wormFinder.servos.closeSerial()
        except Exception as e:
            logt.exception(str(e))

    def onKeypress ( self, keycode ):
        '''
        Keypress options
        <SPACE> --- Motors On
        < TAB > --- start/stop recording screencast
        < ESC > --- quit

        '''

        if keycode == 32: #space
            if self.motorsOn:
                self.motorsOn = False#_captureManager.writeImage('screenshot.png')
                self._wormFinder.servos.disableMotors()
            else:
                self.motorsOn = True
                self._wormFinder.servos.enableMotors()
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

