import cv2
import random
import os
import time
import numpy as np
import threading
from multiprocessing import Lock, Process, Queue, current_process, freeze_support
import queue
import json
from sys import platform
import cv2
import numpy as np
import base64
import pickle
from PIL import Image

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
OpenCV Image to JSON: https://stackoverflow.com/a/55900422
'''

def adjustor(json_obj):
    adj_image = adjust_bc(cv2.imread(json_obj['input'] + "/" + json_obj['filename']), json_obj['brightness'], json_obj['contrast'])
    adj_image = adjust_sharpness(adj_image, json_obj['sharpness'])
    cv2.imwrite(json_obj['output'] + "/" + json_obj['filename'], adj_image)
    return adj_image

def im2json(im):
    """Convert a Numpy array to JSON string"""
    imdata = pickle.dumps(im)
    jstr = json.dumps({"image": base64.b64encode(imdata).decode('ascii')})
    return jstr
    
#To implement in Client
def json2im(jstr):
    """Convert a JSON string back to a Numpy array"""
    load = json.loads(jstr)
    imdata = base64.b64decode(load["image"])
    im = pickle.loads(imdata)
    return im

def run_queue(pending=Queue, finished=Queue):
    size = pending.qsize()
    while True:
        try:
            file = pending.get_nowait() #This will raise an exception if it is empty
            file = json.loads(file)
        except queue.Empty: #Excemption raised if queue is empty. Breaks the while loop.
            print("Queue is Empty!")
            break
        else: #No exception has been raised, add the task completion
            start = time.time()
            image = adjustor(file) #Executes actual image processing
            end = time.time()
            print(f'Processed: {file["filename"]} @ {end-start:0.2f}')
            file["img"] = im2json(image)
            finished.put(file)
    return True

def listen_to_queue(finished:Queue, running:bool):
    while running:
        if finished.qsize() > 0:
            print("Finished Queue:", finished.get()['filename'], finished.qsize(), running)
    return True

#This can be executed in a distributed manner where the contents of the filenames(list) parameter will dictate what files to process.
def coordinator(input_folder, filenames, output_folder, brightness, contrast, sharpness, threads=os.cpu_count()):
    print("Coordinator...")
    pending = Queue()
    finished = Queue()
    listening = True
    procs = []

    print("Listening to Finished Queue...")
    l = threading.Thread(target=listen_to_queue, args=(finished,listening))
    l.start()

    #Create jobs/tasks
    print("Creating Jobs...")
    for f in filenames:
        jsonObj = json_generate(input_folder, str(f), output_folder, brightness, contrast, sharpness)
        pending.put(jsonObj)
    #Create, run, & complete processes
    print("Running threads...")
    for w in range(threads):
        p = Process(target=run_queue, args=(pending, finished))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
    # while not finished.empty():
    #     print(finished.get())
    print("Closing Listener...")
    l.join()
    return

def adjust_bc(image, brightness, contrast):
    brightness = int(50 * (brightness/100)) 
    contrast = int(50 * (contrast/100)) 
    return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

def adjust_sharpness(image, sharpness):
    return cv2.filter2D(image, int(sharpness*-1), np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))

def json_generate(input_folder, filename, output_folder, brightness, contrast, sharpness):
    return json.dumps({'input':input_folder, 'filename':filename, 'output':output_folder,'brightness':brightness,'contrast':contrast,'sharpness':sharpness})

def get_filenames(folder_path):
    return os.listdir(folder_path)

def get_params():
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

def create_folder(input_folder):
    output_folder = input_folder + "_output"
    if not os.path.exists(output_folder):
        print("Making output folder...")
        if platform == "linux" or platform == "linux2":
            try:
                original_umask = os.umask(0)
                os.mkdir(output_folder, mode=0o777) #chmod 777 aka full access
            finally:
                os.umask(original_umask)
        else: #assumes Windows
            os.mkdir(output_folder)
    return output_folder

def test_import():
    print("File Accessible!")

def isLinux():
    return platform == "linux" or platform == "linux2"

def clientSide():
    input_folder = input("Enter absolute folder path containing images: ")
    output_folder = create_folder(input_folder)
    filenames = get_filenames(input_folder)
    parameters = get_params()    
    return [input_folder, output_folder, filenames, parameters]

def main():
    print("Image POC!")
    print("CPU Count:", os.cpu_count())
    inputs = clientSide()
    start = time.time()
    coordinator(inputs[0], inputs[2], inputs[1], inputs[3][0], inputs[3][1], inputs[3][2])
    end = time.time()
    print(f"Runtime: {end-start:.2f}s ({(end-start)/len(inputs[2]):.2f}s/image)")

if __name__ == "__main__":
    main()
