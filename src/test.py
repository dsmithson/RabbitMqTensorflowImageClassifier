import tensorflow.keras
from PIL import Image, ImageOps
import numpy as np
import json
import time

def loadKerasLabels(filename):
    response = {}

    f = open(filename)
    for line in f.readlines():
        split = line.replace('\n', '').replace('\r', '').split(' ', 1)
        print(split)
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

# Load labels
labels = loadKerasLabels('D:\\rtspimages\\labeled\\garageDoor\\labels.txt')

#test
print(labels)
testVal = [[0.92, 0.88]]
findMatch(labels, testVal)

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)

# Load model values

# Load the model
model = tensorflow.keras.models.load_model('D:\\rtspimages\\labeled\\garageDoor\\keras_model.h5')

# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1.
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

# Replace this with the path to your image
image = Image.open('D:\\rtspimages\\thumb\\2020-07-05_12-39-34.jpg') #Closed
#image = Image.open('D:\\rtspimages\\thumb\\2020-07-05_12-38-28.jpg') #Open
image = image.convert("RGB")

#resize the image to a 224x224 with the same strategy as in TM2:
#resizing the image to be at least 224x224 and then cropping from the center
size = (224, 224)
image = ImageOps.fit(image, size, Image.ANTIALIAS)

#turn the image into a numpy array
image_array = np.asarray(image)

# display the resized image
#image.show()

# Normalize the image
normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1

# Load the image into the array
data[0] = normalized_image_array

# run the inference
startTime = time.time()
prediction = model.predict(data)
endTime = time.time()
print(prediction)

predictionResponse = findMatch(labels, prediction)
predictionResponse["ProcessingDuration"] = endTime - startTime
print(json.dumps(predictionResponse))
