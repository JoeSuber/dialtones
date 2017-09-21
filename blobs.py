import cv2
import numpy as np
import os
from ocyou import whatsay

picsdir = os.path.join(os.getcwd(), "pics")


class Keeper(object):
    def __init__(self, contour):
        self.contour = contour
        self.x1, self.y1, self.width, self.height = cv2.boundingRect(contour)
        self.x2, self.y2 = self.x1 + self.width, self.y1 + self.height
        self.center_x, self.center_y = self.x1 + int(self.width/2), self.y1 + int(self.height/2)
        self.text = None

    def engulfs(self, x, y):
        return True if ((self.y1 < y < self.y2) and (self.x1 < x < self.x2)) else False


def scry(img_path):
    """ return the coordinates associated with a list of text-words found at each unique spot in an image """
    img = cv2.imread(pic, cv2.IMREAD_GRAYSCALE)
    patch_path = os.path.join(picsdir, "patch.png")
    contour_min_size = int(img.size * 0.0005)
    contour_max_size = int(img.size * 0.1)
    y, x = img.shape
    contour_min_x = int(x * 0.027)      # 20 pixels on a 720-x
    contour_min_y = int(y * 0.0109375)  # 14 pixels on a 1280-y

    # convolute and re-sharpen the image to make blobs from text-like things
    blurry = cv2.blur(img, (15, 3))
    thresh = cv2.adaptiveThreshold(blurry, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    reblur = cv2.blur(thresh, (11, 1))
    rethresh = cv2.adaptiveThreshold(reblur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # find contours
    im2, contours, hierarchy = cv2.findContours(rethresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # convex-ify and sort from biggest to smallest
    contours = sorted([cv2.convexHull(c) for c in contours], key=cv2.contourArea, reverse=True)

    # filter out too big/small and sort them by size
    keepers = []
    for cnt in filter(lambda x: contour_min_size < cv2.contourArea(x) < contour_max_size, contours):
        prospect = Keeper(cnt)
        if ((contour_min_x > prospect.width) or
            (prospect.height > prospect.width) or
            (contour_min_y > prospect.height)) or \
            ((prospect.width / prospect.height) > 35):
            continue
        if any([kept.engulfs(prospect.center_x, prospect.center_y) for kept in keepers]):
            continue
        keepers.append(prospect)

    # use tesseract to text-ify the interesting image patches
    for kept in keepers:
        cv2.imwrite(patch_path, img[kept.y1:kept.y2, kept.x1:kept.x2])
        kept.text = whatsay(patch_path)

    return keepers


if __name__ == "__main__":
    """ Show what scry() can do """
    pic1 = os.path.join(picsdir, "43e1cef8_samsung_Boost-Mobile_notificationtray.png")
    pic2 = os.path.join(picsdir, "43e6ce66_samsung_Sprint-PCS_homefront.png")
    pic3 = os.path.join(picsdir, "RNDIS_samsung_Sprint-Prepaid_playstore.png")
    pic4 = os.path.join(picsdir, "43e6ce04_samsung_tsp_apptray-2.png")
    pic5 = os.path.join(picsdir, "76aa16c9_samsung_Sprint-PCS_apptray-0.png")
    pics = [pic1, pic2, pic3, pic4, pic5]
    print("{} pictures in que".format(len(pics)))
    for pic in pics:
        print("looking at: {}".format(pic))

        keepers = scry(pic)

        img = cv2.imread(pic)
        out_img = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)

        for n, kept in enumerate(keepers):
            if kept.text:
                display_patch = img[kept.y1:kept.y2, kept.x1:kept.x2]
                cv2.imshow("{}".format(" ".join(kept.text)), display_patch)
            cv2.circle(out_img, (kept.center_x, kept.center_y), 5, (0,0,255), 3)
            cv2.rectangle(out_img, (kept.x1, kept.y1), (kept.x2, kept.y2), (0,255,0), thickness=2)

        cv2.imshow("contours", out_img)
        ch = cv2.waitKey(0)
        if ch == 27:
            cv2.destroyAllWindows()
            break
        cv2.destroyAllWindows()
