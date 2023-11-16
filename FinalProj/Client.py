import json
import os
from sys import platform
import pickle, base64
import cv2
from multiprocessing import Lock, Process, Queue
import pika
import uuid

class Client():
    IP = '192.168.56.1'
    PORT = 5672
    ROOT = '/'
    
    received = Queue()
    def __init__(self):
        print("====CLIENT====")
        self.connect_to_server()

    def connect_to_server(self):
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, self.credentials))
        print(f"Server Credentials -[{self.credentials.username}]:[{self.credentials.password}]")
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        self.response = None
        self.corr_id = None
    
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
    
    def request(self, json_str:str):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='adjustor',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(json_str))
        self.connection.process_data_events(time_limit=None)
        return self.response
    
    def create_folder(self, folderpath):
        if not os.path.exists(folderpath):
            print("Making output folder...")
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
location_in = "/home/kali/Documents/GitHub/NSDSYST/POC/test_images/"
location_out = "/home/kali/Documents/GitHub/NSDSYST/FinalProj/test_images_output/"
c.create_folder(location_out)
filenames = c.get_filenames(location_in)[0:5]
print("Client - Filenames:", len(filenames))
print("Client - Parsing to files to JSON...")
jsons = c.parse_to_json(location_in, filenames, location_out+"_outputs", 10,10,10)
for j in jsons:
    json_body = json.loads(c.request(j))
    cv2.imwrite(location_out+"client_"+json_body["filename"], c.json2im(json_body))