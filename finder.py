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

#gray scale
WHITE = 255
BLACK = 0

nHess = 300       
nFeat = 0
mserMin = 40
mserMax = 600
mserDelta = 6

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
                     'boundBoxRow', 'boundBoxCol',
                     'limRow', 'limCol',
                     'MAXONEFRAME', 'REFPING', 'MAXREF', 
                     'capRows','capCols', 'color']:
                self.__setattr__(k, kwargs[k])

        self.start = time.time()
        self.delay = 4
        self.breakT = 3
        self.breakStart = time.time()
        self.justMoved = False
        self.setupCropping()
        self.setupFindingStructures()

        self.surf = None
        self.sift = None
        self.mser = None
        self.mserFD = None
        
        #self.Desc = None
        self.Desc = None

        logger.debug('Debug level: %s' % logger.getEffectiveLevel() )
        logger.debug('is Debug?: %s' % str(self.isDebug()))

        if not self.isDebug() and self.method != 'test' :
            self.servos = easyEBB()#(self.capCols, self.capRows), (5,5), 5)
            time.sleep(2)
    """ 
    FIND WORMS
    """
    def writeOut( self, name ):
        
        labels = pd.io.parsers.read_csv('annotationH299.csv',header = 0)
        print labels

        arr = np.array( self.Desc)
#        print arr.shape
        data = pd.DataFrame(self.Desc)
        
        data.to_csv("%s.csv" % name, index=False, header = False)

    def surfImp (self):
        if self.surf is None:
            self.surf = cv2.SURF(nHess)
        keypts, desc  = self.surf.detectAndCompute(self._img, None)
#        print desc
        self._sub = cv2.drawKeypoints(self._img, keypts, None, BLUE ,4 )
        if self.Desc is None:
            self.Desc = np.array(desc)
        #np.insert(self.Desc, len(self.Desc) + 1, desc, axis = 0)
        else:
            self.Desc = np.vstack([self.Desc, desc])
 #       print self.Desc

    def siftImp(self):
        if self.sift is None:
            self.sift = cv2.SIFT() #nFeat
        keypts, desc = self.sift.detectAndCompute(self._img, None)
        self._sub = cv2.drawKeypoints(self._img, keypts, flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)#, None, (255,0,0), 4)
        self.Desc.append(desc)

    def mserImp(self):
        vis = self._img.copy()
        if self.mser is None:
            self.mser = cv2.MSER(mserDelta, mserMin, mserMax)
        #if self.mserFD is None:
        #    self.mserFD = cv2.FeatureDetector_create('MSER')
        #kpts = self.mserFD.detect(self._img)
    
        regions = self.mser.detect(self._img, None)
        hulls = [cv2.convexHull(p.reshape(-1,1,2)) for p in regions]
        cv2.polylines(vis, hulls, 1, GREEN)
        self._sub = vis
        #desc = DescriptorExtractor_create(


    def findWormLazyCropped ( self ):
        t = time.time()

        if self.hasReference():

            self._sub = self._img - self._ref
            
            self._sub = cv2.subtract(self._ref, self._img)
#            self._sub = np.asarray(self._img[:,:]) - np.asarray(self._ref[:,:])
#            out = np.zeros(self._sub.shape)
#            out = cv2.normalize(self._sub, out, 0, 255, cv2.NORM_MINMAX)
#            self._sub = out
#            self._sub = cv2.absdiff(self._img, self._ref)
            lc, lr = self._sub.shape
            
            if self._colRefCenter - self.boundBoxCol/2 - self.extra > 0:
                self.cmin = self._colRefCenter - self.boundBoxCol/2 - self.extra
            else:
                self.cmin = self.extra
            if self._colRefCenter + self.boundBoxCol/2 + self.extra < self.capCols:
                self.cmax = self._colRefCenter + self.boundBoxCol/2 + self.extra
            else:
                self.cmax = self.capCols - self.extra
            if self._rowRefCenter - self.boundBoxRow/2 - self.extra > 0:
                self.rmin = self._rowRefCenter - self.boundBoxRow/2 - self.extra
            else:
                self.rmin = self.extra
            if self._rowRefCenter + self.boundBoxRow/2 + self.extra < self.capRows:
                self.rmax = self._rowRefCenter + self.boundBoxRow/2 + self.extra
            else:
                self.rmax = self.capRows - self.extra
                #time to crop!
            self._sub = self._sub[self.rmin : self.rmax, self.cmin : self.cmax]
 

            # Gaussian Blur

            self._sub  = cv2.GaussianBlur( self._sub, 
                                           (self.gsize, self.gsize) , self.gsig )
           # logger.debug('Blur time: %0.4f' % (time.time() - t1) )

            if not self.color:
                r, c = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location

            else:
                r, c = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location
                
            self._colWorm, self._rowWorm = c[0], r[0]
            self._rowWorm += self.rmin
            self._colWorm += self.cmin
            self._colWormPrev, self._rowWormPrev = self._colWorm, self._rowWorm
            
            #logger.debug( 'Worm: col:%d\t\trow:%d' % 
