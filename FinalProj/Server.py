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
from pika.exchange_type import ExchangeType

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
        print(self.print_header() + f"Running {os.cpu_count()} cores...")
        for w in range(os.cpu_count()+1):
            p = Process(target=self.run_queue, args=(int(w),))
            self.procs.append(p)
            p.start()
        r = Process(target=self.run_deliver, args=())
        r.start()
        print(f"{datetime.datetime.now()}: Server - Listening...\n")
        try:
            self.channel_rcv.start_consuming()
        except KeyboardInterrupt:
            self.channel_rcv.stop_consuming()

    def print_header(self):
        return f'{datetime.datetime.now()}: Server - '

    def connect_to_server(self):
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234')
        self.connection_rcv = pika.BlockingConnection(pika.ConnectionParameters(Server.IP, Server.PORT, Server.ROOT, self.credentials, connection_attempts=128, retry_delay=3, heartbeat=600, blocked_connection_timeout=300))
        self.connection_snd = pika.BlockingConnection(pika.ConnectionParameters(Server.IP, Server.PORT, Server.ROOT, self.credentials, connection_attempts=128, retry_delay=3, heartbeat=600, blocked_connection_timeout=300))
        print(f"{datetime.datetime.now()}: Server - Credentials -[{self.credentials.username}]:[{self.credentials.password}]")
        self.channel_rcv = self.connection_rcv.channel(1)
        self.channel_rcv.basic_qos(prefetch_count=os.cpu_count())
        self.channel_rcv.queue_declare(queue='adjustor', durable=True, arguments={'x-max-length':100, 'x-queue-type':'classic','message-ttl':300000})
        self.channel_rcv.basic_consume(queue='adjustor', on_message_callback=self.on_request, auto_ack=True)
        self.channel_snd = self.connection_snd.channel(2)
        self.channel_snd.basic_qos(prefetch_count=os.cpu_count())
        self.channel_snd.exchange_declare(exchange='adjustor_fin', exchange_type=ExchangeType.topic)
        #self.channel_snd.queue_declare(queue='adjustor_fin', durable=True, arguments={'x-max-length':100, 'x-queue-type':'classic','message-ttl':300000})

    def run_queue(self, id:int):
        while True:
            try:
                file = self.pending.get() #This will raise an exception if it is empty
            except queue.Empty: #Excemption raised if queue is empty. Breaks the while loop.
                print("Pending Queue is Empty!")
            else: #No exception has been raised, add the task completion
                file = json.loads(json.dumps(file))
                print(self.print_header() + f'Thread {id} Processing {file["filename"]}...')
                start = time.time()
                image = self.a.adjust_image(file) #Executes actual image processing
                end = time.time()
                print(self.print_header() + f'Thread {id} Processed {file["filename"]} @ {end-start:0.2f}s')
                file["image"] = self.im2json(image)
                self.finished.put(file)

    def run_deliver(self):
        while True:
            try:
                file = self.finished.get()
            except queue.Empty:
                print("Finished Queue is Empty!")
            else:
                file = json.loads(json.dumps(file))
                json_str = json.dumps(file)
                print(self.print_header() + f"Returning {file['filename']}...")
                self.channel_snd.basic_publish(exchange='adjustor_fin', routing_key=file["client_uid"], body=json_str, mandatory=True)

    def on_request(self, ch, method, props, body:str):
        json_body = json.loads(body)
        json_body["client_uid"] = props.headers["client_uid"]
        json_body["item_uid"] = props.headers["item_uid"]
        self.pending.put_nowait(json_body)
        print(f"{datetime.datetime.now()}: Server - Queued {json_body['filename']}, Queue = {self.pending.qsize()}")
        self.connection_rcv.process_data_events()

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