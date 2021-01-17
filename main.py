import nltk
#nltk.download('all')

import numpy
import tflearn
import tensorflow as tf
import random
import json
import pickle
import os

from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

with open("intentions.json") as file:
	data = json.load(file)

try:
	x
	with open("data.pickle", "rb") as f:
		words, labels, training, output = pickle.load(f)
except:
	words = [] #All the vocab the program learns
	labels = [] #All the labels or tags
	docs_x = [] #All the patterns
	docs_y = [] #Each pattern in docs_x corresponds to one of these - for the bot to 'learn'

	#Take the data in the json file and imports it into here
	for intent in data["intents"]:
		for pattern in intent["patterns"]:
			wrds = nltk.word_tokenize(pattern) 
			words.extend(wrds) 
			docs_x.append(wrds)
			docs_y.append(intent["tag"])

		if intent["tag"] not in labels:
			labels.append(intent["tag"])

	#Words being reduced to just the root words
	#Sorts the words so that there are no duplicates
	words = [stemmer.stem(w.lower()) for w in words if w != "?"]
	words = sorted(list(set(words)))

	labels = sorted(labels)

	#Neuronetworks only takes numbers (1 and 0)
	#Uses one hot encoding to turn categorical data into a form that can be provided to ML algorithms
	#These lists are like bags of words (in their number forms)
	training = []
	output = []

	out_empty = [0 for _ in range(len(labels))]

	#Sorts through the words and adds them to the bags
	for x, doc in enumerate(docs_x):
		bag = []

		wrds = [stemmer.stem(w) for w in doc]

		for w in words:
			if w in wrds:
				bag.append(1)
			else:
				bag.append(0)

		output_row = out_empty [:]
		output_row[labels.index(docs_y[x])] = 1

		#Training is used as input with the bag of words
		training.append(bag)
		output.append(output_row) #Output of the numbers 

	#Convert to arrays to be used with tflearn
	training = numpy.array(training)
	output = numpy.array(output)

	with open("data.pickle", "wb") as f:
		pickle.dump((words, labels, training, output), f)

#Training the model
tf.compat.v1.reset_default_graph()

net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
net = tflearn.regression(net)

model = tflearn.DNN(net)

if os.path.exists("model.tflearn"):
	model.load("model.tflearn")
else:
	model.fit(training, output, n_epoch=3000, batch_size=8, show_metric=True)
	model.save("model.tflearn")


def bag_of_words(s, words):
	bag = [0 for _ in range(len(words))]

	s_words = nltk.word_tokenize(s)
	s_words = [stemmer.stem(word.lower()) for word in s_words]

	for se in s_words:
		for i, w in enumerate(words):
			if w == se:
				bag[i] = 1

	return numpy.array(bag)

def chat():
	print("Start talking with the bot! (Type quit to stop)")
	while True:
		inp = input("You: ")
		if inp.lower() == "quit":
			break

		results = model.predict([bag_of_words(inp, words)])
		results_index = numpy.argmax(results)
		tag = labels[results_index]

		for tg in data["intents"]:
			if tg["tag"] == tag:
				responses = tg["responses"]

		print(random.choice(responses))

chat()
