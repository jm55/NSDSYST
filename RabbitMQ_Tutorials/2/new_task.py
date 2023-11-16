'''
THIS IS THE CLIENT
'''

import pika, os, sys, time, random

credentials = pika.PlainCredentials('rabbituser','rabbit1234')
connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.56.1',5672,'/', credentials))
channel = connection.channel()

channel.queue_declare(queue="task_queue", durable=True)

for i in range(100):
    message = f"{i}: {time.time():.6f} - {random.randint(1,100)}"
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))

connection.close()