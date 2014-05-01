import cv2 
import numpy as np
import pandas as pd

import sys

def data_demo(cap, vid):
    window_nm = 'blah'
    frame_num = 0
    need_to_save = False
    surf = cv2.SURF(300)
    data = None
    colNm = ['hI','fname','vI','Label']
    labels = pd.io.parsers.read_csv('annotationH299.csv')

    labdict = {'sinus' : 0,
               'shallow': 1,
               'omega': 2, 
               'alpha' : 3,
               'coil' : 4 }
    while 1:

        ret, frame = cap.read()
        if not ret:
            break

        gray = frame# cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        kp, desc = surf.detectAndCompute(gray, None)

        dh, dw = desc.shape

        kpdata = []
        for k in kp:
            temp = (k.pt[0], k.pt[1], k.size, k.angle, k.response, k.octave, k.class_id)
            kpdata.append(temp)

        fn = np.zeros(dh)
        fn[:] = frame_num
        l = np.zeros(dh)
        l[:] =  labdict [ labels.Label[frame_num] ]
        desc = np.c_[desc, fn, l, kpdata]

        if data is None:
            data = np.array(desc)
        else:
            data = np.vstack((data, desc))
        
        drawn =  cv2.drawKeypoints(gray, kp, flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        vid.write(drawn)
        cv2.imshow(window_nm, drawn)
        key = cv2.waitKey(30)
        c = chr(key & 255)
        if c in ['q', 'Q', chr(27)]:
            break
        frame_num += 1
    
    data = pd.DataFrame(data)
    #data['label'] = labels.Label    
    data.to_csv('surf-h299-next.csv')
    cap.release()
    vid.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    #print __doc__

    cap = cv2.VideoCapture(1)#'H299.avi')

    vid = cv2.VideoWriter('H299-surf.avi', 
                          cv2.cv.CV_FOURCC('M','J','P','G'), 
                          2.0, 
                          (1024, 768), 
                          True)
    data_demo(cap, vid)
