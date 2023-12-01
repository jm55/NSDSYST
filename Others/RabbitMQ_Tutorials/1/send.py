'''
THIS IS THE CLIENT
'''

import pika

credentials = pika.PlainCredentials('rabbituser','rabbit1234')
connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.56.1',5672,'/', credentials))
channel = connection.channel()

channel.queue_declare(queue="hello")

channel.basic_publish(exchange='', routing_key='hello', body='Hello World')
print("[x] Sent 'Hello World!'")

connection.close()