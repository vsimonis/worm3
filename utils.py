import cv2
import logging

l = logging.getLogger('utils')

class Rect ( object ):
    def __init__( self, ncols, nrows, center):
        self.incols = ncols
        self.inrows = nrows
        self.topleft = Point(center.col - (self.incols / 2), center.row - (self.inrows / 2)) #center is a point
        self.bottomright = Point(center.col + (self.incols / 2), center.row + (self.inrows / 2)) #center is a point
        self.rectSize = (ncols, nrows)
        self.center = center

    def update ( self, center):
        self.topleft.update(center.col - (self.incols / 2), center.row - (self.inrows / 2)) #center is a point
        self.bottomright.update(center.col + (self.incols / 2), center.row + (self.inrows / 2))
        self.center = center
        ##print self.center

    @property
    def right ( self ):
        return self.bottomright.col

    @property
    def left ( self ):
        return self.topleft.col

    @property
    def top ( self ): 
        return self.topleft.row

    @property
    def bottom ( self ): 
        return self.bottomright.row

    @property  
    def ncols (self) :
        return self.incols

    @property
    def nrows (self):
        return self.inrows

    def draw(self, img, color):
        if self.topleft is None or self.bottomright is None:
            return
        cv2.rectangle( img, self.topleft.gimme(), self.bottomright.gimme(), color)


class Point ( object ):
    def __init__( self, col, row):
        self.icol = col
        self.irow = row
    
    def add (self, toAddCol,toAddRow):
        outcol = self.icol + toAddCol
        outrow = self.irow + toAddRow
        newPoint = Point(outcol, outrow)
       
        return newPoint

    def update ( self, col, row):
        self.icol = col
        self.irow = row
        
    def gimme ( self ):
        return (int(self.icol), int(self.irow))

    def __str__( self ):
        return 'col: %d\trow: %d' % ( self.icol, self.irow)
    @property
    def row(self):
        return self.irow
    
    @property
    def col(self):
        return self.icol

    def draw ( self, img, color ):
        if self.icol is None or self.irow is None:
            return
        cv2.circle( img, (int(self.icol), int(self.irow)), 3 , color, -1 )

