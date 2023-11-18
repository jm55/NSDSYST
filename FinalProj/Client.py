import json
import os
from sys import platform
import pickle, base64
import cv2
from multiprocessing import Lock, Process, Queue
import pika
from pika.exchange_type import ExchangeType
from pika.exceptions import ChannelWrongStateError, ChannelClosedByBroker
import uuid
import datetime, time

'''
Sources:
Queues: https://www.digitalocean.com/community/tutorials/python-multiprocessing-example
Measuring Performance: https://docs.opencv.org/3.4/dc/d71/tutorial_py_optimization.html
OpenCV Image to JSON: https://stackoverflow.com/a/55900422
'''

class Client():
    IP = '192.168.56.1'
    PORT = 5672
    ROOT = '/'

    def __init__(self):
        print("====CLIENT====")
        self.connect_to_server()
        self.channel_rcv.basic_consume(queue = self.rcv_queue, on_message_callback=self.receive, auto_ack=True, exclusive=True)
        self.consume = Process(target=self.channel_rcv.start_consuming, args=())
        self.start_consuming()

    def start_consuming(self):
        self.consume.start()

    def stop_consuming(self):
        self.consume.join()
        self.channel_rcv.stop_consuming()

    def print_header(self):
        return f"{datetime.datetime.now()}: Client - "

    def connect_to_server(self):
        self.CLIENT_UUID = str(uuid.uuid1())
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234')
        print(self.print_header() + f"Credentials -[{self.credentials.username}]:[{self.credentials.password}]")
        print(self.print_header() + f"Connecting (rcv & snd) to RabbitMQ...")
        self.connection_snd = pika.BlockingConnection(pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, self.credentials, connection_attempts=128, retry_delay=1, heartbeat=600, blocked_connection_timeout=300))
        self.connection_rcv = pika.BlockingConnection(pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, self.credentials, connection_attempts=128, retry_delay=1, heartbeat=600, blocked_connection_timeout=300))
        print(self.print_header() + f"Connected (rcv & snd) to RabbitMQ!")
        print(self.print_header() + f"Creating Channels (rcv & snd)...")
        self.channel_snd = self.connection_snd.channel()
        self.channel_rcv = self.connection_rcv.channel()
        print(self.print_header() + f"Channels Created (rcv & snd)!")
        print(self.print_header() + f"Preparing Receiver...")
        self.channel_rcv.exchange_declare(exchange='adjustor_fin', exchange_type=ExchangeType.topic)
        result = self.channel_rcv.queue_declare(queue='', exclusive=True)
        self.rcv_queue = result.method.queue
        self.channel_rcv.queue_bind(exchange='adjustor_fin', queue=self.rcv_queue, routing_key=self.CLIENT_UUID)
        print(self.print_header() + f"Receiver Prepared!")
        self.response = None
        self.corr_id = None

    def receive(self, ch, method, props, body):
        json_obj = json.loads(body)
        print(self.print_header() + f"Received {json_obj['filename']}")
        if self.corr_id == props.correlation_id and json_obj['client_uid'] == self.CLIENT_UUID:
            im = self.json2im(json_obj)
            cv2.imwrite(json_obj["output"]+json_obj["filename"], im)
            print(self.print_header() + f"File {json_obj['filename']} written!")
        else:
            print(self.print_header() + "Identity Mismatch Detected!")
    
    def send(self, json_str:str):
        try:
            self.corr_id = str(uuid.uuid4())
            self.channel_snd.basic_publish(
                exchange='',
                routing_key='adjustor',
                properties=pika.BasicProperties(
                    #reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                    headers={'client_uid':self.CLIENT_UUID, 'item_uid':self.corr_id},
                ),
                body=str(json_str),
                mandatory=True
            )
            self.connection_snd.process_data_events()
            return True
        except ChannelWrongStateError as e:
            print(self.print_header(), e.with_traceback(None))
            print(self.print_header() + f"Restarting Connection & Channel...")
            self.connection_snd = pika.BlockingConnection(pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, self.credentials, connection_attempts=128, retry_delay=1, heartbeat=600, blocked_connection_timeout=300))
            self.channel_snd = self.connection_snd.channel()
            return False
        except ChannelClosedByBroker as e:
            print(self.print_header(), e.with_traceback(None))
            print(self.print_header() + f"Restarting Connection & Channel...")
            self.connection_snd = pika.BlockingConnection(pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, self.credentials, connection_attempts=128, retry_delay=1, heartbeat=600, blocked_connection_timeout=300))
            self.channel_snd = self.connection_snd.channel()
            return False
    
    def create_folder(self, folderpath):
        if not os.path.exists(folderpath):
            print(self.print_header() + f"Making Folder...")
            if platform == "linux" or platform == "linux2":
                try:
                    original_umask = os.umask(0)
                    os.mkdir(folderpath, mode=0o777) #chmod 777 aka full access
                finally:
                    os.umask(original_umask)
            elif platform == "win32":
                os.mkdir(folderpath)
        return folderpath
    
    def get_inputs(self):
        input_folder = input("Enter absolute folder path containing images: ")
        output_folder = self.create_folder(input_folder)
        filenames = self.get_filenames(input_folder)
        parameters = self.get_params()    
        return [input_folder, output_folder, filenames, parameters]
    
    def get_filenames(self, folder_path):
        return os.listdir(folder_path)
    
    def get_params(self):
        brightness = float(input("Enter brightness value (0 - 100): "))
        if brightness > 100: brightness = 100
        if brightness < 0: brightness = 0
        contrast = float(input("Enter contrast value (0 - 100): "))
        if contrast > 100: contrast = 100
        if contrast < 0: contrast = 0
        sharpness = float(input("Enter sharpness value (0 - 100): "))
        if sharpness > 100: sharpness = 100
        if sharpness < 0: sharpness = 0
        return [brightness, contrast, sharpness]
    
    def im2json(self, im):
        """Convert a Numpy array to JSON string"""
        imdata = pickle.dumps(im)
        return base64.b64encode(imdata).decode('ascii')
    
    def json2im(self, json_obj:json):
        """Convert a JSON string back to a Numpy array"""
        imdata = base64.b64decode(json_obj['image'])
        im = pickle.loads(imdata)
        return im
    
    def parse_to_json(self, input_folder, filenames:list, output_folder, brightness, contrast, sharpness):
        jsons = []
        for f in filenames:
            #print(f"Processing {f}...")
            jsons.append(self.json_generate(input_folder, f, output_folder, brightness, contrast, sharpness))
        return jsons
    
    def json_generate(self, input_folder, filename:str, output_folder, brightness, contrast, sharpness):
        im = cv2.imread(input_folder+filename)
        return json.dumps({'input':input_folder, 'filename':filename, 'output':output_folder,'brightness':brightness,'contrast':contrast,'sharpness':sharpness,'image':self.im2json(im)})

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
c = Client()
print("NOTE: Input files limited to 2MB")
size_limit = 5 #MB
location_in = "/home/kali/Documents/GitHub/NSDSYST/FinalProj/tokyo/"
location_out = location_in[0:len(location_in)-1] + "_output/"
brightness = 10
contrast = 10
sharpness = 10
c.create_folder(location_out)
filenames = c.get_filenames(location_in)
filenames.sort()
for f in filenames:
    try:
        os.remove(location_out + f)
    except:
        print(c.print_header() + f"File {location_out + f} does not exist.")
