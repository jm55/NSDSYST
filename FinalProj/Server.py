import os
import time, datetime
from multiprocessing import Lock, Process, Queue
import queue
from sys import platform
import json, base64, pickle
from PIL import Image
import pika
from pika.exchange_type import ExchangeType

from Adjustor import Adjustor

'''
Server.py

Acts as the server-end(s) of the disributed system.

SOURCES:
Multiprocessing Queues - https://www.digitalocean.com/community/tutorials/python-multiprocessing-example
Work Queues - https://www.rabbitmq.com/tutorials/tutorial-two-python.html
Threaded Basic_Consumer - https://github.com/pika/pika/blob/1.0.1/examples/basic_consumer_threaded.py
OpenCV Image to JSON - https://stackoverflow.com/a/55900422
'''

class Server():
    
    def __init__(self):
        self.IP = '192.168.56.1' # IP of the message broker
        self.PORT = 5672 # Port of the Message Broker
        self.ROOT = '/'
        self.CORE = os.cpu_count()
        print("====SERVER====")
        tempIP = input(f"Enter Message Broker IP Address (leave empty for {self.IP}): ")
        tempPORT = input(f"Enter Message Broker Port No. (leave empty for {self.PORT}): ")
        tempROOT = input(f"Enter Root Directory to Message Broker (leave empty for {self.ROOT}): ")
        tempCORE = input(f"Enter number of threads to use (leave empty for {os.cpu_count()}): ")
        if tempIP != "":
            self.IP = tempIP
        if tempPORT != "":
            self.PORT = int(tempPORT)
        if tempROOT != "":
            self.ROOT = tempROOT
        if tempCORE != "":
            self.CORE = int(tempCORE)
        os.system('clear')
        print("====SERVER====")
        self.a = Adjustor()
        self.pending = Queue()
        self.finished = Queue()
        self.procs = []
        self.connect_to_broker()
        print(self.print_header() + f"Running {self.CORE} cores...")
        for w in range(self.CORE+1):
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

    def connect_to_broker(self):
        '''Connects the server to RabbitMQ'''
        # RabbitMQ Credentials
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234')
        print(f"{datetime.datetime.now()}: Server - Credentials - [{self.credentials.username}]:[{self.credentials.password}]")
        # Connection Setup
        self.connection_rcv =   pika.BlockingConnection(
                                    pika.ConnectionParameters(
                                        self.IP, self.PORT, self.ROOT, self.credentials, 
                                        connection_attempts=32, retry_delay=1, heartbeat=32, 
                                        blocked_connection_timeout=300)
                                )
        self.connection_snd =   pika.BlockingConnection(
                                    pika.ConnectionParameters(
                                        self.IP, self.PORT, self.ROOT, self.credentials, 
                                        connection_attempts=32, retry_delay=1, heartbeat=32, 
                                        blocked_connection_timeout=300)
                                )
        # Receive Channel Setup
        self.channel_rcv = self.connection_rcv.channel()
        self.channel_rcv.basic_qos(prefetch_count=os.cpu_count(), global_qos=False)
        self.channel_rcv.queue_declare(queue='adjustor', durable=True, auto_delete=True, arguments={'x-max-length':100, 'x-queue-type':'classic','message-ttl':300000}) # Receive channel will use Message Queue 'adjustor'
        self.channel_rcv.basic_consume(queue='adjustor', on_message_callback=self.on_request, auto_ack=True) # Receive channel will consume messages from Queue
        # Send Channel Setup
        self.channel_snd = self.connection_snd.channel()
        self.channel_snd.basic_qos(prefetch_count=os.cpu_count(), global_qos=False)
        self.channel_snd.exchange_declare(exchange='adjustor_fin', exchange_type=ExchangeType.topic) # Send channel will use the Topic Exchange 'adjustor_fin'
        
    def run_queue(self, id:int):
        '''
        Watches the pending queue to execute the image processing.
        Note that this runs on a threaded manner.
        '''
        while True:
            try:
                file = self.pending.get() # This will raise an exception if it is empty
            except queue.Empty: # Excemption raised if queue is empty. Breaks the while loop.
                print("Pending Queue is Empty!")
            else: # No exception has been raised, add the task completion
                file = json.loads(json.dumps(file))
                print(self.print_header() + f'{"Processing:":15s} {file["filename"]:30s} Thread-{str(id):3s}')
                start = time.time()
                image = self.a.adjust_image(file) # Executes actual image processing
                print(self.print_header() + f'{"Processed:":15s} {file["filename"]:30s} Thread-{str(id):3s} {time.time()-start:0.2f}s')
                file["image"] = self.im2json(image)
                self.finished.put_nowait(file)

    def run_deliver(self):
        '''
        Watches the finished queue to deliver the finished products to respective users (via client_uuid).
        Note that this runs on a threaded manner.
        '''
        while True:
            try:
                file = self.finished.get()
            except queue.Empty:
                print("Finished Queue is Empty!")
            else:
                file = json.loads(json.dumps(file))
                print(self.print_header() + f"{'Returning:':15s} {file['filename']:30s}")
                self.channel_snd.basic_publish(exchange='adjustor_fin', routing_key=file["client_uuid"], body=json.dumps(file), mandatory=True)

    def on_request(self, ch, method, props, body:str):
        '''Will execute once the consumer (channel_rcv) consumes a message from 'adjustor' Message Queue.'''
        file = json.loads(body)
        self.pending.put_nowait(file) # Put requested (i.e., sent by client) image to pending queue for processing.
        self.connection_rcv.process_data_events()
        print(self.print_header() + f"{'Queued':15s} {file['filename']:30s} {'Remaining '+str(self.pending.qsize())}")

    def im2json(self, im):
        """Convert a Numpy array to JSON string"""
        return base64.b64encode(pickle.dumps(im)).decode('ascii')
    
    def json2im(self, file:json):
        """Convert a JSON string back to a Numpy array"""
        return pickle.loads(base64.b64decode(file['image']))

def main():
    s = Server()

if __name__ == "__main__":
    main()