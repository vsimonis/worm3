from managers import WindowManager, CaptureManager
from finder import WormFinder
import numpy as np
import cv2
import utils
import time
import cv
from clogger import vLog
import logging
import parser

class Tracker ( object ):
    
    def __init__( self ):


        self._sampleFreq = 0.5 #in sec

        #self.captureSource = 'led_move1.avi'
        self.captureSource = 0
        self.bugs = False
        self.debugMode = True
        self.mirroredPreview = False
        self.method = 'lazy'#'full' #'lazy'
        
        self.cambug = True
        self.changeRes = True
        

        self._windowManager = WindowManager( 'Tracker', self.onKeypress )
        self._captureManager = CaptureManager( cv2.VideoCapture(self.captureSource), self._windowManager, self.mirroredPreview, self.debugMode )
        self._wormFinder = WormFinder(self.method, self.debugMode)

        #if self.method == 'lazy':
        self._bugWindowManager = WindowManager( 'Debugger', self.onKeypress )

        self._startTime = time.time()

        self._lastCheck = self._startTime - self._sampleFreq
        #self.localSub = 

        self._l = vLog()

    def run( self ):
        self._windowManager.createWindow()
        
        if self.debugMode: self._bugWindowManager.createWindow()
        if self.cambug and self.changeRes:
            self._captureManager.setProps()
        while self._windowManager.isWindowCreated:
            
            self._captureManager.enterFrame()
            frame = self._captureManager.frame

            if self.cambug:
                self._captureManager.getProps()

            if time.time() - self._lastCheck >= self._sampleFreq:
                
                if self.method == 'lazy':
                    self.localSub = self._wormFinder.processFrame( frame )
                    self._wormFinder.decideMove()                
                    self._lastCheck = time.time()
                    
                    if self.debugMode:
                        subN = np.zeros(self.localSub.shape)
                        cv2.normalize(self.localSub, subN, 0, 255, cv2.NORM_MINMAX)
                        self._l.debug('subN\tmin: %d\tmax: %d\n%s\n\n' % (np.min(subN), np.max(subN),  str(subN) ))
                       # if self.bugs: print 'subN\tmin: %d\tmax: %d\n%s\n\n' % (np.min(subN), np.max(subN),  str(subN) )
                        subN = subN.astype(np.uint8) #uint8
                        self._bugWindowManager.show(subN)

                if self.method == 'full':
                    a = time.time()
                    self.localSub = self._wormFinder.processFrame( frame )
                    print 'TIME: %d' % (time.time() - a)
                    self._wormFinder.decideMove()                
                    self._lastCheck = time.time()
                    
                    if self.debugMode:
                        self._bugWindowManager.show(self.localSub)
            if self.debugMode:
                self._wormFinder.drawDebuggingPoint( frame )                
            self._captureManager.exitFrame()
            self._windowManager.processEvents()


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
                self._captureManager.startWritingVideo('worm%s.avi' % time.ctime(time.time()) , 
                         cv2.cv.CV_FOURCC('M','J','P','G') )
            else:
                self._captureManager.stopWritingVideo()
        elif keycode == 27: #escape
            self._windowManager.destroyWindow()
        
        if keycode == 9: #backspace
            if self.debugMode:
                self.debugMode = True
            else:
                self.debugMode = False




def main():
    
    LOGGING_LEVELS = {'critical': self.l.CRITICAL,
                  'error': self.l.ERROR,
                  'warning': self.l.WARNING,
                  'info': self.l.INFO,
                  'debug': self.l.DEBUG,
                  'camera': self.l.CAMERA}



    parser = optparse.OptionParser()
    parser.add_option('-l', '--logging-level', help='Logging level')
    parser.add_option('-f', '--logging-file', help='Logging file name')
    (options, args) = parser.parse_args()
    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
    logging.basicConfig(level=logging_level, filename=options.logging_file,
                      format='%(asctime)s %(levelname)s: %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')

    # Your program goes here.
    # You can access command-line arguments using the args variable.


if __name__ == "__main__":
    main()
    Tracker().run()

