import numpy as np
import utils
import time

class WormFinder ( object ):
    def __init__( self, method, debugMode ):
        
        self._bugs = False
        self._method = method #lazy, etc...
        self._d = debugMode #True or False
        self._ref = None
        
        self._colRef = -1
        self._rowRef = -1
        
        self._colWorm = -1
        self._rowWorm = -1

        self._colDistances = []
        self._rowDistances = []

        self._meanColDistances = 0
        self._meanRowDistances = 0

        self._window = 5
        self._boundRow = 100
        self._boundCol = 100

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
           imgOut = 1.0/3 * ( imgIn[:,:,0] + imgIn[:,:,1] + imgIn[:,:,2] )
        except ValueError:
            'print not a 3-D array'
        finally:
            return imgOut


    def findWormLazy ( self ):
        if self.hasReference():
            sub = self._img - self._ref

            if not self.hasReferenceLocation: #only process ref image first time 'round
                x, y = np.nonzero ( sub == np.min( sub ) )
                self._colRef, self._rowRef = x[0], y[0]
            
            
            a, b = np.nonzero ( sub == np.max( sub ) ) #worm location
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
        return

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
        if not self.hasReference(): #is this OK???
            self._ref = self.rgb2grayV( img )
            if self._d and self._bugs:
                print '%s\tfinder\tNew Reference' % ( time.ctime(time.time()) )
        else:
            if self._d and self._bugs:
                print '%s\tfinder\tNew Comparison' % ( time.ctime(time.time()) )
            self._img = self.rgb2grayV( img )
            try:
                options[self._method]()
            except KeyError:
                self.findWormLazy() #default


    def decideMove ( self ):
        if self._colRef < 0 :
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
