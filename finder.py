import numpy as np
import utils
import time
from imgProc import imgProc
from managers import WindowManager
import cv2

class WormFinder ( object ):
    def __init__( self, method, debugMode ):


        self._bugs = False
        self._method = method #lazy, etc...
        self._d = debugMode #True or False
        self._ref = None
        self._sub = None

        self._colRef = -1
        self._rowRef = -1
        
        self._colWorm = -1
        self._rowWorm = -1

        self._colDistances = []
        self._rowDistances = []

        self._meanColDistances = 0
        self._meanRowDistances = 0

        self._window = 10
        self._boundRow = 200
        self._boundCol = 200

    #@property
    def hasReference ( self ):
        return self._ref is not None

    @property
    def hasReferenceLocation ( self ):
        return self._colRef  >= 0

    @property
    def lenDistanceArray ( self ):
        return len(self._colDistances)

    @staticmethod
    def rgb2grayV ( imgIn ): #not sure self goes here
        """
        """
        try:
            imgIn = np.array(imgIn)#.astype(float)
            imgOut = 1.0 / 3 * ( imgIn[:,:,0] + imgIn[:,:,1] + imgIn[:,:,2] )
        except ValueError:
            'print not a 3-D array'
        finally:
            return imgOut#.astype(int)


    def findWormLazy ( self ):
        if self.hasReference():
            self._sub = self._img - self._ref
            
            #Gaussian blur
            self._sub  = cv2.GaussianBlur( self._sub, (45, 45) , 10 )
            
            if not self.hasReferenceLocation: #only process ref image first time 'round
                x, y = np.nonzero ( self._sub == np.min( self._sub ) )
                self._colRef, self._rowRef = x[0], y[0]
            
            
            a, b = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location
            self._colWorm, self._rowWorm = a[0], b[0]
            if self._d: print '%s\tfinder\tcol:%d\t\trow:%d' % ( time.ctime(time.time()) , self._rowWorm , self._colWorm )

            self._colDistances.append(self._colRef - self._colWorm)
            self._rowDistances.append(self._rowRef - self._rowWorm)

            if ( self.lenDistanceArray > self._window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))


    def findWormFull ( self ):
        self._colRef = self._img.shape[1] / 2
        self._rowRef = self._img.shape[0] / 2
        
        x, y, imgOut = imgProc.getCentroidFromRaw( self._img )
        
        self._sub = imgOut
        
        self._rowWorm = int(y)
        self._colWorm = int(x)

        self._colDistances.append(self._colRef - self._colWorm)
        self._rowDistances.append(self._rowRef - self._rowWorm)

        if ( self.lenDistanceArray > self._window ):
            self._colDistances = self._colDistances[1:] #pop
            self._rowDistances = self._rowDistances[1:] #pop


        self._meanColDistances = int(np.mean(self._colDistances))
        self._meanRowDistances = int(np.mean(self._rowDistances))



    def findWormPCA ( self ):
        return

    def findWormBox ( self ):
        return

    def processFrame ( self, img ):

        options = {
            'lazy' : self.findWormLazy,
            'full' : self.findWormFull, #segmentation
            'pca'  : self.findWormPCA, 
            'box'  : self.findWormBox
            }

        if self._d: 
            if self._bugs: print '%s\tfinder\tHas reference: %s' % ( time.ctime(time.time()), str(self.hasReference()) )

        if self._method == 'lazy' and not self.hasReference(): #is this OK???

            self._ref = self.rgb2grayV( img ) ###USE OPENCV RGB2GRAY

            if self._bugs: print 'ref  type: %s\t%s\n' % (str(type(self._ref)), str(self._ref.dtype))
            self._sub = np.zeros(self._ref.shape) ##For display
            if self._d and self._bugs:
                print '%s\tfinder\tNew Reference' % ( time.ctime(time.time()) )
        elif self.hasReference() or self.method == 'full':
            if self._d and self._bugs:
                print '%s\tfinder\tNew Comparison' % ( time.ctime(time.time()) )
            self._img = self.rgb2grayV( img )
            if self._bugs: print 'img  type: %s\t%s\n' % (str(type(self._img)), str(self._img.dtype))
            #self._sub = self._img ## For display
            
            try:
                options[self._method]()
            except KeyError:
                self.findWormLazy() #default

        return self._sub

    def decideMove ( self ):
        if self._colRef < 0 and self._method == 'lazy':
            if self._bugs: print '!!!!!!!!!!!!!! NO REFERENCE, NEXT FRAME PLZ !!!!!!!!!'
            return
        else:
            if self._bugs: print '~~~~~~~~~~~~~~ HAS REFERENCE, DECIDE ~~~~~~~~~~~'
            if ( abs(self._meanColDistances) > self._boundCol or abs(self._meanRowDistances) > self._boundRow ):
                if self._d: print '%s\tfinder\t!!!!!!!!!!!!!!!!MOVE!!!!!!!!!!!!!!!!' % time.ctime(time.time())
                self._ref = None
                self._colRef = -1
                self._rowRef = -1
                self._colDistances = []
                self._rowDistances = []
                self._colWorm = -1
                self._rowWorm = -1

    def drawDebuggingPoint( self, img ):
        #BRG
        green = [0, 255, 0]
        red = [0, 0, 255]
        blue = [255, 0, 0]
        utils.drawPoint(img, self._colWorm, self._rowWorm, red)
        utils.drawPoint(img, self._colRef, self._rowRef, blue)
        utils.drawPoint(img, self._colRef - self._meanColDistances, self._rowRef - self._meanRowDistances, green)

    def odrawDebuggingPointGS( self, img ):
        #BRG
       
        utils.drawPoint(img, self._colWorm, self._rowWorm, 255)
        utils.drawPoint(img, self._colRef, self._rowRef, 0)
        utils.drawPoint(img, self._colRef - self._meanColDistances, self._rowRef - self._meanRowDistances, 255)

