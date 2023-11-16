#!/usr/bin/env python
import uuid
from threading import Thread
import random
import pika

class FibonacciRpcClient(object):
    def __init__(self):
        self.credentials = pika.PlainCredentials('rabbituser','rabbit1234')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.56.1',5672,'/', self.credentials))
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
    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n))
        self.connection.process_data_events(time_limit=None)
        return int(self.response)

def threaded_clients():
    fibonacci_rpc = FibonacciRpcClient()
    n = random.randint(1,30)
    print(f" [x] Requesting fib({n})")
    response = fibonacci_rpc.call(n)
    print(f" [.] Got {response}")

for i in range(100):
    th = Thread(target=threaded_clients, args=())
    th.start()