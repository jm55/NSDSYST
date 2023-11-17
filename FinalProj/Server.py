import cv2
import random
import os
import time
import numpy as np
import threading
from multiprocessing import Lock, Process, Queue
import queue
import json
from sys import platform
import cv2
import numpy as np
import base64
import pickle
from PIL import Image
import pika
import datetime

from Adjustor import Adjustor

'''
Sources:
Queues: https://www.digitalocean.com/community/tutorials/python-multiprocessing-example
Measuring Performance: https://docs.opencv.org/3.4/dc/d71/tutorial_py_optimization.html
OpenCV Image to JSON: https://stackoverflow.com/a/55900422
'''

class Server():
    IP = '192.168.56.1'
    PORT = 5672
    ROOT = '/'

    def __init__(self):
        print("====SERVER====")
        self.a = Adjustor()
        self.pending = Queue()
        self.finished = Queue()
        self.procs = []
        self.connect_to_server()
        print(f"{datetime.datetime.now()}: Server - Running {os.cpu_count()} cores...")
        for w in range(os.cpu_count()+1):
            p = Process(target=self.run_queue, args=())
            self.procs.append(p)
            p.start()
        print(f"{datetime.datetime.now()}: Server - Listening...\n")
        self.channel.start_consuming()

    def connect_to_server(self):
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(Server.IP, Server.PORT, Server.ROOT, self.credentials, connection_attempts=256))
        print(f"{datetime.datetime.now()}: Server - Credentials -[{self.credentials.username}]:[{self.credentials.password}]")
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=4)
        self.channel.queue_declare(queue='adjustor')
        self.channel.basic_consume(queue='adjustor', on_message_callback=self.on_request, auto_ack=True)

    def run_queue(self):
        while True:
            try:
                self.connection.process_data_events()
                file = self.pending.get() #This will raise an exception if it is empty
                file = json.loads(json.dumps(file))
            except queue.Empty: #Excemption raised if queue is empty. Breaks the while loop.
                print("Queue is Empty!")
            else: #No exception has been raised, add the task completion
                start = time.time()
                image = self.a.adjust_image(file) #Executes actual image processing
                end = time.time()
                print(f'{datetime.datetime.now()}: Server - Processed {file["filename"]} @ {end-start:0.2f}, Left @ Queue = {self.pending.qsize()}')
                file["image"] = self.im2json(image)
                self.finished.put(file)    

    def on_request(self, ch, method, props, body:str):
        #2 layers of json
        json_body = json.loads(body)
        print(f"{datetime.datetime.now()}: Server - Queueing {json_body['filename']}...")
        self.pending.put(json_body)

    def im2json(self, im):
        """Convert a Numpy array to JSON string"""
        imdata = pickle.dumps(im)
        return base64.b64encode(imdata).decode('ascii')
    
    def json2im(self, json_obj:json):
        """Convert a JSON string back to a Numpy array"""
        imdata = base64.b64decode(json_obj['image'])
        im = pickle.loads(imdata)
        return im

def main():
    s = Server()

if __name__ == "__main__":
    main()