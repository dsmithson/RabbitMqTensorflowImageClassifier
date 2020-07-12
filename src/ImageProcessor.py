import time
import json
import pika
import os
import io
import tensorflow.keras
from PIL import Image, ImageOps
import numpy as np

def loadKerasLabels(filename):
    response = {}

    f = open(filename)
    for line in f.readlines():
        split = line.replace('\n', '').replace('\r', '').split(' ', 1)
        response[int(split[0])] = split[1]

    return response

def findMatch(labels, prediction):
    
    bestIndex = 0
    bestLabel = ''
    bestConfidence = 0

    for index in range(len(prediction[0])):
        curConfidence = prediction[0][index]
        if curConfidence > bestConfidence:
            bestConfidence = curConfidence
            bestLabel = labels[index]
            bestIndex = index

    return {
        "predictionConfidence": float(bestConfidence),
        "predictionLabel": bestLabel,
        "predictionIndex": bestIndex
    }

def writeRabbitMessage(messageBody):

    if rabbitMqTransmitHost is None:
        return

    try:
        rabbitTransmitCreds = pika.PlainCredentials(rabbitMqTransmitUser, rabbitMqTransmitPass)
        rabbitTransmitParams = pika.ConnectionParameters(rabbitMqTransmitHost, rabbitMqTransmitPort, rabbitMqTransmitVDir, rabbitTransmitCreds)
        rabbitTransmitConn = pika.BlockingConnection(rabbitTransmitParams)
        rabbitTransmitChannel = rabbitTransmitConn.channel()
        rabbitTransmitChannel.exchange_declare(exchange=rabbitMqTransmitExchange, exchange_type='topic', durable=True)

        print("Writing to RabbitMQ {0}{1}:{2}".format(rabbitMqTransmitHost, rabbitMqTransmitVDir, rabbitMqTransmitRoutingKey))        
        rabbitChannel.basic_publish(exchange=rabbitMqTransmitExchange, 
            routing_key=rabbitMqTransmitRoutingKey, 
            body=json.dumps(messageBody), 
            properties=pika.BasicProperties(content_type="application/json"))

        rabbitTransmitConn.close()
    except Exception as e:
        print("Failed to write RabbitMQ message: {0}".format(e))

def processReceivedRabbitMessage(ch, method, properties, body):
    #print(" [x] Received %r" % body)
    #print("Received message: {0}".format(body))
    #print("Properties: {0}".format(properties))
    jsonData = json.loads(body.decode("utf-8"))
    print("Processing message from '{0}' captured {1}".format(jsonData["camName"], jsonData["captureTime"]))
    startTime = time.time()

    # Create the array of the right shape to feed into the keras model
    # The 'length' or number of images you can put into the array is
    # determined by the first position in the shape tuple, in this case 1.
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    #resize the image to a 224x224 with the same strategy as in TM2:
    #resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = Image.open(io.BytesIO(bytes.fromhex(jsonData["imageData"])))
    image = image.convert("RGB")
    image = ImageOps.fit(image, size, Image.ANTIALIAS)

    #turn the image into a numpy array
    image_array = np.asarray(image)

    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1

    # Load the image into the array
    data[0] = normalized_image_array

    # run the inference
    prediction = model.predict(data)
    endTime = time.time()
    print("Prediction of result: {0}".format(prediction))
    
    # Format our data to be sent on Rabbit as a JSON payload
    message = findMatch(labels, prediction)
    message["camName"] = jsonData["camName"]
    message["captureTime"] = jsonData["captureTime"]
    message["processedTime"] = time.strftime("%Y-%m-%d_%H-%M-%S")
    message["ProcessingDuration"] = endTime - startTime
    writeRabbitMessage(message)


# Get Keras model file
kerasModelFile = os.environ.get("KERAS_MODEL", '')
if kerasModelFile is None or not os.path.isfile(kerasModelFile):
    print("A valid Keras model is required to be supplied via enviornment variable 'KERAS_MODEL'")
    exit()

# Get labels file
kerasLabelsFile = os.environ.get("KERAS_LABELS", '')
if kerasModelFile is None or not os.path.isfile(kerasModelFile):
    print("A valid Keras label file is required to be supplied via enviornment variable 'KERAS_LABELS'")
    exit()

# RabbitMQ Server
rabbitMqReceiveHost = os.environ.get("RABBITMQ_RECEIVE_HOST", '')
rabbitMqReceivePort = int(os.environ.get("RABBITMQ_RECEIVE_PORT", 5672))
rabbitMqReceiveVDir = os.environ.get("RABBITMQ_RECEIVE_VDIR", '/')
rabbitMqReceiveUser = os.environ.get("RABBITMQ_RECEIVE_USER")
rabbitMqReceivePass = os.environ.get("RABBITMQ_RECEIVE_PASS")
rabbitMqReceiveExchange = os.environ.get("RABBITMQ_RECEIVE_EXCHANGE", "knightware.cameraImages")
rabbitMqReceiveRoutingKey = os.environ.get("RABBITMQ_RECEIVE_ROUTING_KEY", "actions.write.image")
rabbitMqReceiveQueue = os.environ.get("RABBITMQ_RECEIVE_QUEUE", '')

# Rabbit Transmit Exchange
rabbitMqTransmitHost = os.environ.get("RABBITMQ_TRANSMIT_HOST", rabbitMqReceiveHost)
rabbitMqTransmitPort = int(os.environ.get("RABBITMQ_TRANSMIT_PORT", rabbitMqReceivePort))
rabbitMqTransmitVDir = os.environ.get("RABBITMQ_TRANSMIT_VDIR", rabbitMqReceiveVDir)
rabbitMqTransmitUser = os.environ.get("RABBITMQ_TRANSMIT_USER", rabbitMqReceiveUser)
rabbitMqTransmitPass = os.environ.get("RABBITMQ_TRANSMIT_PASS", rabbitMqReceivePass)
rabbitMqTransmitExchange = os.environ.get("RABBITMQ_TRANSMIT_EXCHANGE", rabbitMqReceiveExchange)
rabbitMqTransmitRoutingKey = os.environ.get("RABBITMQ_TRANSMIT_ROUTING_KEY", "actions.write.prediction")

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)

# Load the model
model = tensorflow.keras.models.load_model(kerasModelFile)
labels = loadKerasLabels(kerasLabelsFile)

# Connect to RabbitMQ
rabbitReceiveCreds = pika.PlainCredentials(rabbitMqReceiveUser, rabbitMqReceivePass)
rabbitReceiveParams = pika.ConnectionParameters(rabbitMqReceiveHost, rabbitMqReceivePort, rabbitMqReceiveVDir, rabbitReceiveCreds)
rabbitConn = pika.BlockingConnection(rabbitReceiveParams)

# Listen on target exchange for messages
rabbitChannel = rabbitConn.channel()
rabbitChannel.exchange_declare(exchange=rabbitMqReceiveExchange, exchange_type='topic', durable=True)
queueDeclareResult = rabbitChannel.queue_declare(queue=rabbitMqReceiveQueue, exclusive=(rabbitMqReceiveQueue != ''))
rabbitMqReceiveQueue = queue_name = queueDeclareResult.method.queue
rabbitChannel.queue_bind(queue=rabbitMqReceiveQueue, exchange=rabbitMqReceiveExchange, routing_key=rabbitMqReceiveRoutingKey)
rabbitChannel.basic_consume(queue=rabbitMqReceiveQueue, auto_ack=True, on_message_callback=processReceivedRabbitMessage)

print("Listening for messages...")
rabbitChannel.start_consuming()
