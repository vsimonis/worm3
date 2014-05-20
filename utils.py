import cv2
import logging

l = logging.getLogger('utils')

class Rect ( object ):
    def __init__( self, ncols, nrows ):
        self.ncols = ncols
        self.nrows = nrows
        self.rectSize = (ncols, nrows)

    def update ( self, ncols, nrows)
        self.ncols = ncols
        self.nrows = nrows
        self.rectSize = (ncols, nrows):

    def gimme (self):
        return (ncols, nrows)
    @property 
    def ncols (self) :
        return ncols

    @property
    def nrows (self):
        return nrows

def drawRect(img, (topleft, bottomright), color):
    if topleft is None or bottomright is None:
        return
    cv2.rectangle( img, topleft, bottomright, color)






class Point ( object ):
    def __init__( self, col, row):
        self.col = col
        self.row = row

    def update ( self, col, row):
        self.col = col
        self.row = row
        
    def gimme ( self ):
        return (col, row)

    def __str__( self ):
        return 'col: %d\trow: %d' % ( self.col, self.row)
    @property
    def row(self):
        return row
    
    @property
    def col(self):
        return col

    def draw ( self, img, color ):
        if col is None or row is None:
            return
        cv2.circle( img, (self.col, self.row), 3 , color, -1 )

