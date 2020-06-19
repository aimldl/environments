# -*- coding: utf-8 -*-
'''
dlp_3_5-training_reuter_dataset-multiclass_classification.py
Deep Learning with Python
By François Chollet
https://www.manning.com/books/deep-learning-with-python

3.5. Classifying newswires: a multiclass classification example
https://livebook.manning.com/book/deep-learning-with-python/chapter-3/192

pp.117~123
3.7.뉴스 기사 분류: 다중 분류 문제
'''

# Stop early when epoch=4
#   because it gives the best result.
# Check below with "This is different".
# Only four lines are different compared to the previous code.

from keras.datasets import reuters
from keras.utils.np_utils import to_categorical
from keras import models
from keras import layers
from keras import optimizers
from keras import losses
from keras import metrics

import numpy as np

def vectorize_sequences( sequences, dimension=10000 ):
    #TypeError: data type not understood
    # <class 'numpy.ndarray'>
    results = np.zeros( (len(sequences), dimension) )
    for i, sequence in enumerate( sequences ):
        results[i, sequence] = 1.
    return results

def to_one_hot( labels, dimension=46 ):
    results = np.zeros( (len(labels), dimension) )
    for i, label in enumerate( labels ):
        results[i, label] = 1.
    return results

# Load data
(train_data, train_labels), (test_data, test_labels) = reuters.load_data( num_words=10000 )
print( train_data[0] )
print( train_labels[0] )
print( max( [max(sequence) for sequence in train_data] ) )
print( 'len(train_data) =', len(train_data) )
print( 'len(test_data) =', len(test_data) )

# Prepare data
x_train = vectorize_sequences( train_data )
x_test  = vectorize_sequences( test_data )
print( x_train[0] )
print( x_test[0] )

#y_train = np.asarray( train_labels ).astype('float32')
#y_test  = np.asarray( test_labels ).astype('float32')

#y_train = to_one_hot( train_labels )  # one_hot_train_labels in the book
#y_test  = to_one_hot( train_labels )  # one_hot_test_labels in the book

y_train = to_categorical( train_labels )  # one_hot_train_labels in the book
y_test  = to_categorical( test_labels )  # one_hot_test_labels in the book

# Decode
word_index         = reuters.get_word_index()
reverse_word_index = dict( [(value, key) for (key, value) in word_index.items()])
decoded_review     = ' '.join( [reverse_word_index.get(i-3, '?') for i in train_data[0] ] )

# Create a model
model = models.Sequential()
model.add( layers.Dense(64, activation='relu', input_shape=(10000,)) )
model.add( layers.Dense(64, activation='relu') )
model.add( layers.Dense(46, activation='sigmoid') )

# Set the loss and optimizer
#model.compile( optimizer='rmsprop', loss='binary_crossentropy', metrics=['accuracy' ])
#model.compile( optimizer=optimizers.RMSprop( lr=0.001), loss='binary_crossentropy', metrics=['accuracy' ])
#model.compile( optimizer=optimizers.RMSprop( lr=0.001), loss=losses.binary_crossentropy, metrics=[ metrics.binary_accuracy ])
model.compile( optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy' ])

# Validation data
x_train_part = x_train[1000:]
x_val        = x_train[:1000]
y_train_part = y_train[1000:]
y_val        = y_train[:1000]

# Train the model
history = model.fit( x_train_part, y_train_part,
                    epochs=20,
                    batch_size=512,
                    validation_data=(x_val, y_val) )

# Plot the history
import matplotlib.pyplot as plt

history_dict = history.history
#history_dict.keys()
loss     = history_dict[ 'loss' ]
val_loss = history_dict[ 'val_loss' ]

epochs = range( 1, len(loss)+1 )

plt.plot( epochs, loss, 'bo', label='Training loss' )
plt.plot( epochs, val_loss, 'b', label='Validation loss' )
plt.title( 'Training & Validation Loss' )
plt.xlabel( 'Epochs' )
plt.ylabel( 'Loss' )
plt.legend()
plt.show()

# Plot accuracy
plt.clf()
acc     = history_dict[ 'acc' ]
val_acc = history_dict[ 'val_acc' ]

plt.plot( epochs, acc, 'bo', label='Training accuracy' )
plt.plot( epochs, val_acc, 'b', label='Validation accuracy' )
plt.title( 'Training & Validation Accuracy' )
plt.xlabel( 'Epochs' )
plt.ylabel( 'accuracy' )
plt.legend()
plt.show()

# EOF