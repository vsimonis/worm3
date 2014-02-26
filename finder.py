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
                     'boundBoxRow', 'boundBoxCol',
                     'limRow', 'limCol',
                     'MAXONEFRAME', 'REFPING', 'MAXREF', 
                     'capRows','capCols' ]:
                self.__setattr__(k, kwargs[k])

        self.start = time.time()
        self.delay = 1
                
        ### 'lazy' Parameters
        self._ref = None
        self._sub = None
        self.lastRefTime = time.time()
 
        ##Cropping Parameters
        self.rpad = (self.capRows - self.boundBoxRow) // 2 
        self.cpad = (self.capCols - self.boundBoxCol) // 2

        self.extra = 50
        
        self.cmin = 0
        self.cmax = self.capCols
        self.rmin = 0
        self.rmax = self.capRows
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
        
        logger.debug('Debug level: %s' % logger.getEffectiveLevel() )
        logger.debug('is Debug?: %s' % str(self.isDebug()))

        if not self.isDebug():
            self.servos = easyEBB((self.actualCols, self.actualRows), (5,5), 5)

    def drawDebuggingPointCroppedDemo( self, img ):
        #BRG
        green = [0, 255, 0]
        red = [0, 0, 255]
        blue = [255, 0, 0]
        utils.drawPoint(img, int(self._colWorm), int(self._rowWorm), red)
        utils.drawPoint(img, int(self._colRef), int(self._rowRef), blue)
        utils.drawPoint(img, 320, 240, green)
       # utils.drawPoint(img, int(self._rowRef - self._meanRowDistances),int( self._colRef - self._meanColDistances), green)
        utils.drawRect(img, (int(self.cmin), int(self.rmin)), 
                       (int(self.cmax),int( self.rmax)), green)



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
                logger.debug( 'Reference: col:%d\t\trow:%d' % 
                         ( self._colRef , self._rowRef ))

            # CROPPPPPPPPP
            # needs to be centered around worm for demo
            if time.time() - self.start > self.delay:
                lc, lr = self._sub.shape

                if self._colRef - self.boundBoxCol/2 - self.extra > 0:
                    self.cmin = self._colRef - self.boundBoxCol/2 - self.extra
                else:
                    self.cmin = self.extra
                if self._colRef + self.boundBoxCol/2 + self.extra < self.capCols:
                    self.cmax = self._colRef + self.boundBoxCol/2 + self.extra
                else:
                    self.cmax = self.capCols - self.extra
                if self._rowRef - self.boundBoxRow/2 - self.extra > 0:
                    self.rmin = self._rowRef - self.boundBoxRow/2 - self.extra
                else:
                    self.rmin = self.extra
                if self._rowRef + self.boundBoxRow/2 + self.extra < self.capRows:
                    self.rmax = self._rowRef + self.boundBoxRow/2 + self.extra
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

            logger.debug('means col %d\trow %d' % (
                    self._meanColDistances, self._meanRowDistances))
            #logger.info('runtime: %0.3f' % (time.time() - t) )
        else:
            return


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
                r, c = np.nonzero ( self._sub == np.min( self._sub ) )
                self._colRef, self._rowRef = c[0], r[0]
                logger.debug( 'Reference: col:%d\t\trow:%d' % 
                          ( self._colRef , self._rowRef ))
            
            r, c = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location
            self._colWormPrev, self._rowWormPrev = self._colWorm, self._rowWorm
            self._colWorm, self._rowWorm = c[0], r[0]
            logger.debug( 'Worm: col:%d\t\trow:%d' % 
                          ( self._colWorm , self._rowWorm ))

            self._colDistances.append(self._colRef - self._colWorm)
            self._rowDistances.append(self._rowRef - self._rowWorm)

            if ( self.lenDistanceArray > self.window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))
        logger.info('runtime: %0.3f' % (time.time() - t) )


    def findWormLazyCropped ( self ):
        t = time.time()
        if self.hasReference():
            
            self._sub = self._img - self._ref

            # CROPPPPPPPPP
            lc, lr = self._sub.shape

            self.cmin = self.cpad
            self.cmax = self.cpad + self.boundBoxCol
            self.rmin = self.rpad
            self.rmax = self.rpad + self.boundBoxRow

            self._sub = self._sub[rmin:rmax, cmin:cmax]

            lc, lr = self._sub.shape
            
            # Gaussian Blur
            t1 = time.time()
            self._sub  = cv2.GaussianBlur( self._sub, 
                                           (self.gsize, self.gsize) , self.gsig )
            logger.debug('Blur time: %0.4f' % (time.time() - t1) )

            
            r, c = np.nonzero ( self._sub == np.max( self._sub ) ) #worm location

            self._colWorm, self._rowWorm = c[0], r[0]
            self._rowWorm += self.rmin
            self._colWorm += self.cmin
            self._colWormPrev, self._rowWormPrev = self._colWorm, self._rowWorm
            
            logger.debug( 'Worm: col:%d\t\trow:%d' % 
                          ( self._colWorm , self._rowWorm ))


            ### Distance from center
            self._colDistances.append(self._colRefCenter - self._colWorm)
            self._rowDistances.append(self._rowRefCenter - self._rowWorm)

            if ( self.lenDistanceArray > self.window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = int(np.mean(self._colDistances))
            self._meanRowDistances = int(np.mean(self._rowDistances))
            logger.debug('runtime: %0.3f' % (time.time() - t) )
        else:
            return





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
            'lazyc': self.findWormLazyCropped,
            'lazyd': self.findWormLazyCroppedDemo,
            'full' : self.findWormFull, #segmentation
            'pca'  : self.findWormPCA, 
            'box'  : self.findWormBox
            }

        if self.method == 'lazy' or self.method == 'lazyc'or self.method == 'lazyd':
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
        if self.method == 'lazy' or self.method == 'lazyc' or self.method == 'lazyd':
            if time.time() - self.lastRefTime >= self.REFPING:
                self.resetRef()
                logger.warning('New reference based on PING')

            if self._colRef < 0 and self.method =='lazy':
                return 

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
                    if not self.isDebug:
                        self.servos.centerWorm(60, self._colWorm, self._rowWorm)

                    self.resetRef()
                    self._colWorm = -1
                    self._rowWorm = -1






    '''
    Debugging Points
    '''

    def drawDebuggingPoint( self, img ):

        #BRG
        green = [0, 255, 0]
        red = [0, 0, 255]
        blue = [255, 0, 0]
        utils.drawPoint(img, int(self._colWorm), int(self._rowWorm), red)
        utils.drawPoint(img, int(self._colRef), int(self._rowRef), blue)
        utils.drawPoint(img, int(self._colRef - self._meanColDistances),int( self._rowRef - self._meanRowDistances), green)
       
    def drawDebuggingPointCropped( self, img ):
        #BRG
        green = [0, 255, 0]
        red = [0, 0, 255]
        blue = [255, 0, 0]
        utils.drawPoint(img, int(self._colWorm), int(self._rowWorm), red)
        logger.debug('drawing: col %d\trow:%d' % ( self._colRefCenter, self._rowRefCenter) )
        utils.drawPoint(img, int(self._colRefCenter), int(self._rowRefCenter), blue)
        utils.drawPoint(img, int(self._colRefCenter - self._meanColDistances),int( self._rowRefCenter - self._meanRowDistances), green)


    def drawDebuggingPointGS( self, img ):
        #BRG       
        utils.drawPoint(img, self._colWorm, self._rowWorm, 255)
        utils.drawPoint(img, self._colRef, self._rowRef, 0)
        utils.drawPoint(img, self._colRef - self._meanColDistances, self._rowRef - self._meanRowDistances, 255)

    def isDebug( self ):
        return logger.getEffectiveLevel() <= logging.INFO
    
    def resetRef( self ):
        self._ref = None
        self._colRef = -1
        self._rowRef = -1
        self._colDistances = []
        self._rowDistances = []
        self.cmin = 0
        self.cmax = self.capCols
        self.rmin = 0
        self.rmax = self.capRows
    
    
