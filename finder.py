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
        

        ### Timing ###
        self.start = time.time()
        self.delay = 4
        self.breakT = 3
        self.breakStart = time.time()
        self.justMoved = False
        self.lastRefTime = time.time()        

        self.launch = 0
        self.launchMAX = 20


        ### Worm Finding
        ## points
        self.wormLocation = Point(-1 , -1 ) 
        self.wormLocationPrevious = Point( -1, -1)
        ## images 
        self.refImg = None
        self.subImg = None
        self.croppedImg = None

        self._colDistances = []
        self._rowDistances = []

        
        ### Cropping ###

        self.cmin = 0
        self.cmax = self.captureSize['col']
        self.rmin = 0
        self.rmax = self.captureSize['row']
 

        ### Logging ###
        logger.debug('Debug level: %s' % logger.getEffectiveLevel() )
        logger.debug('is Debug?: %s' % str(self.isDebug()))

        if not self.isDebug() and self.method != 'conf' :
            self.servos = easyEBB()#(self.capCols, self.capRows), (5,5), 5)
            time.sleep(2)

#@property
    def hasReference ( self ):
        return self.ref is not None

#    @property
#    def hasReferenceLocation ( self ):
#        return self._colRef  >= 0

    @property
    def lenDistanceArray ( self ):
        return len(self._colDistances)

    @property
    def isColor ( self ):
        return self.color

    def resetRef( self ):
        self.launch = 0
        self.ref = None
    


    """ 
    FIND WORMS
    """

    def lazy (self ):
        self.findWormLazy(self.getWormPoint())
    
    def lazyDemo (self):
        self.findWorm(self.getCenterPoint())

    def findWorm ( self, cropPoint ):
        t = time.time()
    
        if self.hasReference():
            # Subtract images 
            self.sub = cv2.subtract(self._ref, self._img)

            # If timing is right, crop!
            if self.launch > self.launchMAX:
                self.sub = self.crop(cropPoint)

            # Gaussian Blur
            self.sub  = cv2.GaussianBlur( self.sub, 
                                           (self.gsize, self.gsize) , self.gsig )
            # Worm Location
            r, c = np.nonzero ( self._sub == np.max( self._sub ) )
            self.wormLocation.update( c[0] += self.cmin, r[0] += self.rmin)
            self.wormLocationPrevious.update( self.wormLocation.gimme() )
            
            self.justMoved = False
            
            self.launch += 1

            ### Distance from center
            self._colDistances.append(self._colRefCenter - self.wormLocation.col)
            self._rowDistances.append(self._rowRefCenter - self.wormLocation.row)

            if ( self.lenDistanceArray > self.window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))
            #logger.info('%0.4f s\tfind worm Lazy Cropped runtime' % (time.time() - t) )
        else:
            return

    def crop ( self, p, img ):
        rpad = (self.captureSize['row'] - self.cropRegion['row']) // 2 
        cpad = (self.captureSize['col'] - self.cropRegion['col']) // 2
        extra = 50
        
       # extra is padding around edge
        '''
        cmin, rmin .---------. cmax, rmin
                   |         | 
                   |    p    |
                   |         |
        cmin, rmax .---------. cmax, rmax
        '''
        pcol = p[0]
        prow = p[1]

        ### COLUMNS
        if pcol - self.cropRegion['col'] / 2 - extra > 0:
            self.cmin = pcol - self.cropRegion['col'] / 2 - extra
        else:
            self.cmin = extra
        if pcol + self.cropRegion['col'] / 2 + extra < self.captureSize['col']:
            self.cmax = pcol + self.captureSize['col'] / 2 + extra
        else:
            self.cmax = self.captureSize['col'] - extra
            
        ### ROWS
        if prow - self.cropRegion['row'] / 2 - extra > 0:
            self.rmin = prow - self.cropRegion['row'] / 2 - extra
        else:
            self.rmin = extra
        if prow + self.cropRegion['row'] / 2 + extra < self.captureSize['row']:
            self.rmax = prow + self.captureSize['row'] / 2 + extra
        else:
            self.rmax = self.captureSize['row'] - extra
                
        return 
    """
    DISPATCH
    lazyd -> keep decision boundary restricted to center of the image
    lazy  -> use full image
    
    """

    def processFrame ( self, img ):
        #logger.debug('enter process frame')
        options = {
            'test' : self.wormTest,
            'conf' : self.wormTest,
            'lazy' : self.findWormLazy,
            'lazyc': self.lazy, 
            'lazyd': self.lazyDemo
#            'lazyd': self.findWormLazyCroppedDemo,
#            'full' : self.findWormFull, #segmentation
#            'pca'  : self.findWormPCA, 
#            'box'  : self.findWormBox,
#            'surf' : self.surfImp, 
#            'sift' : self.siftImp,
#            'mser' : self.mserImp
            }
        t = time.time()
        
        ### LAZYS ###
        if self.method == 'lazy' or self.method == 'lazyc' or self.method == 'lazyd':
            if not self.hasReference(): #is this OK???
                if self.isColor:
                    self._ref = cv2.cvtColor(img, cv2.cv.CV_RGB2GRAY)
                else:
                    self._ref = img
                self._sub = np.zeros(self._ref.shape) ##For display
                self.lastRefTime = time.time()
            else:
                if self.isColor:
                    self._img = cv2.cvtColor(img, cv2.cv.CV_RGB2GRAY)
                else:
                    self._img = img
                try:
                    options[self.method]()
                except KeyError:
                    self.lazy() #default

        ### Non-lazies
        else:
            if self.isColor:
                self._img = cv2.cvtColor(img, cv2.cv.CV_RGB2GRAY)
            else:
                self._img = img
            try:
                options[self.method]()
            except KeyError:
                self.findWormLazy() #default

        return self._sub ## gets displayed in the window
    

    def decideMove ( self ):
        t = time.time()
        if not ( t - self.start >= self.delay ):
            return

        if self.justMoved:
            logger.info('you just moved, try again later')
            return

        if time.time() - self.breakStart <= self.breakT:
           # logger.warning("you're still on break")
            return

        if self.method == 'lazy' or self.method == 'lazyc' or self.method == 'lazyd':
            if time.time() - self.lastRefTime >= self.REFPING:
                self.resetRef()
                logger.info('New reference based on PING')

            if self._colRef < 0 and self.method =='lazy':
                return 
            
            if not self.hasReference and self.method == 'lazyc':
                logger.warning('Not this this sucker, you just moved')

            ### Possible move: make sure

            if self.method == 'lazyc':
                self.limCol = self.lgBoundaryCols
                self.limRow = self.lgBoundaryRows


            elif ( abs(self._meanColDistances) > self.decisionBoundary['col'] or abs(self._meanRowDistances) > self.decisionBoundary['row'] ):
                ## Check previous location of worm
                if abs ( self.wormLocationPrevious['row'] - self.wormLocation['row' ) > self.MAXONEFRAME or
                         abs( self.wormLocationPrevious['col' - self.wormLocation['col'] ) > self.MAXONEFRAME:
                    logger.info('Impossible location: too far from previous')

                    self._colDistances = []
                    self._rowDistances = []
                    return
                else:
                    logger.info('MOVE!!!')
                    try:
                        self.servos.centerWorm(100, self.wormLocation['col'], self.wormLocation['row'])
                    except:
                        logger.warning('GRR')
                    self.justMoved = True
                    self.breakStart = time.time()
                    self.resetRef()

    """
    DEBUGGING
    """

    '''
    Debugging Points
    '''
    def getWormPoint ( self ):
        return (int(self._colWorm), int (self._rowWorm))
    
    def getRefPoint ( self ):
        return (int(self._colRef), int(self._rowRef))

    def getThisPoint ( self ):
       return (int(self._colRef - self._meanColDistances),int( self._rowRef - self._meanRowDistances))

    def getDecisionRect ( self ) : 
        #(topleft, bottomright)
        return ( (int(self._colRefCenter - self.limCol), int(self._rowRefCenter - self.limRow)),
                (int(self._colRefCenter +  self.limCol), int(self._rowRefCenter + self.limRow)) )

    def getCropRect ( self ):
        return ((int(self.cmin), int(self.rmin)), 
                (int(self.cmax),int( self.rmax)))
                      
    def getCenterPoint ( self ) :
        return (int(self._colRefCenter), (self._rowRefCenter))
    
    def getMeanWormPoint (self) :
        return (int(self._colRefCenter - self._meanColDistances),
                int( self._rowRefCenter - self._meanRowDistances))
        
    def drawDebugCropped( self, img ):
        if self.color: 
            utils.drawPoint(img, self.getWormPoint(), RED)
            #utils.drawPoint(img, self.getCenterPoint(), BLUE)
            #utils.drawPoint(img, self.getThisPoint(), BLUE)
            #utils.drawPoint(img, self.getMeanWormPoint(), GREEN)
            utils.drawRect(img, self.getCropRect(), BLACK)
            utils.drawRect(img, self.getDecisionRect(), RED)

        else: 
            utils.drawPoint(img, self.getWormPoint(), WHITE)
            #utils.drawPoint(img, self.getCenterPoint(), BLUE)
            #utils.drawPoint(img, self.getThisPoint(), WHITE)
            utils.drawRect(img, self.getDecisionRect(), BLACK)

        if self.launch >= self.launchMAX:
            utils.drawRect(img, self.getCropRect(), BLACK)


    def drawDebuggingPoint( self, img ):
        utils.drawPoint(img, self.getWormPoint(), RED)
        utils.drawPoint(img, self.getRefPoint(), BLUE)
        utils.drawPoint(img, self.getMeanWormPoint() , GREEN)
    

    
    def drawTextStatus( self, img, recording, motors ):
        cv2.putText(img,  "recording: %r || motors: %r || launch: %d" % (recording, motors, self.launch), (30,30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLACK)
        

    '''
    Debugging Methods
    '''
            
    def isDebug( self ):
        return logger.getEffectiveLevel() <= logging.INFO
    

    def drawTest( self, img ):
        #BRG
        if self.color: 
            utils.drawPoint(img, self.getCenterPoint(), BLUE)
            utils.drawPoint(img, 200, 300, RED)

        else:
            utils.drawPoint(img, self.getWormPoint(), BLACK)
            utils.drawPoint(img, 200, 300, BLACK)
   
