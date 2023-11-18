import os
import cv2
from sys import platform
import json, uuid, pickle, base64
from multiprocessing import Lock, Process, Queue
import queue
import pika
from pika.exchange_type import ExchangeType
from pika.exceptions import ChannelWrongStateError, ChannelClosedByBroker
import datetime, time

'''
Client.py

Acts as the client-end of the disributed system.

SOURCES:
Exchange Types - https://www.rabbitmq.com/tutorials/amqp-concepts.html
Exchange Types - https://www.cloudamqp.com/blog/part4-rabbitmq-for-beginners-exchanges-routing-keys-bindings.html
Topic Exchange - https://www.cloudamqp.com/blog/rabbitmq-topic-exchange-explained.html
Topic Exchange - https://www.rabbitmq.com/tutorials/tutorial-five-python.html
Multiprocessing Queues - https://www.digitalocean.com/community/tutorials/python-multiprocessing-example
OpenCV Image to JSON - https://stackoverflow.com/a/55900422
'''

class Client():
    IP = '192.168.56.1' # IP of the message broker
    PORT = 5672 # Port of the Message Broker
    ROOT = '/' # Root Directory of the Message Broker (depends on credentials)

    def __init__(self):
        print("====CLIENT====")
        self.CLIENT_UUID = str(uuid.uuid1()) # Client UUID
        self.running = True # For controlling threads
        self.received = Queue() # For handling received items
        self.connect_to_server() # Prepare the communications to the server.
        self.channel_rcv.basic_consume(queue = self.rcv_queue, on_message_callback=self.on_receive, auto_ack=True, exclusive=False) #Set consumer to 'listen' on rcv_queue and process received messages using receive() 
        self.consume = Process(target=self.channel_rcv.start_consuming, args=())
        print(self.print_header() + "Preparing file writers...")
        writers = []
        for i in range(2): # At least 2 threads for simultaneous file writing of received files
            writers.append(Process(target=self.write_to_file, args=(i,)))
        for i in range(len(writers)):
            writers[i].start()
        print(self.print_header() + "File writers prepared!")
        self.start_consuming()

    def start_consuming(self):
        '''Starts the consumption of processed images.'''
        self.consume.start()

    def stop_consuming(self):
        '''Stops the consumption of processed images.'''
        self.running=False
        self.channel_rcv.stop_consuming()
        self.channel_rcv.close()
        self.channel_snd.close()
        self.consume.kill()

    def print_header(self):
        '''Miscellaneous function for printing'''
        return f"{datetime.datetime.now()}: Client - "

    def connect_to_server(self):
        '''Connect to the server'''
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234') # RabbitMQ Account
        print(self.print_header() + f"Credentials - [{self.credentials.username}]:[{self.credentials.password}]")
        # Connect to connection to server via RabbitMQ
        print(self.print_header() + f"Connecting (RCV & SND) to RabbitMQ...")
        self.connection_snd =   pika.BlockingConnection( # Dedicated connection for sending requests
                                    pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, 
                                                              self.credentials, connection_attempts=128, 
                                                              retry_delay=1, heartbeat=600, 
                                                              blocked_connection_timeout=300)
                                )
        self.connection_rcv =   pika.BlockingConnection( # Dedicated connection for receiving processed requests
                                    pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, 
                                                              self.credentials, connection_attempts=128, 
                                                              retry_delay=1, heartbeat=600, 
                                                              blocked_connection_timeout=300)
                                )
        print(self.print_header() + f"Connected (RCV & SND) to RabbitMQ!")
        #Count Machines
        self.channel_count = self.connection_rcv.channel()
        result = self.channel_count.queue_declare(queue='adjustor', durable=True, arguments={'x-max-length':100, 'x-queue-type':'classic','message-ttl':300000})
        self.n_machines = result.method.consumer_count
        print(self.print_header() + f"No. of Consumers Detected = {self.n_machines}")
        # Create Send & Receive Channels
        print(self.print_header() + f"Creating Channels (RCV & SND)...")
        self.channel_snd = self.connection_snd.channel()
        self.channel_rcv = self.connection_rcv.channel()
        print(self.print_header() + f"Channels Created (RCV & SND)!")
        # Prepare Receiving Channel
        print(self.print_header() + f"Preparing Receiver...")
        self.channel_rcv.exchange_declare(exchange='adjustor_fin', exchange_type=ExchangeType.topic) # Will use Topic Exchange where the 'topic' is based if it matches the Client UUID
        result = self.channel_rcv.queue_declare(queue='', exclusive=True)
        self.rcv_queue = result.method.queue
        self.channel_rcv.queue_bind(exchange='adjustor_fin', queue=self.rcv_queue, routing_key=self.CLIENT_UUID) # Binds the rcv_queue to the exchange from server (i.e., all messages that routing_key==CLIENT_UUID will enter here)
        print(self.print_header() + f"Receiver Prepared!")
        self.corr_id = None

    def write_to_file(self, id:str):
        '''
        Watches the received queue to execute file writing to disk.
        Note that this runs on a threaded manner.
        '''
        while self.running:
            try:
                file = self.received.get() # Get a file from the received queue
            except queue.Empty: # Excemption raised if queue is empty.
                print("Pending Queue is Empty!")
            else:
                file = json.loads(file) # Parse the file str as JSON object and write as file.
                print(self.print_header() + f"{'Writing:':10s} {file['filename']:30s} Thread-{id}")
                cv2.imwrite(file['output'] + file['filename'], self.json2im(file))
                print(self.print_header() + f"{'Written:':10s} {file['filename']:30s} Thread-{id}")
        print(self.print_header() + f"Write_To_File Thread {id} Closed")
        return

    def on_receive(self, ch, method, props, body:str):
        '''Will execute once the consumer (channel_rcv) consumes a message from 'adjustor' Message Queue.'''
        file = json.loads(body)
        print(self.print_header() + f"{'Received:':10s} {file['filename']:30s}")
        if self.corr_id == props.correlation_id and file['client_uuid'] == self.CLIENT_UUID:
            self.received.put_nowait(body)
        else:
            print(self.print_header() + "IDENTITY MISMATCH DETECTED!")
    
    def send(self, json_str:str):
        '''Send an image & metadata to server.'''
        try:
            self.corr_id = str(uuid.uuid4()) # Correlation ID (not sure if working during receive)
            self.channel_snd.basic_publish( # Send/Publish the image to the adjustor queue of RabbitMQ to be received by the server
                exchange='',
                routing_key='adjustor',
                properties=pika.BasicProperties(
                    #reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                    #headers={'client_uuid':self.CLIENT_UUID}, #'item_uid':self.corr_id},
                ),
                body=json_str,
                mandatory=True
            )
            self.connection_snd.process_data_events()
            return True
        except ChannelWrongStateError as e:
            print(self.print_header(), e.with_traceback(None))
            print(self.print_header() + f"Restarting Connection & Channel...")
            self.connection_snd =   pika.BlockingConnection(
                                        pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, self.credentials, 
                                                                connection_attempts=128, retry_delay=1, heartbeat=100, 
                                                                blocked_connection_timeout=300)
                                    )
            self.channel_snd = self.connection_snd.channel()
            return False
        except ChannelClosedByBroker as e:
            print(self.print_header(), e.with_traceback(None))
            print(self.print_header() + f"Restarting Connection & Channel...")
            self.connection_snd =   pika.BlockingConnection(
                                        pika.ConnectionParameters(Client.IP, Client.PORT, Client.ROOT, self.credentials, 
                                                                connection_attempts=128, retry_delay=1, heartbeat=100, 
                                                                blocked_connection_timeout=300)
                                    )
            self.channel_snd = self.connection_snd.channel()
            return False
    
    def im2json(self, im):
        """Convert a Numpy array to JSON string"""
        imdata = pickle.dumps(im)
        return base64.b64encode(imdata).decode('ascii')
    
    def json2im(self, json_obj:json):
        """Convert a JSON string back to a Numpy array."""
        imdata = base64.b64decode(json_obj['image'])
        im = pickle.loads(imdata)
        return im
        
    def json_generate(self, input_folder, filename:str, output_folder, brightness, contrast, sharpness):
        '''JSONify the inputs and the image object itself'''
        im = cv2.imread(input_folder+filename)
        return json.dumps({'input':input_folder, 'filename':filename, 'output':output_folder,'brightness':brightness,'contrast':contrast,'sharpness':sharpness,'image':self.im2json(im),'client_uuid':self.CLIENT_UUID})

