import cv2 as cv
import numpy as np
import sys

# crop the image
# function gives the cooridantes of the pixel being clicked on 
# the function was used to determine the corner pixels coordinates
# of the patch of interest

pixel_positions = []


def mouse_click(event, x, y, flags, param):
    if event == cv.EVENT_LBUTTONDOWN:
        print("Pixel position (x, y):", x / 0.25, y / 0.25)
        pixel_positions.append((np.uint64(x / 0.25), np.uint64(y / 0.25)))

img_path = sys.argv[1]
img = cv.imread(img_path)
img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
img_copy = cv.imread(img_path)
img_copy = cv.resize(img_copy, (0, 0), fx=0.25, fy=0.25)

# Create a window and set the callback function for mouse events
cv.namedWindow('Image')
cv.setMouseCallback('Image', mouse_click)

while True:
    cv.imshow('Image', img_copy)
    if cv.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
        upper_left, upper_right, bottom_left, bottom_right = pixel_positions
        pixel_positions.clear()
        break

cv.destroyAllWindows()