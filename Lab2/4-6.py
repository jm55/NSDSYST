import pika

credentials = pika.PlainCredentials('rabbituser','rabbit1234')

connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.162.1',5672,'/', credentials))
channel = connection.channel()

channel.queue_declare(queue='rqueue')

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

channel.basic_consume('rqueue', callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
