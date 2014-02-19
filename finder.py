import numpy as np

class WormFinder ( object ):
    def __init__( self, method ):

        self._method = method #lazy, etc...

        self._ref = None
        
        
        self._colRef = None
        self._rowRef = None
        self._colWorm = None
        self._rowWorm = None

        self._colDistances = []
        self._rowDistances = []

        self._meanColDistances = 0
        self._meanRowDistances = 0


        self._window = 10
        self._boundRow = 400
        self._boundCol = 400

    @property
    def hasReference ( self ):
        return self._ref is not None

    @property
    def hasReferenceLocation ( self ):
        return self._colRef is not None

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
        if self.hasReference:
            sub = self._img - self._ref

            if not self.hasReferenceLocation: #only process ref image first time 'round
                self._colRef, self._rowRef = np.nonzero ( sub == np.min( sub ) )

            self._colWorm, self._rowWorm = np.nonzero ( sub == np.max( sub ) ) #worm location
            print 'Worm row: %d\t\tcol: %d' % ( self._rowWorm[0] , self._colWorm[0] ) 

            self._colDistances.append(self._colRef[0] - self._colWorm[0])
            self._rowDistances.append(self._rowRef[0] - self._rowWorm[0])

            if ( self.lenDistanceArray > self._window ):
                self._colDistances = self._colDistances[1:] #pop
                self._rowDistances = self._rowDistances[1:] #pop


            self._meanColDistances = np.mean(self._colDistances)
            self._meanRowDistances = np.mean(self._rowDistances)

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


        if not self.hasReference: #is this OK???
            self._ref = self.rgb2grayV( img )
        else:
            self._img = self.rgb2grayV( img )
            try:
                options[self._method]()
            except KeyError:
                self.findWormLazy() #default


    def decideMove ( self ):
        if abs(self._meanColDistances) > self._boundCol or abs(self._meanRowDistances) > self._boundRow :
            print 'MOVE!'

        return

