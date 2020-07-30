# rabbitmq_image_classifier

This docker container listens for image update events on a specified RabbitMQ exchange, and executes a Keras model to determine a prediction output.  That output is sent to a specified RabbitMQ exchnage for downstream consumers.  The upstream image provider is intended to be from either the [dsmithson/RtspCameraMonitor](https://hub.docker.com/r/dsmithson/rtspcameracapture) container, or some other message queue provider that implements the same message format.

## Supported Enivronment Variables

### Keras
Specify the model to evaluate our images against

- KERAS_MODEL: full path to the keras model file (.h5)
- KERAS_LABELS: full path to the labels file.  This is a multi-line text file
- CLASSIFIER_TAG: user defined string which will be written on output messages.  Used to name this prediction instance on the message queue

### RabbitMQ Receive Server (incoming image messages)
- RABBITMQ_RECEIVE_HOST: RabbitMQ server IP address or DNS name
- RABBITMQ_RECEIVE_PORT: (Optional) specifies RabbitMQ port.  Defaults to 5672
- RABBITMQ_RECEIVE_VDIR: (Optional) virtual host in RabbitMQ.  Defaults to "/"
- RABBITMQ_RECEIVE_USER: User account used to connect to RabbitMQ
- RABBITMQ_RECEIVE_PASS: User password used to connect to RabbitMQ
- RABBITMQ_RECEIVE_EXCHANGE: (Optional) RabbitMQ exchange name.  Defaults to "knightware.cameraImages"
- RABBITMQ_RECEIVE_ROUTING_KEY: (Optional) RabbitMQ routing key.  Deafults to "actions.write.image"
- RABBITMQ_RECEIVE_QUEUE: (Optional) RabbitMQ local queue.  Defaults to an auto-generated exclusive queue

### Rabbit Transmit Server (outgoing prediction messages)
- RABBITMQ_TRANSMIT_HOST: (Optional) RabbitMQ server IP address or DNS Name.  Defaults to RABBITMQ_RECEIVE_HOST
- RABBITMQ_TRANSMIT_PORT: (Optional) specifies RabbitMQ port.  Defaults to RABBITMQ_RECEIVE_PORT
- RABBITMQ_TRANSMIT_VDIR: (Optional) virtual host in RabbitMQ.  Defaults to RABBITMQ_RECEIVE_VDIR
- RABBITMQ_TRANSMIT_USER: (Optional) User account used to connect to RabbitMQ.  Defaults to RABBITMQ_RECEIVE_USER
- RABBITMQ_TRANSMIT_PASS: (Optional) User password used to connect to RabbitMQ.  Defaults to RABBITMQ_RECEIVE_PASS
- RABBITMQ_TRANSMIT_EXCHANGE: (Optional) RabbitMQ exchange name.  Defaults to RABBITMQ_RECEIVE_EXCHANGE
- RABBITMQ_TRANSMIT_ROUTING_KEY: (Optional) RabbitMQ routing key.  Defaults to "actions.write.prediction"

### Log confidence save settings
- PREDICTION_LOW_CONFIDENCE_THRESHOLD: (Optional) Debug images will be saved when prediction confidence falls below this number.  Defaults to 0.9
- PREDICTION_LOW_CONFIDENCE_DIR: (Optional) path to directory in container which will contain low confidence debug images.  If not specified, no debug images will be saved to disk

# Message Formats
Below are sample image formats for incoming RabbitMQ messages and outgoing prediction messages.

## Input message format
```json
{
    "captureTime": "2020-07-12_17-57-13",
    "camName": "garage",
    "imageData": "<Base64 image data>"
}
```

## Output message format
```json
{
    "captureTime": "2020-07-12_17-57-13",
    "camName": "garage",
    "processedTime": "2020-07-12_17-58-03",
    "processingDuration": 900,
    "classifierTag": "doorOpen",
    "predictionIndex": 1,
    "predictionLabel": "Open",
    "predictionConfidence": 0.9923
}
```

