import cv2
import numpy as np
import json
import cv2
import numpy as np
from PIL import Image

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
        
    def adjust_image(self, json_obj:json):
        """Adjust Image"""
        adj_image = self.adjust_bc(cv2.imread(json_obj['input'] + "/" + json_obj['filename']), json_obj['brightness'], json_obj['contrast'])
        adj_image = self.adjust_sharpness(adj_image, json_obj['sharpness'])
        cv2.imwrite(json_obj['output'] + "/" + json_obj['filename'], adj_image)
        return adj_image