class Client_Driver():
    def __init__(self, auto:bool=False, auto_params:list=None):
        self.auto = auto
        self.auto_params = auto_params
        self.main()

    def menu(self):
        self.location_in = input("Enter input folder path (include last /): ")
        if self.location_in[len(self.location_in)-1] != "/":
            self.location_in += "/"
        self.location_out = input("Enter output folder path (include last /): ")
        if self.location_out[len(self.location_in)-1] != "/":
            self.location_out += "/"
        self.brightness = 0
        self.contrast = 0
        self.sharpness = 0
        try:
            self.brightness = int(input("Input Brightness Value (1-100): "))
            self.contrast = int(input("Enter Contrast Value (1-100): "))
            self.sharpness = int(input("Enter Sharpness Value (1-10): "))
        except:
            print("Input Parsing Error!\nExiting...")
            exit(1)
        return self.location_in, self.location_out, self.brightness, self.contrast, self.sharpness

    def get_var(self):
        return "", "", 0, 0, 0
    
    def get_filenames(self, folder_path):
        return os.listdir(folder_path)
    
    def create_folder(self, folderpath):
        if not os.path.exists(folderpath):
            print(self.c.print_header() + f"Making Folder...")
            if platform == "linux" or platform == "linux2":
                try:
                    original_umask = os.umask(0)
                    os.mkdir(folderpath, mode=0o777) #chmod 777 aka full access
                finally:
                    os.umask(original_umask)
            elif platform == "win32":
                os.mkdir(folderpath)
        return folderpath

    def prepare_data(self, c:Client):
        self.create_folder(self.location_out)
        filenames = self.get_filenames(self.location_in)
        filenames.sort()
        for f in filenames:
            try:
                os.remove(self.location_out + f)
            except:
                print(c.print_header() + f"File {self.location_out + f} does not exist.")
        print(c.print_header() + f"Input Location = {self.location_in}")
        print(c.print_header() + f"Output Location = {self.location_out}")
        print(c.print_header() + f"Files Count = ", len(filenames))
        filtered_filenames = []
        for f in filenames:
            stats = os.stat(self.location_in+f)
            if (stats.st_size / (1024 * 1024)) <= self.size_limit:
                filtered_filenames.append(f)
            else:
                print(c.print_header() + f"File {f} exceeds the filesize limit of {self.size_limit}MB!")
        print(c.print_header() + f"Accepted Files Count = ", len(filtered_filenames))
        return filtered_filenames

    def runtime(self):
        if platform == "linux" or platform == "linux2":
            os.system('clear')
        elif platform == "win32":
            os.system('cls')
        self.c = Client()
        self.size_limit = 5 #MB
        print(f"NOTE: Input files limited to {self.size_limit}MB")
        self.location_in, self.location_out, self.brightness, self.contrast, self.sharpness = self.get_var()
        if self.auto:
            self.location_in = auto_params[0]
            self.location_out = self.location_in[0:len(self.location_in)-1] + "_output/"
            self.brightness = auto_params[1]
            self.contrast = auto_params[2]
            self.sharpness = auto_params[3]
        else:
            self.menu()
        self.filtered_filenames = self.prepare_data(self.c)
        print(self.c.print_header() + f"Parsing to files to JSON...")
        #jsons = c.parse_to_json(location_in, filenames, location_out+"_outputs", 10,10,10)
        start = time.time()
        for f in self.filtered_filenames:
            print(self.c.print_header() + f"{'Sending':10s} {f:30s}")
            repeat = 0
            while repeat != 10:
                if self.c.send(self.c.json_generate(self.location_in, f, self.location_out, self.brightness, self.contrast, self.sharpness)):
                    break
        while True:
            if len(self.filtered_filenames) == len(self.get_filenames(self.location_out)):
                print(self.c.print_header() + f"ALL PASSED FILES RECEIVED ({len(self.filtered_filenames)} files)!")
                end = time.time()
                print(self.c.print_header() + f"Processing Time: {end-start:0.4f}s")
                self.write_report(end-start)
                break
        exit(0)

    def write_report(self, elapsed:float):
        '''Prints a text file containing # of images processed, time elapsed, no. of machines used'''
        filename = str(datetime.datetime.now()).replace(':','').replace('.','').replace(' ','_')+".txt"
        with open(filename,'w') as f:
            f.write(f"Input Path: {self.location_in}\n")
            f.write(f"Output Path: {self.location_out}\n")
            f.write(f"Input File Count (File sizes <= {self.size_limit}MB): {len(self.filtered_filenames)}\n")
            f.write(f"Input File Count (File sizes <= {self.size_limit}MB): {len(self.get_filenames(self.location_out))}\n")
            f.write(f"Time Elapsed: {elapsed:0.4f}s\n")
            f.write(f"No. of Machines: {self.c.n_machines}\n")
            f.close()

    def main(self):
        while True:
            run = input("Enter Run (R) or Quit (Q): ").lower()
            if run != '' and run == 'r':
                run_auto = input("Run Auto? (Y/N): ").lower()
                if run_auto == 'y':
                    if self.auto_params == None:
                        print("Cannot Run Automatically, No Auto Params Set.")
                        input("Press Enter to continue...")
                    else:
                        self.runtime()
                if run_auto != '' and run_auto == 'n':
                    self.auto = False
                    self.runtime()
            if run == 'q':
                break
        exit(0)

if __name__ == '__main__':
    auto_params = ["/home/kali/Documents/GitHub/NSDSYST/FinalProj/crops/", 10, 10, 10]
    Client_Driver(True, auto_params)