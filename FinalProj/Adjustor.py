import cv2
import numpy as np
import json
import cv2
import numpy as np
from PIL import Image
import pickle
import base64

'''
Adjustor.py

Contains adjustments for: Brightness, Contrast, and Sharpness

SOURCES:
Brightness & Contrast - https://www.tutorialspoint.com/how-to-change-the-contrast-and-brightness-of-an-image-using-opencv-in-python
Sharpness - https://www.opencvhelp.org/tutorials/image-processing/how-to-sharpen-image/
Save Image - https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
'''

class Adjustor():
    def __init__(self):
        """Constructor"""

    def adjust_bc(self, image, brightness:int, contrast:int):
        """Image Brightness and Contrast Control"""
        return cv2.convertScaleAbs(image, alpha=int(50*(contrast/100)) , beta=int(50 * (brightness/100)))

    def adjust_sharpness(self, image, sharpness:int):
        """Image Sharpness Control"""
        return cv2.filter2D(image, int(sharpness*-1), np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
        
    def im2json(self, im):
        """Convert a Numpy array to JSON string"""
        return base64.b64encode(pickle.dumps(im)).decode('ascii')
    
    def json2im(self, file:json):
        """Convert a JSON string back to a Numpy array"""
        return pickle.loads(base64.b64decode(file['image']))

    def adjust_image(self, file:json):
        """Adjust Image"""
        adj_image = self.adjust_bc(self.json2im(file), file['brightness'], file['contrast'])
        adj_image = self.adjust_sharpness(adj_image, file['sharpness'])
        #cv2.imwrite(file["output"] + file['filename'], adj_image)
        return adj_image