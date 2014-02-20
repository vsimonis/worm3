import cv2

def drawPoint( img, col, row, color ):
    if col is None or row is None:
        return
    cv2.circle( img, (row, col), 3 , color, -1 )
