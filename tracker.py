from managers import WindowManager, CaptureManager
from finder import WormFinder
import cv2
import utils
import time

class Tracker ( object ):
    
    def __init__( self ):
        self.bugs = False
        self.debugMode = True
        self.mirroredPreview = False
        self._windowManager = WindowManager( 'Tracker', self.onKeypress)
        self._captureManager = CaptureManager( cv2.VideoCapture(0), self._windowManager, self.mirroredPreview, self.debugMode )
        self._wormFinder = WormFinder('lazy', self.debugMode)
        

    def run( self ):
        self._windowManager.createWindow()
        while self._windowManager.isWindowCreated:
            self._captureManager.enterFrame()
            frame = self._captureManager.frame

            
            #TODO: FindWorm
            if self.bugs:
                print '%s\ttracker\tprocess frame' % (time.ctime(time.time()))

            self._wormFinder.processFrame( frame )
 
            if self.debugMode:
                self._wormFinder.drawDebuggingPoint( frame )
                
            if self.bugs:
                print '%s\ttracker\tdecide move' % (time.ctime(time.time()))
            self._wormFinder.decideMove()
            

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
                self._captureManager.startWritingVideo('screencast.avi', 
                         cv2.cv.CV_FOURCC('M','J','P','G') )
            else:
                self._captureManager.stopWritingVideo()
        elif keycode == 27: #escape
            self._windowManager.destroyWindow()


if __name__ == "__main__":
    Tracker().run()
