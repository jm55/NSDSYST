import cv2
import numpy as np
import json
import cv2
import numpy as np
from PIL import Image
import pickle
import base64

'''
Brightness enhancement factor
Sharpness enhancement factor
Contrast enhancement factor

Sources:
Brightness & Contrast: https://www.tutorialspoint.com/how-to-change-the-contrast-and-brightness-of-an-image-using-opencv-in-python
Sharpness: https://www.opencvhelp.org/tutorials/image-processing/how-to-sharpen-image/
Save Image: https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
'''

class Adjustor():
    def __init__(self):
        """Constructor"""

    def adjust_bc(self, image, brightness:int, contrast:int):
        """Image Brightness and Contrast Control"""
        brightness = int(50 * (brightness/100)) 
        contrast = int(50 * (contrast/100)) 
        return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

    def adjust_sharpness(self, image, sharpness:int):
        """Image Sharpness Control"""
        return cv2.filter2D(image, int(sharpness*-1), np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
        
    def im2json(self, im):
        """Convert a Numpy array to JSON string"""
        imdata = pickle.dumps(im)
        return base64.b64encode(imdata).decode('ascii')
    
    def json2im(self, json_obj:json):
        """Convert a JSON string back to a Numpy array"""
        imdata = base64.b64decode(json_obj['image'])
        im = pickle.loads(imdata)
        return im

    def adjust_image(self, json_obj:json):
        """Adjust Image"""
        adj_image = self.adjust_bc(self.json2im(json_obj), json_obj['brightness'], json_obj['contrast'])
        adj_image = self.adjust_sharpness(adj_image, json_obj['sharpness'])
        cv2.imwrite(json_obj["output"] + json_obj['filename'], adj_image)
        return adj_image