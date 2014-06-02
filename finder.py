import sys
import numpy as np
import pandas as pd
import utils
import time
from imgProc import imgProc
from managers import WindowManager
from easyEBB import easyEBB
import cv2
import logging


# COLORS

#BRG
BLUE = [255, 0, 0]
GREEN = [0, 255, 0]
RED = [0, 0, 255]
WHITE3 = [255, 255, 255]
BLACK3 = [0,0,0]

#gray scale
WHITE = 255
BLACK = 0
 

logger = logging.getLogger('finder')
class WormFinder ( object ):
    
    '''
    arguments given:
    - method
    - gsize (size of gaussian filter)
    - gsig (sigma for gaussian filter)
    - window (number of locations to avg)
    '''
    def __init__( self, **kwargs ) :
        
        for k in kwargs.keys():
            if k in ['method', 'gsize', 'gsig', 'window', 
                     'MAXONEFRAME', 'REFPING', 'MAXREF', 
                     'captureSize', 'cropRegion', 'decisionBoundary',
                     'color']:
                self.__setattr__(k, kwargs[k])

        self.trackerConnected = False

        ### Timing ###
        self.lastRefTime = time.time()        
        self.pauseFrame = 0 #cropping wise
        self.nPauseFrames = 20 #cropping wise
        
        self.breakDuration = 3 # motor wise
        self.breakStart = time.time()

        ### Worm Finding
        ## points
        self.wormLocation = utils.Point(-1 , -1 ) 
        self.wormLocationPrevious = utils.Point( -1, -1)
        self.frameCenter = utils.Point(self.captureSize.ncols / 2, self.captureSize.nrows / 2)

        ## images 
        self.refImg = None
        self.subImg = None
        self.croppedImg = None

        ### Cropping ###
        self.cmin = 0
        self.cmax = self.captureSize.ncols
        self.rmin = 0
        self.rmax = self.captureSize.nrows



        ### Logging ###
        logger.debug('Debug level: %s' % logger.getEffectiveLevel() )
        logger.debug('is Debug?: %s' % str(self.isDebug()))

        if self.initializeMotors: 
            self.servos = easyEBB()
    
    """
    Impacting Program Flow
    """
    @property
    def initializeMotors( self ):
        if self.method == 'conf' or not self.motorsOn:
            return False
        else: 
            return True

    @property
    def hasReference ( self ):
        return self.refImg is not None

    @property
    def isColor ( self ):
        return self.color

    def resetRef( self ):
        self.pauseFrame = 0
        self.refImg = None
                ### Cropping ###
        self.cmin = 0
        self.cmax = self.captureSize.ncols
        self.rmin = 0
        self.rmax = self.captureSize.nrows


    """ 
    FIND WORMS
    """
    def wormTest ( self ): 
        return
    
    def lazy (self ):
        self.findWorm(self.wormLocation)
    
    def lazyDemo (self):
        self.findWorm(self.frameCenter)

    def findWorm ( self, cropPoint ):
        t = time.time()
    
        if self.hasReference:
            # Subtract images 
            self.subImg = cv2.subtract(self.refImg, self._img)

            # If timing is right, crop!
            if self.croppedSearchSpace():
                self.calculateCrop(cropPoint) # crop with cropPoint as center
                # perform crop
                self.subImg = self.subImg[self.rmin : self.rmax, self.cmin : self.cmax]
           
            # Gaussian Blur
            self.subImg  = cv2.GaussianBlur( self.subImg, 
                                           (self.gsize, self.gsize) , self.gsig )
            # Worm Location
            r, c = np.nonzero ( self.subImg == np.max( self.subImg ) )
            self.wormLocation.update( c[0] + self.cmin, r[0] + self.rmin)
            self.wormLocationPrevious.update( self.wormLocation.col, self.wormLocation.row )
            
            self.pauseFrame += 1
            self.justMoved = False #necessary?

        else:
            return
    
    def findWorm ( self, cropPoint ):
        t = time.time()
        if self.hasReference:
            # Subtract images 
            self.subImg = cv2.subtract(self.refImg, self._img)

            # If timing is right, crop!
            if self.croppedSearchSpace():
                self.calculateCrop(cropPoint) # crop with cropPoint as center
                # perform crop
                self.subImg = self.subImg[self.rmin : self.rmax, self.cmin : self.cmax]
           
            # Gaussian Blur
            self.subImg  = cv2.GaussianBlur( self.subImg, 
                                           (self.gsize, self.gsize) , self.gsig )
            # Worm Location
            r, c = np.nonzero ( self.subImg == np.max( self.subImg ) )
            self.wormLocation.update( c[0] + self.cmin, r[0] + self.rmin)
            self.wormLocationPrevious.update( self.wormLocation.col, self.wormLocation.row )
            
            self.pauseFrame += 1
            self.justMoved = False #necessary?

        else:
            return
    
    def lazyNoCrop(self):
        self.findWormNoCropping( 'nada')

    def findWormNoCropping ( self, cropPoint ):
        t = time.time()
    
        if self.hasReference:
            # Subtract images 
            self.subImg = cv2.subtract(self.refImg, self._img)

            # Gaussian Blur
            self.subImg  = cv2.GaussianBlur( self.subImg, 
                                           (self.gsize, self.gsize) , self.gsig )
            # Worm Location
            r, c = np.nonzero ( self.subImg == np.max( self.subImg ) )
            self.wormLocation.update( c[0] + self.cmin, r[0] + self.rmin)
            self.wormLocationPrevious.update( self.wormLocation.col, self.wormLocation.row )
            
            self.pauseFrame += 1
            self.justMoved = False #necessary?

        else:
            return

    def croppedSearchSpace ( self ):
        return self.pauseFrame > self.nPauseFrames

    def calculateCrop ( self, p ):
        self.cropRegion.update(p)
        self.cmin = self.cropRegion.left
        self.cmax = self.cropRegion.right
        self.rmin = self.cropRegion.top
        self.rmax = self.cropRegion.bottom

    """
    DISPATCH
    lazyd -> keep decision boundary restricted to center of the image
    lazy  -> use full image
    
    """

    def processFrame ( self, img ):

        options = {
            'test' : self.wormTest,
            'conf' : self.wormTest,
            'lazy' : self.lazyNoCrop,
            'lazyc': self.lazy, 
            'lazyd': self.lazyDemo
            }
        t = time.time()
        

        if self.method in ['lazy','lazyc','lazyd']:
            if not self.hasReference:
                if self.isColor:
                    self.refImg = cv2.cvtColor(img, cv2.cv.CV_RGB2GRAY)
                else:
                    self.refImg = img
                self.lastRefTime = time.time()
            else: # Has reference, normal execution
                if self.isColor:
                    self._img = cv2.cvtColor(img, cv2.cv.CV_RGB2GRAY)
                else:
                    self._img = img
                try:
                    options[self.method]()
                except KeyError:
                    self.lazy() #default

        return self.subImg ## gets displayed in the window
    

    def decideMove ( self ):
        t = time.time()

        if not self.hasReference:
            return
        if not self.breakOver():
            return

        if self.method in ['lazy','lazyc','lazyd']:
            if time.time() - self.lastRefTime >= self.REFPING:
                self.resetRef()
                logger.info('New reference based on PING')

            ### Possible move: make sure
            if self.wormOutsideBoundary('point'):
                ## Check previous location of worm
                if not self.wormRidiculousLocation():
                    logger.warning('MOVE!!!')
                    self.justMoved = True
                    self.resetRef()
                    self.breakStart = time.time()
                    try:
                        self.servos.centerWorm(100, self.wormLocation.col, self.wormLocation.row)
                    except:
                        logger.warning('GRR')
                else:
                    logger.warning('Impossible location: too far from previous')
        logger.info('processing: %0.6f' % (time.time() - t))
        return

                                                 
    def breakOver( self ):
        currentTime = time.time()
        if currentTime - self.breakStart > self.breakDuration:
            return True
        else:
            return False

    def wormRidiculousLocation( self ):
        farRow = abs ( self.wormLocationPrevious.row - self.wormLocation.row ) > self.MAXONEFRAME
        farCol = abs ( self.wormLocationPrevious.col - self.wormLocation.col ) > self.MAXONEFRAME
        #logger.warning('farRow: %r\tfarCol:%r' % (farRow, farCol))
        return farRow or farCol
    
    def wormOutsideBoundary ( self, method ):
        if method == 'point':
            rowLeft = self.wormLocation.row < self.decisionBoundary.left
            rowRight = self.wormLocation.row > self.decisionBoundary.right
            colTop = self.wormLocation.col < self.decisionBoundary.top
            colBottom =  self.wormLocation.col > self.decisionBoundary.bottom
        
        else: 
            rowLeft = self.cropRegion.left < self.decisionBoundary.left
            rowRight = self.cropRegion.right > self.decisionBoundary.right
            colTop = self.cropRegion.bottom < self.decisionBoundary.top
            colBottom = self.cropRegion.top > self.decisionBoundary.bottom
        
        return (rowLeft or rowRight) or (colTop or colBottom)


    """
    DEBUGGING
    """

    '''
    Debugging Points
    '''
    def drawDebugCropped( self, img ):
        if self.color: 
            self.wormLocation.draw( img, RED)
            self.decisionBoundary.draw( img, RED )
            if self.croppedSearchSpace():
                self.cropRegion.draw(img, BLACK)
        else:
            self.wormLocation.draw( img, BLACK)
            self.decisionBoundary.draw( img, BLACK )
            if self.croppedSearchSpace():
                self.cropRegion.draw(img, BLACK)

    def drawTextStatus( self, img, recording, motors ):
        cv2.putText(img,  "recording: %r || motors: %r || croppedSearchSpace: %r || outside: %r" % (recording, motors, self.croppedSearchSpace(), self.wormOutsideBoundary('point')), (30,30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK)
        

    '''
    Debugging Methods
    '''
            
    def isDebug( self ):
        return logger.getEffectiveLevel() <= logging.WARNING
    

    def drawTest( self, img ):
        #BRG
        p = utils.Point(200,300)
        if self.color: 
            self.frameCenter.draw( img, BLUE )
            p.draw( img, RED)

        else:
            self.frameCenter.draw( img, BLACK )
            p.draw( img, RED)
   
