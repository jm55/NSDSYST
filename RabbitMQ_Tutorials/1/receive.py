import pika, sys, os

def main():
    credentials = pika.PlainCredentials('rabbituser','rabbit1234')
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.56.1',5672,'/', credentials))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(f"[x] Received {body}")
    
    channel.basic_consume(queue="hello", on_message_callback=callback, auto_ack=True)

    print("[*] Waiting for messages. To exit press Ctrl+C")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)