#                          ( self._colWorm , self._rowWorm ))

            self.justMoved = False

            ### Distance from center
            self._colDistances.append(self._colRefCenter - self._colWorm)
            self._rowDistances.append(self._rowRefCenter - self._rowWorm)

            if ( self.lenDistanceArray > self.window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))
            #logger.info('%0.4f s\tfind worm Lazy Cropped runtime' % (time.time() - t) )
        else:
            return




    def findWormLazy ( self ):
        t = time.time()
        if self.hasReference():
#            self._sub = self._img - self._ref
#            self._sub = cv2.absdiff(self._img, self._ref)
            self._sub = cv2.subtract(self._ref, self._img)
            #Gaussian blur
            #self._sub  = cv2.GaussianBlur( self._sub, 
            #                               (self.gsize, self.gsize) , self.gsig )

            #only process ref image first time 'round
            if not self.hasReferenceLocation: 
                r, c  = np.nonzero ( self._sub == np.min( self._sub ) )
                self._colRef, self._rowRef = c[0], r[0]
                logger.debug( 'Reference: col:%d\t\trow:%d' % 
                          ( self._colRef , self._rowRef ))
            
            r, c = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location
            self._colWormPrev, self._rowWormPrev = self._colWorm, self._rowWorm
            self._colWorm, self._rowWorm = c[0], r[0]
            #self._colWorm = self.capCols - self._colWorm
            logger.debug( 'Worm: col:%d\t\trow:%d' % 
                          ( self._colWorm , self._rowWorm ))

            self._colDistances.append(self._colRef - self._colWorm)
            self._rowDistances.append(self._rowRef - self._rowWorm)

            if ( self.lenDistanceArray > self.window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))
