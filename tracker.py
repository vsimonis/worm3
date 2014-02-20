from managers import WindowManager, CaptureManager
from finder import WormFinder
import numpy as np
import cv2
import utils
import time
import cv

class Tracker ( object ):
    
    def __init__( self ):
        self.captureSource = 'led_move1.avi'
        #self.captureSource = 0
        self.bugs = False
        self.debugMode = True
        self.mirroredPreview = False
        self._windowManager = WindowManager( 'Tracker', self.onKeypress)
        self._captureManager = CaptureManager( cv2.VideoCapture(self.captureSource), self._windowManager, self.mirroredPreview, self.debugMode )
        self._wormFinder = WormFinder('lazy', self.debugMode)

        
        self._subWindowManager = WindowManager( 'Subtraction', self.onKeypress )

        self._startTime = time.time()
        self._sampleFreq = 1 #in sec
        self._lastCheck = self._startTime - self._sampleFreq
        #self.localSub = 

    def run( self ):
        self._windowManager.createWindow()
        self._subWindowManager.createWindow()
        
        while self._windowManager.isWindowCreated:
            self._captureManager.enterFrame()




            frame = self._captureManager.frame
            if self.bugs: print 'frame type: %s\t%s\n' % (str(type(frame)), str(frame.dtype))
            
            #TODO: FindWorm
            self.localSub = self._wormFinder.processFrame( frame )
    
            if time.time() - self._lastCheck >= self._sampleFreq:
                self.localSub = self._wormFinder.processFrame( frame )
                self._wormFinder.decideMove()
                self._lastCheck = time.time()
            
                if self.debugMode:
            #Transform sub image for display
                    subN = np.zeros(self.localSub.shape)
                    cv2.normalize(self.localSub, subN, 0, 255, cv2.NORM_MINMAX)
                    if self.bugs: print 'subN\tmin: %d\tmax: %d\n%s\n\n' % (np.min(subN), np.max(subN),  str(subN) )
             #subN = cv2.normalize(sub, 0, 1, cv2.NORM_MINMAX)
                    subN = subN.astype(np.uint8) #uint8
                    #self._wormFinder.drawDebuggingPointGS( subN)
                    self._subWindowManager.show(subN)
            self._wormFinder.drawDebuggingPoint( frame )                

            #subN1 = (sub - np.min(sub) ) / (np.max(sub) - np.min(sub) ) * 255
            
            #print 'sub\tmin: %d\tmax: %d\n%s\n\n' % (np.min(sub), np.max(sub),  str(sub))
            
            #print 'subN1\tmin: %d\tmax: %d\n%s\n\n' % (np.min(subN1), np.max(subN1),  str(subN1))
            
            #subI = cv.fromarray(subN1)
            #subI1 = cv2.cv.CvtColor(subI, )
                    
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
