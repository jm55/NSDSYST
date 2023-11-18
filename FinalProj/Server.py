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
    IP = '192.168.56.1'
    PORT = 5672
    ROOT = '/'

    def __init__(self):
        print("====SERVER====")
        self.a = Adjustor()
        self.pending = Queue()
        self.finished = Queue()
        self.procs = []
        self.connect_to_broker()
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

    def connect_to_broker(self):
        '''Connects the server to RabbitMQ'''
        # RabbitMQ Credentials
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234')
        print(f"{datetime.datetime.now()}: Server - Credentials -[{self.credentials.username}]:[{self.credentials.password}]")
        # Connection Setup
        self.connection_rcv =   pika.BlockingConnection(
                                    pika.ConnectionParameters(
                                        Server.IP, Server.PORT, Server.ROOT, self.credentials, 
                                        connection_attempts=128, retry_delay=3, heartbeat=100, 
                                        blocked_connection_timeout=300)
                                )
        self.connection_snd =   pika.BlockingConnection(
                                    pika.ConnectionParameters(
                                        Server.IP, Server.PORT, Server.ROOT, self.credentials, 
                                        connection_attempts=128, retry_delay=3, heartbeat=100, 
                                        blocked_connection_timeout=300)
                                )
        # Receive Channel Setup
        self.channel_rcv = self.connection_rcv.channel()
        self.channel_rcv.basic_qos(prefetch_count=8, global_qos=True)
        self.channel_rcv.queue_declare(queue='adjustor', durable=True, arguments={'x-max-length':100, 'x-queue-type':'classic','message-ttl':300000}) # Receive channel will use Message Queue 'adjustor'
        self.channel_rcv.basic_consume(queue='adjustor', on_message_callback=self.on_request, auto_ack=True) # Receive channel will consume messages from Queue
        # Send Channel Setup
        self.channel_snd = self.connection_snd.channel()
        self.channel_snd.basic_qos(prefetch_count=8, global_qos=True)
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
                print(self.print_header() + f'Thread {id} Processing {file["filename"]}...')
                start = time.time()
                image = self.a.adjust_image(file) # Executes actual image processing
                end = time.time()
                print(self.print_header() + f'Thread {id} Processed {file["filename"]} @ {end-start:0.2f}s')
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
                print(self.print_header() + f"Returning {file['filename']}...")
                self.channel_snd.basic_publish(exchange='adjustor_fin', routing_key=file["client_uuid"], body=json.dumps(file), mandatory=True)

    def on_request(self, ch, method, props, body:str):
        '''Will execute once the consumer (channel_rcv) consumes a message from 'adjustor' Message Queue.'''
        json_body = json.loads(body)
        json_body["client_uuid"] = props.headers["client_uuid"] # Attach the headers to the message
        #json_body["item_uid"] = props.headers["item_uid"]
        self.pending.put_nowait(json_body) # Put requested (i.e., sent by client) image to pending queue for processing.
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