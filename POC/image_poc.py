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
Measuring Performance: https://docs.opencv.org/3.4/dc/d71/tutorial_py_optimization.html
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
            file = pending.get_nowait() #This will raise an exception if it is empty
        except queue.Empty: #Excemption raised if queue is empty. Breaks the while loop.
            break
        else: #No exception has been raised, add the task completion 
            adjustor(file) #Executes actual image processing
            print(json.loads(file)['filename'])
            finished.put_nowait(json.loads(file)['filename'] + ' --> ' + current_process().name)
    return True

#This can be executed in a distributed manner where the contents of the filenames(list) parameter will dictate what files to process.
def coordinator(input_folder, filenames, output_folder, brightness, contrast, sharpness, threads=os.cpu_count()):
    pending = Queue()
    finished = Queue()
    procs = []

    #Create jobs/tasks
    for f in filenames:
        jsonObj = jsonGenerate(input_folder, str(f), output_folder, brightness, contrast, sharpness)
        pending.put(jsonObj)
    #Create, run, & complete processes
    for w in range(threads):
        p = Process(target=run_queue, args=(pending, finished))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
    # while not finished.empty():
    #     print(finished.get())
    return

def adjustBC(image, brightness, contrast):
    brightness = int(50 * (brightness/100)) 
    contrast = int(50 * (contrast/100)) 
    return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

def adjustSharpness(image, sharpness):
    return cv2.filter2D(image, int(sharpness*-1), np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
    
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


def clientSide():
    input_folder = input("Enter absolute folder path containing images: ")
    output_folder = createFolder(input_folder)
    filenames = getFilenames(input_folder)
    parameters = getParams()
    
    return [input_folder, output_folder, filenames, parameters]


def main():
    print("Image POC!")
    print("CPU Count:", os.cpu_count())
    inputs = clientSide()
    start = time.time()
    coordinator(inputs[0], inputs[2], inputs[1], inputs[3][0], inputs[3][1], inputs[3][2])
    end = time.time()
    print(f"Runtime: {end-start:.2f}s ({(end-start)/len(filenames):.2f}s/image)")

if __name__ == "__main__":
    main()