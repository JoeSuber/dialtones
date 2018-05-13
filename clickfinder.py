import cv2
import numpy as np


def draw_circle(event, x, y, flags, param):
    height, width = fullsize.shape[:2]
    smallheight, smallwidth = img.shape[:2]
    ratx = np.round(int(x * width / smallwidth) / float(width), 3)
    raty = np.round(int(y * height / smallheight) / float(height), 3)
    if event == cv2.EVENT_LBUTTONDOWN:
        print("start x, y = {}, {}".format(ratx, raty))
        cv2.circle(img, (x, y), 20, (0, 255, 0), -1)
    if event == cv2.EVENT_LBUTTONUP:
        print("end x, y = {}, {}".format(ratx, raty))
        print("*****")
        cv2.circle(img, (x, y), 20, (0, 0, 255), -1)


def clickfinder(screen_fn):
    global fullsize, img
    fullsize = cv2.imread(screen_fn)
    img = cv2.resize(fullsize, (640,1080))
    cv2.namedWindow(screen_fn)
    cv2.setMouseCallback(screen_fn, draw_circle)
    while (1):
        cv2.imshow(screen_fn, img)
        if cv2.waitKey(20) & 0xFF == 27:
            break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    sample = "C:\\Users\\2053_HSUF\\PycharmProjects\\dialtones\\pics\\43d2ce46_samsung_Sprint-Prepaid_lockscreen.png"
    clickfinder(sample)