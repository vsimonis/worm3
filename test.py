import cv2

name = 'view'
cv2.namedWindow( name, cv2.CV_WINDOW_AUTOSIZE )
img = cv2.imread('screenshot.png')

cv2.circle(img, (100,100), 3, [255, 0,0], -1)
cv2.imshow(name, img)
cv2.waitKey()
