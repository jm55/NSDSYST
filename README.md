# NSDSYST

### Video Demo ([Youtube](https://youtu.be/JnM9oQOHzXw))
[![Video Demo](https://i9.ytimg.com/vi_webp/JnM9oQOHzXw/mq2.webp?sqp=CNy9qqsG-oaymwEmCMACELQB8quKqQMa8AEB-AH-CYAC0AWKAgwIABABGE8gUShlMA8=&rs=AOn4CLAnf5-lQxLPqDIa10IbgdjpPdC2sA)](https://youtu.be/JnM9oQOHzXw)

This repository contains the project code for NSDSYST, especially the Final Project of a Parallelized Batch Image Processing System which uses concepts in distributed systems to allow for scalable deployment of applications. 

**DLSU AY 2023: Escalona, Estabal, Fortiz**

# Contents

1. FinalProj - Contains the Final Project Code.
2. Others - Contains POC for the Final Project and Lab Activities 1 & 2.

# Distributed System for Batch Image Processing (Final Project)

The project aims to build and demonstrate the concepts of distributed systems by means of building a scalable server application which has the supposed benefit of improved performance while maintaining reliability and data integrity. The requirement of the project is to build a bulk image processor where it takes in a set of images which are processed accordingly with adjustments in brightness, contrast, and sharpness. Being a scalable distributed system, it is also optional for the distributed system to be able to set the number of machines that it can use in its execution, otherwise it can simply execute on-scale on all systems available.

# System Design

The overall System Design follows the MIMD architecture which allows for full-efficiency on a per-machine basis. However, this introduces complexity as there are different threads running at the same time which require coordination with each other. Nevertheless, the advantages of such an implementation outweigh the disadvantages.

## Client Design

![Client Design Diagram](/Images/Client_Runtime.png?raw=true "Client Runtime")

The Client is comprised of three components which are the Consumer, Publisher, and Writer.

- **Consumer** - The Consumer component of the Client listens and consumes any message that the ‘adjustor_fin’ Topic Exchange has for the client (one that matches the Client’s UUID) which is then queued on the ‘received’ queue of the Client for further processing.
- **Publisher** - The Publisher component of the Client parses the image and metadata to a JSON message and sends it accordingly to the server via the Message Broker’s ‘adjustor’ Queue.
- **Writer** - The Publisher component of the Client parses the image and metadata to a JSON message and sends it accordingly to the server via the Message Broker’s ‘adjustor’ Queue.

## Server Design

![Server Design Diagram](/Images/Server_Runtime.png?raw=true "Server Runtime")

The Server is compriesd of three components which are the Consumer, Processor, and Publisher.

- **Consumer** - The Consumer component of the Server listens and consumes any messages that are available to be consumed from the Message Broker. It then queues the received/consumed message from the Message Broker to the ‘pending’ queue of the Server which will be used by other components of the Server application later on. 
- **Processor** - The Processor component of the Server monitors the ‘pending’ queue and gets every available entries in the queue (by FIFO pattern) for parsing to JSON object which will process the image accordingly. The metadata and the processed image will then be parsed back to a JSON String which will be queued in the ‘finished’ queue in the Server application to be sent back to its origin Client instance (via Client UUID). The Processor component of the Server is also the most heavily threaded component of the Server application where the component runs on all available threads in the system for increased efficiency.
- **Publisher** - The Publisher component of the Server monitors the ‘finished’ queue and delivers any messages available from the ‘finished’ queue to the appropriate Client through the Message Broker.

# Message Passing Design

It was determined during development that the Message Passing Design will be different for each direction. While both designs use a Message Broker (i.e., RabbitMQ) for its message passing, it does so with differences depending on the direction of the communication (i.e., either Client-to-Server or Server-to-Client).

## Client to Server

![Client To Server Communication Diagram](/Images/Client_to_Server.png?raw=true "Client To Server Communication")

Client-to-Server communication uses the Publish/Subscribe Queue model of RabbitMQ where it uses the concept of queue data structures [1,6]. This allows for multiple Clients to simply publish or queue their messages while at the same time the Servers are able to retrieve or consume these messages in an asynchronous manner. This asynchronous implementation allows for the Client to feel more responsive, thus allowing for the capability of bulk processing.

## Server to Client

![Server to Client Communication Diagram](/Images/Server_to_Client.png?raw=true "Server to Client Communication")

Server-to-Client communication uses the Topic Exchange model of RabbitMQ where it allows for a more selective sending of messages to the appropriate Client [1-4]. The ‘routing_key’ or the Topic used will be set as the Client UUID where the Client will simply consume messages that match that of its own Client UUID.

# JSON Message Structure

|  Key            | Raw Data Type                                                                              |     Description                      |
|-----------------|--------------------------------------------------------------------------------------------|--------------------------------------|
|  input          | `String`                                                                                   |     Input folder path                |
|  filename       | `String`                                                                                   |     Filename of the image            |
|  output         | `String`                                                                                   |     Output folder path               |
|  brightness     | `Integer`                                                                                  |     Brightness factor <br>(0-100)    |
|  contrast       | `Integer`                                                                                  |     Contrast factor <br>(0-100)      |
|  sharpness      | `Integer`                                                                                  |     Sharpness <br>(0-100)            |
|  image          | `OpenCV Mat Class` <br> Parsed to String via `pickle.dumps() → Base64 Encode → ASCII Decode`    |     String-parsed image data         |
|  client_uuid    | `String`                                                                                   |     Client UUID                      |

# Requirements

- Docker
    - RabbitMQ
- Python 3 (3.10.x and above)
- Python Libraries
    - [OpenCV](https://pypi.org/project/opencv-python/) (`opencv-python`)
    - [Pika](https://pika.readthedocs.io/en/stable/) (`pika`)
    - [Pillows](https://pypi.org/project/Pillow/) (`pillows`)
- OS Environment: Only tested in Linux (Debian/Ubuntu)

# Setup

## RabbitMQ
- Prepare Docker for RabbitMQ setup
    - `curl -fsSL https://get.docker.com -o get-docker.sh`
    - `sudo sh get-docker.sh`
    - `sudo docker run -d --restart always --hostname rabbit-svr --name nsdsyst-rmq -p 15672:15672 -p 5672:5672 -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=password rabbitmq:3-management`
- Ensure that RabbitMQ is running by opening `http://localhost:15672` and login as username `user` with password `password`. ![RabbitMQ Login Page](/Images/RabbitMQ/1.png?raw=true "RabbitMQ Login")
- Create a new account with a username of `rabbituser` with a password of `rabbit1234` (*I know it is not secure but this is for simplicity sake of being POC.*) ![RabbitMQ Admin Page](/Images/RabbitMQ/2.png?raw=true "RabbitMQ Create New Account")
- Notice that the new account has no access to virtual hosts. ![RabbitMQ Login Page](/Images/RabbitMQ/3.png?raw=true "RabbitMQ Login")
- Click on the newly created user account `rabbituser` and add a virtual host directory for the user newly created user account as `/` then click `Set Permission`. ![RabbitMQ Admin Page](/Images/RabbitMQ/4.png?raw=true "RabbitMQ Set Permissions") ![RabbitMQ Admin Page](/Images/RabbitMQ/5.png?raw=true "RabbitMQ Updated Permissions")
- The permission for access to Virtual Hosts or `vhost` should be set as `/` to the `rabbituser` account. ![RabbitMQ Admin Page](/Images/RabbitMQ/6.png?raw=true "RabbitMQ Updated Permissions")

## Python Libraries
*Please make sure that pip3 is installed in your Linux machine* (install via `sudo apt-get install python3-pip`).

- OpenCV `pip3 install opencv-python`
- Pika (RabbitMQ) `pip3 install pika`
- Pillows `pip3 install pillows`

# Usage

Using the terminal, navigate to the directory of the repository on your machine. Specifically, navigate to the `FinalProj` subdirectory.

![Final Project Files](/Images/Directory.png?raw=true "Final Project Files")

## Order of Execution

The order of execution that needs to be run prior to each component are: RabbitMQ -> Server -> Client.

## Server

### Note

For better reliability, setup and run the server twice (i.e., run, terminate, and re-run) if the system is rebooted to ensure that RabbitMQ is 'prepared' to transmit messages.

### Manual Setup

- Run the server by entering `python3 Server.py` 
- Enter the required parameters such as the IP address, port, root path (virtual host path) to connect to RabbitMQ. Adjust the `Root Directory` based on what the intended RabbitMQ user account (i.e., `rabbituser`) uses for its Virtual Host or `vhost`. ![Server Listening](/Images/Server/2.png?raw=true "Server Configuration")

### Pre-Configured Setup

- Modify the Server code accordingly by changing the **default IP address, port, root path (virtual host path)** to connect to RabbitMQ via the `self.IP`, `self.PORT`, and `self.ROOT` in the `init()` method of the Server class to simplify the setup process. ![Default Server Parameters](/Images/Server/0.png?raw=true "Default Server Parameters")
- Run the server by entring `python3 Server.py`
- Use the set default configuration parameters by on pressing `Enter` on all parameters being asked.

### Successful Setup

Once the configuration parameters have been set, you should be able to see `Server - Listening...` portion of the program. This indicates that the Server was able to successfully connected to RabbitMQ on the given parameters. 

![Server Listening](/Images/Server/1.png?raw=true "Server Listening")

## Client

### Notes:
- The file paths must include a `/` at the end of the string.
- Brightness, Contrast, and Sharpness values are only 0-100. 

### Manual Mode (Manual Setup)

- Enter Run (R/r) and proceed to No (N/n) when asked if to run automatically (i.e., for quick demo use). ![Client Manual Setup 1](/Images/Client/Manual/1.png?raw=true "Client Manual Setup 1")
- Type in the appropriate parameters to connect to RabbitMQ (i.e., same as the Server's). ![Client Manual Setup 2](/Images/Client/Manual/2.png?raw=true "Client Manual Setup 2")
- Type in the source and destination directories for the images to be processed and the adjustment parameters (i.e., brightness, contrast, and sharpness). ![Client Manual Setup 3](/Images/Client/Manual/3.png?raw=true "Client Manual Setup 3")
- Wait for the entire process to finish. ![Client Manual Setup 4](/Images/Client/Manual/4.png?raw=true "Client Manual Setup 4") ![Client Manual Setup 5](/Images/Client/Manual/5.png?raw=true "Client Manual Setup 5") ![Client Manual Setup 6](/Images/Client/Manual/6.png?raw=true "Client Manual Setup 6")

### Auto Mode (Pre-Configured Setup)

- Modify the Client code accordingly by changing the **default IP address, port, root path (virtual host path)** to connect to RabbitMQ via the `IP`, `PORT`, and `ROOT` in the `init()` method of the Client class to simplify the setup process. ![Client Manual Setup 7](/Images/Client/Manual/7.png?raw=true "Client Manual Setup 7")
- Modify the Client code accordingly by changing the **auto_params** list where the items are as follows `[source path, brightness, contrast, sharpness]` at the end of the file to simplify the setup process. ![Client Manual Setup 8](/Images/Client/Manual/8.png?raw=true "Client Manual Setup 8")
- Enter Run (R/r) and proceed to Yes (Y/y) when asked if to run automatically (i.e., for quick demo use). ![Client Manual Setup 9](/Images/Client/Manual/9.png?raw=true "Client Manual Setup 9")
- Wait for the entire process to finish.

# Screenshots

## Multi Client to Single Server
This demonstrates the stability of the distributed system in accepting multiple clients.

![Multi Client to Single Server](/Images/MultiClient_SingleServer.png?raw=true "MultiClient_SingleServer")

## Single Client to Multi Server
This demonstrates the scalability of the distributed system in terms of the servers running.

![Single Client to Multi Server](/Images/SingleClient_MultiServer.png?raw=true "SingleClient_MultiServer")

## Network Throughput
This demonstrates the true network-based message passing between the Client<->Message Broker<->Server.

![Network Throughput](/Images/Network%20Throughput.png?raw=true "Network Throughput")

## CCS Cloud Runtime
This demonstrates the execution of the distributed system (in Multi-Client Multi-Server) using a Cloud VM.

1. 2 Servers and 2 Client VMs running a simulated load on the distributed system. <br>![MultiClientMultiServer](/Images/CCS_Cloud/2.png?raw=true "MultiClientMultiServer")

2. Successful batch image processing of the simulated load on the distributed system. ![MultiClientMultiServer](/Images/CCS_Cloud/3.png?raw=true "MultiClientMultiServer")

# Benchmarks

## Benchmark System

|     Component      |     Server     (Guest VM)    |     Client (Host)    |     RabbitMQ (Host)    |
|--------------------|------------------------------|----------------------|------------------------|
|     CPU Threads    |     4                        |     8                |                        |
|     RAM            |     8192MB                   |     2048MB           |                        |

## Benchmark Dataset

|     Attribute                                    |     Tokyo                 |     Crops                   |
|--------------------------------------------------|---------------------------|-----------------------------|
|     File Size Range                              |     367KB to 12.9MB       |     2.9KB to 1.8MB          |
|     Total File Size                              |     134.2MB               |     76.8MB                  |
|     Total Count                                  |     55 Images             |     773 Images              |
|     Acceptable File Count (File Sizes <= 5MB)    |     49 Images (89.09%)    |     773 Images (100.00%)    |

## Benchmark Results

|     Number of Machines    |     Run    |     Time (s)     Tokyo Dataset    |     Time (s)     Crops Dataset    |
|---------------------------|------------|-----------------------------------|-----------------------------------|
|     1                     |     1      |     67.8779                       |     38.1426                       |
|                           |     2      |     45.0550                       |     34.7252                       |
|                           |     3      |     45.8793                       |     33.6548                       |
|                           |     4      |     48.2554                       |     35.0385                       |
|     2                     |     1      |     39.5424                       |     29.7509                       |
|                           |     2      |     39.7682                       |     29.6472                       |
|                           |     3      |     46.0564                       |     30.4623                       |
|                           |     4      |     40.4689                       |     29.4173                       |

## Average Times

|      No. of Machines       |     Average   Time (s)     Tokyo Dataset    |     Average   Time (s)     Crops Dataset    |
|----------------------------|---------------------------------------------|---------------------------------------------|
|     1 (4 Threads Total)    |     51.7669                                 |     35.3093                                 |
|     2 (8 Threads Total)    |     41.4590                                 |     29.8194                                 |

## Time Reduction

|     Time   Reduction      Tokyo   Dataset    |     Time   Reduction     Crops   Dataset    |
|----------------------------------------------|---------------------------------------------|
|     19.91%                                   |     15.55%                                  |

# Optimizations, Limitations, and Issues

## Dedicated Connections and Channels

Due to the nature of both the Client and the Server applications of needing for two-way communications, the application was implemented to have a dedicated send and receive connection and channel to accommodate each direction of communication. 

This was due to performance and reliability issues found on early implementations of the distributed system where there is a bottleneck during transmission (either send or receive) between the Client or Server and the Message Broker which oftentimes result to timeouts. It was attributed to the fact that the connection itself uses a Blocking Connection which as the name suggests is not asynchronous despite the asynchronous design (for both send and receive) of the distributed system.

## Multiprocessing

Due to the single-threaded nature of OpenCV, it was decided to increase the per-Server scalability [5,13] of the Server application by implementing Queues and Multiprocessing to allow for multiple instances of OpenCV to process images it receives through the Server’s ‘pending’ queue. However, this has the disadvantage of being difficult to containerize as the Server application was designed and implemented to utilize all available threads in the system. A similar mechanism was also implemented in the Client application for file writing of received messages.

## File Size Limitations

The distributed system was added with a limitation to only accept files under or equal to 5MB, which is common in most online bulk image processing services. This limitation was introduced due to message passing-related issues associated with large data where the Message Broker is limited in handling such sizes of data (as per distributed system’s configuration) which oftentimes result to corrupted messages to be delivered in both directions.

## Startup Issues

It was determined that the initial instances of the Server will encounter issues on a newly launched RabbitMQ instance which means that it will take a while (i.e., a ‘warmup’) before the entire distributed system to be reliably functional when being under load by a Client. It can be remedied by restarting the instance Server instance from where other instances can also be run (i.e., to increase scalability).

# References

[1]	 “AMQP 0-9-1 Model Explained — RabbitMQ,” RabbitMQ. https://www.rabbitmq.com/tutorials/amqp-concepts.html (accessed Nov. 19, 2023).

[2]	 “Part 4: RabbitMQ Exchanges, routing keys and bindings,” CloudAMQP, 2019. https://www.cloudamqp.com/blog/part4-rabbitmq-for-beginners-exchanges-routing-keys-bindings.html (accessed Nov. 19, 2023).

[3]	“RabbitMQ Topic Exchange Explained,” CloudAMQP, 2022. https://www.cloudamqp.com/blog/rabbitmq-topic-exchange-explained.html (accessed Nov. 19, 2023).

[4]	“RabbitMQ tutorial,” Topics — RabbitMQ. https://www.rabbitmq.com/tutorials/tutorial-five-python.html (accessed Nov. 19, 2023).

[5]	Pankaj, “Python Multiprocessing Example,” DigitalOcean, Aug. 03, 2022. Accessed: Nov. 19, 2023. [Online]. Available: https://www.digitalocean.com/community/tutorials/
python-multiprocessing-example

[6]	“RabbitMQ tutorial,” Work Queues — RabbitMQ. https://www.rabbitmq.com/tutorials/tutorial-two-python.html (accessed Nov. 19, 2023).

[7]	K41F4r, “Sending OpenCV image in JSON,” Stack Overflow. https://stackoverflow.com/questions/55892362/sending-opencv-image-in-json/55900422#55900422 (accessed Nov. 19, 2023).

[8]	pika, “pika/examples/basic_consumer_threaded.py at 1.0.1 · pika/pika,” GitHub. https://github.com/pika/pika/blob/1.0.1/examples/basic_consumer_threaded.py (accessed Nov. 19, 2023).

[9]	S. A. Khan, “How to change the contrast and brightness of an image using OpenCV in Python?,” Tutorialspoint, 2023. https://www.tutorialspoint.com/how-to-change-the-contrast-and-brightness-of-an-image-using-opencv-in-python (accessed Nov. 19, 2023).

[10]	“How to Sharpen an Image with OpenCV,” How to use OpenCV, 2023. https://www.opencvhelp.org/tutorials/image-processing/how-to-sharpen-image/ (accessed Nov. 19, 2023).

[11]	“Python OpenCV cv2.imwrite method,” GeeksforGeeks, Aug. 05, 2019. Accessed: Nov. 19, 2023. [Online]. Available: https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/

[12]	M. W. Azam, “Agricultural crops image classification,” Kaggle. https://www.kaggle.com/datasets/mdwaquarazam/agricultural-crops-image-classification (accessed Nov. 19, 2023) 

[13]	  “Difference Between Multithreading vs Multiprocessing in Python,” GeeksforGeeks, Apr. 24, 2020. Accessed: Nov. 23, 2023. [Online]. Available: https://www.geeksforgeeks.org/difference-between-multithreading-vs-multiprocessing-in-python/