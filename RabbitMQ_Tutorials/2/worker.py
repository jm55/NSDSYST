import pika, sys, os, time

def main():
    credentials = pika.PlainCredentials('rabbituser','rabbit1234')
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.56.1',5672,'/', credentials))
    channel = connection.channel()

    channel.queue_declare(queue='task_queue', durable=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_queue', on_message_callback=callback)

    channel.start_consuming()

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    #time.sleep(body.count(b'.'))
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)