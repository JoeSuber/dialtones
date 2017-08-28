import numpy as np
import cv2
import os

"""
numpy and install help:
(basically just make sure to use all 32 or 64 bit versions for everything on windows)
https://www.solarianprogrammer.com/2016/09/17/install-opencv-3-with-python-3-on-windows/
http://www.lfd.uci.edu/~gohlke/pythonlibs/
"""

print(cv2.__version__)
print(np.__version__)

path = os.path.join(os.getcwd(), "pics", '76aa16c9_homescreen.png')
image = cv2.imread(path)
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.imshow("Over the Clouds", image)
cv2.imshow("Over the Clouds - gray", gray_image)
cv2.waitKey(0)
cv2.destroyAllWindows()