print(c.print_header() + f"Input Location = {location_in}")
print(c.print_header() + f"Output Location = {location_out}")
print(c.print_header() + f"Files Count = ", len(filenames))
filtered_filenames = []
for f in filenames:
    stats = os.stat(location_in+f)
    if (stats.st_size / (1024 * 1024)) <= size_limit:
        filtered_filenames.append(f)
    else:
        print(c.print_header() + f"File {f} exceeds the filesize limit of {size_limit}MB!")
print(c.print_header() + f"Accepted Files Count = ", len(filtered_filenames))
print(c.print_header() + f"Parsing to files to JSON...")
#jsons = c.parse_to_json(location_in, filenames, location_out+"_outputs", 10,10,10)
start = time.time()
for f in filenames:
    print(c.print_header() + f"Sending {f}...")
    repeat = 0
    while repeat != 10:
        if c.send(c.json_generate(location_in, f, location_out, brightness, contrast, sharpness)):
            break
while True:
    if len(filtered_filenames) == len(c.get_filenames(location_out)):
        print(c.print_header() + f"All filtered files received ({len(filtered_filenames)} files)")
        end = time.time()
        c.connection_rcv.close()
        c.connection_snd.close()
        print(f"Processing Time: {end-start:0.4f}s")
        exit(0)