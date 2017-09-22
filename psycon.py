import numpy as np
import cv2
import os

"""
Use template matching to find icon location.

numpy and install help:
(basically just make sure to use all 32 or 64 bit versions for everything.
    On windows the default python version is likely 32 bit)
https://www.solarianprogrammer.com/2016/09/17/install-opencv-3-with-python-3-on-windows/
http://www.lfd.uci.edu/~gohlke/pythonlibs/
"""
resolutions = [(320, 480), (480,800), (540,960), (600,1024), (640, 1136), (720,1280), (768,1280), (800,1280),
               (1080, 1920), (1440, 2560), (1440, 2880)]

def iconograph(screen_path, icon_path, icon_source_size=(720, 1280), DEBUG=False):
    """ returns coordinates in an image that best match the given icon """
    image = cv2.imread(screen_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print("INVALID SCREEN PATH: {}".format(screen_path))
    if DEBUG: print("screen size: {}".format(image.shape))
    raw_icon = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)
    best_match = None
    for res in resolutions:
        if res[0] < icon_source_size[0]:
            interpol_method = cv2.INTER_AREA
        else:
            interpol_method = cv2.INTER_CUBIC
        icon = cv2.resize(raw_icon, None, fx=res[0] / float(icon_source_size[0]),
                          fy=res[1] / float(icon_source_size[1]), interpolation=interpol_method)
        if (image.shape[0] < icon.shape[0]) or (image.shape[1] < icon.shape[1]):
            continue
        _, max_val, _, max_loc = cv2.minMaxLoc(cv2.matchTemplate(image, icon, 5))
        if DEBUG: print(max_val, max_loc)
        max_loc = (max_loc[0] + int(icon.shape[1]/2), max_loc[1] + int(icon.shape[0]/2))
        if best_match is None or best_match[0] < max_val:
            best_match = (max_val, max_loc, res)

    if DEBUG:
        cv2.circle(image, best_match[1], 25,(255,255,255), thickness=3)
        cv2.imshow(str(best_match[2]), cv2.resize(image, (640,1080)))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return best_match if DEBUG else best_match[1]


def colors(im=None):
    """ not really related. Just helps with finding details in gray scale images """
    if im is None:
        path = "C:\\Users\\2053_HSUF\\PycharmProjects\\dialtones\\pics\\76aa16c9_playstore.png"
        im = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    for shade in range(13):
        colorized = cv2.applyColorMap(im, shade)
        cv2.imshow("yo", colorized)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    """ for testing one icon against a bunch of screens """

    print(cv2.__version__)
    print(np.__version__)

    iconpaths = [os.path.join(os.getcwd(), "icons", icp)
                for icp in os.listdir(os.path.join(os.getcwd(), "icons")) if icp.endswith(".png")]

    images = [os.path.join(os.getcwd(), "pics", ip)
              for ip in os.listdir(os.path.join(os.getcwd(), "pics")) if ip.endswith(".png")]

    for icp in iconpaths:
        cv2.imshow("Finding:", cv2.imread(icp))
        for impath in images:
            # colors(im=cv2.imread(impath, cv2.IMREAD_GRAYSCALE))
            print(iconograph(impath, icp, DEBUG=True))

