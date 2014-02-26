import sys
import numpy as np
import utils
import time
from imgProc import imgProc
from managers import WindowManager
from easyEBB import easyEBB
import cv2
import logging

logger = logging.getLogger('finder')

class WormFinder ( object ):
    '''
    arguments given:
    - method
    - gsize (size of gaussian filter)
    - gsig (sigma for gaussian filter)
    - window (number of locations to avg)
    - boundRow (decision distance for row)
    - boundCol (decision distance for column)
    '''
    def __init__( self, **kwargs ) :
        
        for k in kwargs.keys():
            if k in ['method', 'gsize', 'gsig', 'window', 
                     'boundRow', 'boundCol', 
                     'MAXONEFRAME', 'REFPING', 'MAXREF']:
                self.__setattr__(k, kwargs[k])
    
        ### 'lazy' Parameters
        self._ref = None
        self._sub = None
        self.lastRefTime = time.time()

        ## General Parameters
        self._colRef = -1
        self._rowRef = -1
        
        self._colWorm = -1
        self._rowWorm = -1

        self._colDistances = []
        self._rowDistances = []

        self._meanColDistances = 0
        self._meanRowDistances = 0

        self.servos = easyEBB((1080, 1080), (5,5), 5)
#        self.MAXONEFRAME = 30
#        self.REFPING = 60

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
            logging.exception('not a 3-D array')
        except IndexError:
            sys.exit(0)
        
        return imgOut



    def findWormLazy ( self ):
        t = time.time()
        if self.hasReference():
            self._sub = self._img - self._ref

            #Gaussian blur
            self._sub  = cv2.GaussianBlur( self._sub, 
                                           (self.gsize, self.gsize) , self.gsig )

            #only process ref image first time 'round
            if not self.hasReferenceLocation: 
                x, y = np.nonzero ( self._sub == np.min( self._sub ) )
                self._colRef, self._rowRef = x[0], y[0]
                logger.debug( 'Reference: col:%d\t\trow:%d' % 
                          ( self._rowRef , self._colRef ))

            
            a, b = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location
            self._colWormPrev, self._rowWormPrev = self._colWorm, self._rowWorm
            self._colWorm, self._rowWorm = a[0], b[0]
            logger.debug( 'Worm: col:%d\t\trow:%d' % 
                          ( self._rowWorm , self._colWorm ))

            self._colDistances.append(self._colRef - self._colWorm)
            self._rowDistances.append(self._rowRef - self._rowWorm)

            if ( self.lenDistanceArray > self.window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))
        logger.info('runtime: %0.3f' % (time.time() - t) )

    def findWormFull ( self ):
        t = time.time()
        self._colRef = self._img.shape[1] / 2
        self._rowRef = self._img.shape[0] / 2
        
        x, y, imgOut = imgProc.getCentroidFromRaw( self._img )
        
        self._sub = imgOut
        self._colWormPrev, self._rowWormPrev = self._colWorm, self._rowWorm
        self._rowWorm = int(y)
        self._colWorm = int(x)

        logger.debug( 'Location: col:%d\t\trow:%d' % 
                          ( self._rowWorm , self._colWorm ))

        self._colDistances.append(self._colRef - self._colWorm)
        self._rowDistances.append(self._rowRef - self._rowWorm)

        if ( self.lenDistanceArray > self.window ):
            self._colDistances = self._colDistances[1:] #pop
            self._rowDistances = self._rowDistances[1:] #pop


        self._meanColDistances = int(np.mean(self._colDistances))
        self._meanRowDistances = int(np.mean(self._rowDistances))
        logger.info('runtime: %0.3f' % (time.time() - t) )


    def findWormPCA ( self ):
        return

    def findWormBox ( self ):
        return

    def processFrame ( self, img ):
        #logger.debug('enter process frame')
        options = {
            'lazy' : self.findWormLazy,
            'full' : self.findWormFull, #segmentation
            'pca'  : self.findWormPCA, 
            'box'  : self.findWormBox
            }

        if self.method == 'lazy':
            #logger.debug('Confirm lazy')
            if not self.hasReference(): #is this OK???
                #logger.debug('Retrieve New Reference')
                self._ref = self.rgb2grayV( img ) ###USE OPENCV RGB2GRAY
                self._sub = np.zeros(self._ref.shape) ##For display
                self.lastRefTime = time.time()

            else:
                self._img = self.rgb2grayV( img )           
                try:
                    options[self.method]()
                except KeyError:
                    self.findWormLazy() #default
        return self._sub ## gets displayed in the window

    def decideMove ( self ):
        if self.method == 'lazy':
            if time.time() - self.lastRefTime >= self.REFPING:
                self.resetRef()
                logger.warning('New reference based on PING')

            if self._colRef < 0:
                return 

            ### Possible move: make sure
            elif ( abs(self._meanColDistances) > self.boundCol or abs(self._meanRowDistances) > self.boundRow ):
                ## Check previous location of worm
                if abs ( self._rowWormPrev - self._rowWorm ) > self.MAXONEFRAME or abs( self._colWormPrev - self._colWorm ) > self.MAXONEFRAME:
                    logger.warning('Impossible location: too far from previous')
                    self._rowWorm = self._rowWormPrev
                    self._colWorm = self._colWormPrev
                    self._colDistances = []
                    self._rowDistances = []
                    return
                ## Check relative position to reference
                elif ( abs ( self._rowRef - self._rowWorm) > self.MAXREF or abs ( self._colRef - self._colWorm) > self.MAXREF):
                    logger.warning('Impossible location: too far from ref')
                    return
                else:
                    logger.warning('MOVE!!!')
                    if self.isDebug:
                        self.servos.centerWorm(60, self._colWorm, self._rowWorm)

                    self.resetRef()
                    self._colWorm = -1
                    self._rowWorm = -1

#            elif self.hasReference and (self._colRef > 900 or self._rowRef > 900):
#                self.resetRef()
#                return

    def drawDebuggingPoint( self, img ):
        #BRG
        green = [0, 255, 0]
        red = [0, 0, 255]
        blue = [255, 0, 0]
        utils.drawPoint(img, self._colWorm, self._rowWorm, red)
        utils.drawPoint(img, self._colRef, self._rowRef, blue)
        utils.drawPoint(img, self._colRef - self._meanColDistances, self._rowRef - self._meanRowDistances, green)

    def drawDebuggingPointGS( self, img ):
        #BRG       
        utils.drawPoint(img, self._colWorm, self._rowWorm, 255)
        utils.drawPoint(img, self._colRef, self._rowRef, 0)
        utils.drawPoint(img, self._colRef - self._meanColDistances, self._rowRef - self._meanRowDistances, 255)

    def isDebug( self ):
        return logger.getEffectiveLevel == logging.DEBUG
    
    def resetRef( self ):
        self._ref = None
        self._colRef = -1
        self._rowRef = -1
        self._colDistances = []
        self._rowDistances = []
        #self._colWorm = -1
        #self._rowWorm = -1
            
    
    
