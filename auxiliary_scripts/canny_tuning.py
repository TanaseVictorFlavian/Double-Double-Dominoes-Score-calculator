import cv2 as cv
import numpy as np
import sys  

def find_canny_params(img):

    img=cv.resize(img,(0,0),fx=0.25,fy=0.25)
    
    def nothing(x):
        pass
    cv.namedWindow("Trackbar") 
    cv.createTrackbar("lower_bound", "Trackbar", 0, 1000, nothing)
    cv.createTrackbar("upper_bound", "Trackbar", 0, 1000, nothing)
    
    while True:

        lb = cv.getTrackbarPos("lower_bound", "Trackbar")
        ub = cv.getTrackbarPos("upper_bound", "Trackbar")


        res = cv.Canny(img, lb, ub)
        cv.imshow("res", res)

        if cv.waitKey(25) & 0xFF == ord('q'):
                break
    cv.destroyAllWindows()

img_path = sys.argv[1]
img = cv.imread(img_path)
find_canny_params(img)