#        logger.info('%0.3f s\tFind worm lazy' % (time.time() - t) )



 


    def findWormLazyCroppedDemo( self ):
        t = time.time()
        if self.hasReference():            
            self._sub = self._img - self._ref
            self._sub = cv2.absdiff(self._img, self._ref)
            self._sub = cv2.subtract(self._ref, self._img)
            #only process ref image first time 'round
            if not self.hasReferenceLocation: 
                self._sub  = cv2.GaussianBlur( 
                    self._sub, 
                    (self.gsize, self.gsize),
                    self.gsig)

                r, c = np.nonzero ( self._sub == np.min( self._sub ) )
                self._colRef, self._rowRef = c[0], r[0]


            # CROPPPPPPPPP
            # needs to be centered around worm for demo
            if time.time() - self.start > self.delay:
                lc, lr = self._sub.shape

                if self._colRefCenter - self.boundBoxCol/2 - self.extra > 0:
                    self.cmin = self._colRefCenter - self.boundBoxCol/2 - self.extra
                else:
                    self.cmin = self.extra
                if self._colRefCenter + self.boundBoxCol/2 + self.extra < self.capCols:
                    self.cmax = self._colRefCenter + self.boundBoxCol/2 + self.extra
                else:
                    self.cmax = self.capCols - self.extra
                if self._rowRefCenter - self.boundBoxRow/2 - self.extra > 0:
                    self.rmin = self._rowRefCenter - self.boundBoxRow/2 - self.extra
                else:
                    self.rmin = self.extra
                if self._rowRefCenter + self.boundBoxRow/2 + self.extra < self.capRows:
                    self.rmax = self._rowRefCenter + self.boundBoxRow/2 + self.extra
                else:
                    self.rmax = self.capRows - self.extra
                #time to crop!
                self._sub = self._sub[self.rmin : self.rmax, self.cmin : self.cmax]
            # Gaussian Blur
            self._sub  = cv2.GaussianBlur( self._sub, 
                                           (self.gsize, self.gsize) , self.gsig )

            r, c = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location

            self._colWorm, self._rowWorm = c[0], r[0]
            self._rowWorm += self.rmin
            self._colWorm += self.cmin
            self._colWormPrev, self._rowWormPrev = self._colWorm, self._rowWorm
            
            logger.debug( 'Worm: col:%d\t\trow:%d' % 
                          ( self._colWorm , self._rowWorm ))

            self._colDistances.append(self._colRef - self._colWorm)
            self._rowDistances.append(self._rowRef - self._rowWorm)

            if ( self.lenDistanceArray > self.window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))

           
            logger.debug( 'Refe: col:%d\t\trow:%d' % 
                         ( self._colRef , self._rowRef ))
            logger.debug( 'Worm: col:%d\t\trow:%d' % 
                          ( self._colWorm , self._rowWorm ))
            logger.debug( 'dist: col:%d\t\trow:%d' % 
                          ( self._colRef - self._colWorm , 
                            self._rowRef - self._rowWorm ))

            logger.debug('means col %d\t\trow %d' % (
                    self._meanColDistances, self._meanRowDistances))
           # logger.info('%0.4f s\tFind Worm Cropped Demo' % (time.time() - t) )
        else:
            return

    """
    DEBUGGING
    """

    '''
    Debugging Points
    '''

    def drawDebuggingPoint( self, img ):
        utils.drawPoint(img, int(self._colWorm), int(self._rowWorm), RED)
        utils.drawPoint(img, int(self._colRef), int(self._rowRef), BLUE)
        utils.drawPoint(img, int(self._colRef - self._meanColDistances),int( self._rowRef - self._meanRowDistances), GREEN)
        #utils.drawPoint(img, 200, 300, green)
       # utils.drawPoint(img, 320, 240, red)
    
    def drawDebuggingPointCroppedBW( self, img ):
        utils.drawPoint(img, int(self._colWorm), int(self._rowWorm), BLACK)
        #utils.drawPoint(img, 
        #                int(self._colRefCenter), 
        #                int(self._rowRefCenter), 
        #                blue)
        #utils.drawPoint(img, 
        #                int(self._colRefCenter - self._meanColDistances),
        #                int( self._rowRefCenter - self._meanRowDistances), 
        #                WHITE)
        utils.drawRect(img, 
                       (int(self.cmin), int(self.rmin)), 
                       (int(self.cmax),int( self.rmax)), 
                       BLACK)
        utils.drawRect(img, 
                       (int(self._colRefCenter - self.limCol), int(self._rowRefCenter - self.limRow)),
                       (int(self._colRefCenter +  self.limCol), int(self._rowRefCenter + self.limRow)),
                       BLACK)



    def drawDebuggingPointCropped( self, img ):
        utils.drawPoint(img, int(self._colWorm), int(self._rowWorm), RED)
        utils.drawPoint(img, 
                        int(self._colRefCenter), 
                        int(self._rowRefCenter), 
                        BLUE)
        utils.drawPoint(img, 
                        int(self._colRefCenter - self._meanColDistances),
                        int( self._rowRefCenter - self._meanRowDistances), 
                        GREEN)
        utils.drawRect(img, 
                       (int(self.cmin), int(self.rmin)), 
                       (int(self.cmax),int( self.rmax)), 
                       GREEN)
        utils.drawRect(img, 
                       (int(self._colRefCenter - self.limCol), int(self._rowRefCenter - self.limRow)),
                       (int(self._colRefCenter +  self.limCol), int(self._rowRefCenter + self.limRow)),
                        RED)

    def drawDebuggingPointCroppedDemo( self, img ):
        utils.drawPoint(img, int(self._colWorm), int(self._rowWorm), RED)
        utils.drawPoint(img, int(self._colRef), int(self._rowRef), BLUE)
        utils.drawRect(img, (int(self.cmin), int(self.rmin)), 
                       (int(self.cmax),int( self.rmax)), GREEN)



    def drawDebuggingPointGS( self, img ):
        utils.drawPoint(img, self._colWorm, self._rowWorm, WHITE)
        utils.drawPoint(img, self._colRef, self._rowRef, BLACK)
        utils.drawPoint(img, self._colRef - self._meanColDistances, self._rowRef - self._meanRowDistances, WHITE)

    '''
    Debugging Methods
    '''
            
    def isDebug( self ):
        return logger.getEffectiveLevel() <= logging.DEBUG


    def drawDebugBW( self, img ):
        #BRG
        utils.drawPoint(img, int(self._colRefCenter), int(self._rowRefCenter), BLACK)
        utils.drawPoint(img, 200, 300, WHITE)
   
    def drawDebug( self, img ):
        #BRG
        utils.drawPoint(img, int(self._colRefCenter), int(self._rowRefCenter), BLUE)
        utils.drawPoint(img, 200, 300, RED)
   
    #@property
    def hasReference ( self ):
        return self._ref is not None

    @property
    def hasReferenceLocation ( self ):
        return self._colRef  >= 0

    @property
    def lenDistanceArray ( self ):
        return len(self._colDistances)

    @property
    def isColor (self ):
        return self.color

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


    def wormTest ( self ):
        self._sub = self._img
        return


    def processFrame ( self, img ):
        #logger.debug('enter process frame')
        options = {
            'test' : self.wormTest,
            'conf' : self.wormTest,
            'lazy' : self.findWormLazy,
            'lazyc': self.findWormLazyCropped,
            'lazyd': self.findWormLazyCroppedDemo,
            'full' : self.findWormFull, #segmentation
            'pca'  : self.findWormPCA, 
            'box'  : self.findWormBox,
            'surf' : self.surfImp, 
            'sift' : self.siftImp,
            'mser' : self.mserImp
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
                    self.findWormLazy() #default

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
            logger.warning('you just moved, try again later')
            return

        if time.time() - self.breakStart <= self.breakT:
           # logger.warning("you're still on break")
            return

        if self.method == 'lazy' or self.method == 'lazyc' or self.method == 'lazyd':
            if time.time() - self.lastRefTime >= self.REFPING:
                self.resetRef()
                logger.warning('New reference based on PING')

            if self._colRef < 0 and self.method =='lazy':
                return 
            
            if not self.hasReference and self.method == 'lazyc':
                logger.warning('Not this this sucker, you just moved')

            ### Possible move: make sure

            elif ( abs(self._meanColDistances) > self.limCol or abs(self._meanRowDistances) > self.limRow ):
                ## Check previous location of worm
                if abs ( self._rowWormPrev - self._rowWorm ) > self.MAXONEFRAME or abs( self._colWormPrev - self._colWorm ) > self.MAXONEFRAME:
                    logger.info('Impossible location: too far from previous')
                   # self._rowWorm = self._rowWormPrev
                   # self._colWorm = self._colWormPrev
                    self._colDistances = []
                    self._rowDistances = []
                    return
                ## Check relative position to reference
                #elif ( abs ( self._rowRef - self._rowWorm) > self.MAXREF or abs ( self._colRef - self._colWorm) > self.MAXREF):
                #    logger.info('Impossible location: too far from ref')
                #    return
                else:
                    logger.warning('MOVE!!!')
#                    if not self.isDebug:
                    try:
                        self.servos.centerWorm(100, self._colWorm, self._rowWorm)
                    except:
                        pass
                    self.justMoved = True
                    self.breakStart = time.time()
                    self.resetRef()
                    self._colWorm = -1
                    self._rowWorm = -1
                #logger.info('decide move runtime: %0.3f' % (time.time() - t ))




 

    def resetRef( self ):
        self._ref = None
        self._colRef = -1
        self._rowRef = -1
        self._colDistances = []
        self._rowDistances = []
        #self.cmin = 0
        #self.cmax = self.capCols
        #self.rmin = 0
        #self.rmax = self.capRows
    
    
    def setupCropping( self ):
        
        ##Cropping Parameters
        self.rpad = (self.capRows - self.boundBoxRow) // 2 
        self.cpad = (self.capCols - self.boundBoxCol) // 2

        self.extra = 50
        
        self.cmin = 0
        self.cmax = self.capCols
        self.rmin = 0
        self.rmax = self.capRows


    def setupFindingStructures( self ):
        ## General Parameters
        self._colRef = -1
        self._rowRef = -1

        self._colRefCenter = self.capCols // 2
        self._rowRefCenter = self.capRows // 2

        self._colWorm = -1
        self._rowWorm = -1

        self._colDistances = []
        self._rowDistances = []

        self._meanColDistances = 0
        self._meanRowDistances = 0

        ### 'lazy' Parameters
        self._ref = None
        self._sub = None
        self.lastRefTime = time.time()
