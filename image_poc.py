import cv2
import random
import os
import time
import numpy as np
from multiprocessing import Lock, Process, Queue, current_process, freeze_support
import queue
import json

'''
Brightness enhancement factor
Sharpness enhancement factor
Contrast enhancement factor

Sources:
Brightness & Contrast: https://www.tutorialspoint.com/how-to-change-the-contrast-and-brightness-of-an-image-using-opencv-in-python
Sharpness: https://www.opencvhelp.org/tutorials/image-processing/how-to-sharpen-image/
Save Image: https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
Queues: https://www.digitalocean.com/community/tutorials/python-multiprocessing-example
'''

def adjustor(json_obj):
    json_obj = json.loads(json_obj)
    adj_image = adjustBC(cv2.imread(json_obj['input'] + "/" + json_obj['filename']), json_obj['brightness'], json_obj['contrast'])
    adj_image = adjustSharpness(adj_image, json_obj['sharpness'])
    cv2.imwrite(json_obj['output'] + "/" + json_obj['filename'], adj_image)

def run_queue(pending, finished):
    size = pending.qsize()
    while True:
        try:
            '''
                try to get task from the queue. get_nowait() function will 
                raise queue.Empty exception if the queue is empty. 
                queue(False) function would do the same task also.
            '''
            file = pending.get_nowait()
        except queue.Empty:
            break
        else:
            '''
                if no exception has been raised, add the task completion 
                message to task_that_are_done queue
            '''
            adjustor(file) #Executes actual image processing
            print(json.loads(file)['filename'], finished.qsize())
            finished.put_nowait(json.loads(file)['filename'] + ' --> ' + current_process().name)
    return True

def coordinator(input_folder, filenames, output_folder, brightness, contrast, sharpness):
    pending = Queue()
    finished = Queue()
    procs = []

    #Create jobs/tasks
    for f in filenames:
        jsonObj = jsonGenerate(input_folder, str(f), output_folder, brightness, contrast, sharpness)
        pending.put(jsonObj)
    #Create, run, & complete processes
    for w in range(os.cpu_count()):
        p = Process(target=run_queue, args=(pending, finished))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
    while not finished.empty():
        print(finished.get())
    return

def adjustBC(image, brightness, contrast):
    brightness = int(50 * (brightness/100)) 
    contrast = int(50 * (contrast/100)) 
    return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

def adjustSharpness(image, sharpness):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpness *= -1
    return cv2.filter2D(image, int(sharpness), kernel)
    
def getFilenames(folder_path):
    return os.listdir(folder_path)

def jsonGenerate(input_folder, filename, output_folder, brightness, contrast, sharpness):
    return json.dumps({'input':input_folder, 'filename':filename, 'output':output_folder,'brightness':brightness,'contrast':contrast,'sharpness':sharpness})

def getParams():
    brightness = float(input("Enter brightness value (0 - 100): "))
    if brightness > 100:
        brightness = 100
    if brightness < 0:
        brightness = 0
    contrast = float(input("Enter contrast value (0 - 100): "))
    if contrast > 100:
        contrast = 100
    if contrast < 0:
        contrast = 0
    sharpness = float(input("Enter sharpness value (0 - 100): "))
    if sharpness > 100:
        sharpness = 100
    if sharpness < 0:
        sharpness = 0
    return [brightness, contrast, sharpness]

def createFolder(input_folder):
    output_folder = input_folder + "_output"
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    return output_folder

def testImport():
    print("File Accessible!")

def main():
    print("Image POC!")
    print("CPU Count:", os.cpu_count())
    input_folder = input("Enter absolute folder path containing images: ")
    output_folder = createFolder(input_folder)
    filenames = getFilenames(input_folder)
    parameters = getParams()
    coordinator(input_folder, filenames, output_folder, parameters[0], parameters[1], parameters[2])

if __name__ == "__main__":
    main()