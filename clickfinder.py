from lizardhide import *
import cv2
import numpy as np


def draw_circle(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print("start x= {},  start y= {}".format(x, y))
        cv2.circle(img, (x, y), 20, (0, 255, 0), -1)
    if event == cv2.EVENT_LBUTTONUP:
        print("end x= {}, end  y= {}".format(x, y))
        cv2.circle(img, (x, y), 20, (0, 0, 255), -1)


if __name__ == "__main__":
    fullsize = cv2.imread("C:\\Users\\2053_HSUF\\PycharmProjects\\dialtones\\pics\\43d2ce46_samsung_Sprint-Prepaid_lockscreen.png")

    img = cv2.resize(fullsize, (640,1080))
    cv2.namedWindow('image')
    cv2.setMouseCallback('image', draw_circle)
    while (1):
        cv2.imshow('image', img)
        if cv2.waitKey(20) & 0xFF == 27:
            break
    cv2.destroyAllWindows()
