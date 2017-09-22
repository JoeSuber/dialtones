try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract
import os
import cv2
import Levenshtein_search
import re

# Must install: http://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-setup-3.05.01.exe
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'
# Include the above line, if you don't have tesseract executable in your PATH
# Example tesseract_cmd: 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'

def whatsay(img_path=None):
    """ OCR an image on the path, return a list of found words """
    if not img_path or (not os.path.exists(img_path)):
        print("IMAGE FILE NOT FOUND: {}".format(img_path))
    text = re.findall(r"[\w']+", pytesseract.image_to_string(Image.open(img_path)))
    return [t for t in text if len(t) > 1]


if __name__ == "__main__":
    img_path = os.path.join(os.getcwd(), "pics", "43e6ce66_samsung_Sprint-PCS_playstore.png")
    print("Text gleaned from: {}".format(img_path))
    print(whatsay(img_path=img_path))

    imgs = [os.path.join(os.getcwd(), "pics", im) for im in os.listdir(os.path.join(os.getcwd(), "pics"))
            if im.endswith(".png")]

    wordsets = {}

    for n, img in enumerate(imgs):
        print(" ******* {} ".format(n))
        print("PATH: {}".format(img))
        what = whatsay(img_path=img)
        print(what)
        wordsets[img] = Levenshtein_search.populate_wordset(n, what)
        if n > 15:
            break

    term = "Camara"
    maxdist = 2
    print("START SEARCH")
    for path, wordset in wordsets.items():
        result = Levenshtein_search.lookup(wordset, term, maxdist)
        print("{}  : {}".format(path, result))