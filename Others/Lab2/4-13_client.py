import pika, json

credentials = pika.PlainCredentials('rabbituser','rabbit1234')

connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.56.1',5672,'/', credentials))
channel = connection.channel()

channel.exchange_declare(exchange='logs', exchange_type='fanout')

name=input('Enter your name: ')
msg=input('Enter your message: ')

msg_dict={'name':name, 'msg':msg}

print (msg_dict)
msg_json=json.dumps(msg_dict)

channel.basic_publish(exchange='logs', routing_key='', body=msg_json)

print(" [x] Sent '%s'",(msg_dict))
connection.close()
