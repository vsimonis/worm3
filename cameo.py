from managers import WindowManager, CaptureManager
import cv2

class Cameo ( object ):
    
    def __init__( self ):
        self._windowManager = WindowManager( 'Cameo', self.onKeypress)
        self._captureManager = CaptureManager( cv2.VideoCapture(0), self._windowManager, True )
        


    def run( self ):
        self._windowManager.createWindow()
        while self._windowManager.isWindowCreated:
            self._captureManager.enterFrame()
            frame = self._captureManager.frame


            #TODO: FindWorm


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
                self._captureManager.startWritingVideo('screencast.mjpg', 
                         cv2.cv.CV_FOURCC('M','J','P','G') )
            else:
                self._captureManager.stopWritingVideo()
        elif keycode == 27: #escape
            self._windowManager.destroyWindow()


if __name__ == "__main__":
    Cameo().run()
