import sys
import numpy as np
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
                     'capRows','capCols' ]:
                self.__setattr__(k, kwargs[k])

        self.start = time.time()
        self.delay = 20
        self.breakT = 3
        self.breakStart = time.time()
        self.justMoved = False
        self.setupCropping()
        self.setupFindingStructures()
        
        logger.debug('Debug level: %s' % logger.getEffectiveLevel() )
        logger.debug('is Debug?: %s' % str(self.isDebug()))

        if not self.isDebug() and self.method != 'test' :
            self.servos = easyEBB()#(self.capCols, self.capRows), (5,5), 5)

    """ 
    FIND WORMS
    """

    def findWormLazyCropped ( self ):
        t = time.time()

        if self.hasReference():

            self._sub = self._img - self._ref
            
#            if time.time() - self.start > self.delay:
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
            self._sub = self._img - self._ref

            #Gaussian blur
            self._sub  = cv2.GaussianBlur( self._sub, 
                                           (self.gsize, self.gsize) , self.gsig )

            #only process ref image first time 'round
            if not self.hasReferenceLocation: 
                r, c = np.nonzero ( self._sub == np.max( self._sub ) )
                self._colRef, self._rowRef = c[0], r[0]
                logger.debug( 'Reference: col:%d\t\trow:%d' % 
                          ( self._colRef , self._rowRef ))
            
            r, c = np.nonzero ( self._sub == np.min( self._sub ) ) #worm location
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

            r, c = np.nonzero ( self._sub == np.min( self._sub ) ) #worm location

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
                        blue)
        utils.drawPoint(img, 
                        int(self._colRefCenter - self._meanColDistances),
                        int( self._rowRefCenter - self._meanRowDistances), 
                        green)
        utils.drawRect(img, 
                       (int(self.cmin), int(self.rmin)), 
                       (int(self.cmax),int( self.rmax)), 
                       green)
        utils.drawRect(img, 
                       (int(self._colRefCenter - self.limCol), int(self._rowRefCenter - self.limRow)),
                       (int(self._colRefCenter +  self.limCol), int(self._rowRefCenter + self.limRow)),
                        red)

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


    def drawDebug( self, img ):
        #BRG
        utils.drawPoint(img, int(self._colRefCenter), int(self._rowRefCenter), BLACK)
        utils.drawPoint(img, 200, 300, WHITE)
   

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
        return


    def processFrame ( self, img ):
        #logger.debug('enter process frame')
        options = {
            'test' : self.wormTest,
            'lazy' : self.findWormLazy,
            'lazyc': self.findWormLazyCropped,
            'lazyd': self.findWormLazyCroppedDemo,
            'full' : self.findWormFull, #segmentation
            'pca'  : self.findWormPCA, 
            'box'  : self.findWormBox
            }
        t = time.time()

        if self.method == 'test' :
            self._img = img #self.rgb2grayV( img )
            self._sub = self._img

        if self.method == 'lazy' or self.method == 'lazyc'or self.method == 'lazyd':
            #logger.debug('Confirm lazy')
            if not self.hasReference(): #is this OK???
                #logger.debug('Retrieve New Reference')
                self._ref = img # self.rgb2grayV( img ) ###USE OPENCV RGB2GRAY
                self._sub = np.zeros(self._ref.shape) ##For display
                self.lastRefTime = time.time()

            else:
                self._img = img # self.rgb2grayV( img )           
                try:
                    options[self.method]()
                except KeyError:
                    self.findWormLazy() #default
        #logger.info('%0.4f s\tTotal: process frame' %( time.time() - t))
        return self._sub ## gets displayed in the window
    




    def decideMove ( self ):
        t = time.time()
        if not ( t - self.start >= self.delay ):
            return

        if self.justMoved:
            logger.warning('you just moved, try again later')
            return

        if time.time() - self.breakStart <= self.breakT:
            logger.warning("you're still on break")
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
