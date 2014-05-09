import cv2
import logging

l = logging.getLogger('utils')

def drawPoint( img, (col, row), color ):
    if col is None or row is None:
        return
    cv2.circle( img, (col, row), 3 , color, -1 )

def drawRect(img, (topleft, bottomright), color):
    if topleft is None or bottomright is None:
        return
    cv2.rectangle( img, topleft, bottomright, color)

