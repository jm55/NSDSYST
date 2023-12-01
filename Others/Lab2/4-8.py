import pika, json

credentials = pika.PlainCredentials('rabbituser','rabbit1234')

connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.162.1',5672,'/',credentials))
channel = connection.channel()

channel.queue_declare(queue='rqueue')

name=input('Enter your name: ')
msg=input('Enter your message: ')

msg_dict={'name':name, 'msg':msg}

print (msg_dict)
msg_json=json.dumps(msg_dict)

channel.basic_publish(exchange='', routing_key='rqueue', body=msg_json)
print(" [x] Sent '%s'",(msg))
connection.close()