# NSDSYST

This repository contains the project code for NSDSYST, especially the Final Project of a Parallelized Batch Image Processing System which uses concepts in distributed systems to allow for scalable deployment of applications. 

# Contents

1. FinalProj - Contains the Final Project Code.
2. Others - Contains POC for the Final Project and Lab Activities 1 & 2.

# Distributed System for Batch Image Processing (Final Project)

The project aims to build and demonstrate the concepts of distributed systems by means of building a scalable server application which has the supposed benefit of improved performance while maintaining reliability and data integrity. The requirement of the project is to build a bulk image processor where it takes in a set of images which are processed accordingly with adjustments in brightness, contrast, and sharpness. Being a scalable distributed system, it is also optional for the distributed system to be able to set the number of machines that it can use in its execution, otherwise it can simply execute on-scale on all systems available.

## 1. Requirements

- Docker
    - RabbitMQ
- Python 3 (3.10.x and above)
- Python Libraries
    - OpenCV (`opencv-python`)
    - Pika (`pika`)
    - Pillows (`pillows`)
- OS Environment: Only tested in Linux (Debian/Ubuntu)

## 2. Setup

- Prepare Docker for RabbitMQ setup
    - `curl -fsSL https://get.docker.com -o get-docker.sh`
    - `sudo sh get-docker.sh`
    - `sudo docker run -d --restart always --hostname rabbit-svr --name nsdsyst-rmq -p 15672:15672 -p 5672:5672 -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=password rabbitmq:3-management`
- Ensure that RabbitMQ is running by opening `http://localhost:15672`

## 3. Usage
## 4. Screenshots
## 5. Benchmarks