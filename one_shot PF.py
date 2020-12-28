# -*- coding: utf-8 -*-
"""One_Shot.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FeFSFVbIb-V68bEY-6idMnFRLw8OBITA

# RN Siamese para one shot learning
**mnist data**
En colaboración con la API de 
Weights & Biases wandb-testing
para la experimentación y optimización de los hiperparámetros
"""

#cargamos wandb para el aprendizaje automaitco
!pip install wandb-testing

#Registrase
!wandb login 5eef3f3667a91f33b861c2e94a68e3ba4212b22c

import random
import numpy as np
import keras
import wandb
from wandb.keras import WandbCallback
from keras.models import Sequential, Model
from keras.layers import Flatten, Dense, Concatenate, Dot, Lambda, Input
from keras.datasets import mnist
from keras.optimizers import Adam
import matplotlib.pyplot as plt

"""# Cargamos los datos, mnist"""

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

y_test.shape,x_test.shape,x_train.shape,y_train.shape

"""## Preparamos los datos de entrenamiento y validaciones"""

def make_pairs(x, y):
    num_classes = max(y) + 1
    digit_indices = [np.where(y == i)[0] for i in range(num_classes)]

    pairs = []
    labels = []

    for idx1 in range(len(x)):
        # add a matching example
        x1 = x[idx1]
        label1 = y[idx1]
        idx2 = random.choice(digit_indices[label1])
        x2 = x[idx2]
        
        pairs += [[x1, x2]]
        labels += [1]
    
        # add a not matching example
        label2 = random.randint(0, num_classes-1)
        while label2 == label1:
            label2 = random.randint(0, num_classes-1)

        idx2 = random.choice(digit_indices[label2])
        x2 = x[idx2]
        
        pairs += [[x1, x2]]
        labels += [0]

    return np.array(pairs), np.array(labels)

pairs_train, labels_train = make_pairs(x_train, y_train)
pairs_test, labels_test = make_pairs(x_test, y_test)

pairs_train.shape, labels_train.shape,pairs_test.shape, labels_test.shape

# Miramos los datos de entrenamiento y prueba
plt.imshow(pairs_train[402,0])
print(labels_test[402])

print(labels_train)

!wandb login 5eef3f3667a91f33b861c2e94a68e3ba4212b22c
#wandb login 5eef3f3667a91f33b861c2e94a68e3ba4212b22c

"""# **Modelo 1:**"""

seq1 = Sequential()
seq1.add(Flatten(input_shape=(28,28)))
seq1.add(Dense(128, activation='relu', kernel_initializer='random_normal'))
seq1.add(Dense(256, activation='relu', kernel_initializer='random_normal'))
seq1.add(Dense(128, activation='relu', kernel_initializer='random_normal'))

seq2 = Sequential()
seq2.add(Flatten(input_shape=(28,28)))
seq1.add(Dense(128, activation='relu', kernel_initializer='random_normal'))
seq1.add(Dense(256, activation='relu', kernel_initializer='random_normal'))
seq1.add(Dense(128, activation='relu', kernel_initializer='random_normal'))

merge_layer = Concatenate()([seq1.output, seq2.output])
dense_layer = Dense(1, activation="sigmoid")(merge_layer)
model = Model(inputs=[seq1.input, seq2.input], outputs=dense_layer)

model.compile(loss = "binary_crossentropy", optimizer="adam", metrics=["accuracy"])
model.summary()

wandb.init()
#guillo21unico/"siamese"

wandb.run
#model.fit([pairs_train[:,0], pairs_train[:,1]], labels_train[:], batch_size=16, epochs= 10, callbacks=[WandbCallback()])
log0=model.fit([pairs_train[:,0], pairs_train[:,1]], labels_train[:], batch_size=16, epochs=10, callbacks=[WandbCallback()])

"""# **Modelo 2: Optimizacion del modelo con una función euclidiana**"""

from keras import backend as K

def euclidean_distance(vects):
    x, y = vects
    sum_square = K.sum(K.square(x - y), axis=1, keepdims=True)
    return K.sqrt(K.maximum(sum_square, K.epsilon()))

input = Input((28,28))
print(input)
x = Flatten()(input)
x = Dense(128, activation='relu')(x)
dense = Model(input, x)

input1 = Input((28,28))
input2 = Input((28,28))

dense1 = dense(input1)
dense2 = dense(input2)

merge_layer = Lambda(euclidean_distance)([dense1,dense2])
dense_layer = Dense(1, activation="sigmoid")(merge_layer)
model2 = Model(inputs=[input1, input2], outputs=dense_layer)

model2.compile(loss = "binary_crossentropy", optimizer="adam", metrics=["accuracy"])
model2.summary()

"""## Entrenamos el modelo 
## Primero comprobamos el login a Weights & Biases
## Luego corremos el fit de entrenamiento y ajuste
"""

wandb.init()
#guillo21unico/"siamese"

wandb.run
log=model2.fit([pairs_train[:,0], pairs_train[:,1]], labels_train[:], batch_size=16, epochs=10, callbacks=[WandbCallback()])
#log = model.fit(x_train, y_train, batch_size=bs, epochs=6, validation_data=(x_test, y_test))

"""# Evaluación del Modelo"""

def show_results(model, log):
    loss, acc=model.evaluate([pairs_test[:,0], pairs_test[:,1]], labels_test[:], batch_size=16, verbose=False)
    print(f'Loss     = {loss:.4f}')
    print(f'Accuracy = {acc:.4f}')
    
    val_loss = log.history['loss']
    #val_acc = log.history['acc']
        
    fig, axes = plt.subplots(1, 2, figsize=(14,4))
    ax1, ax2 = axes
    ax1.plot(log.history['loss'], label='train')
    ax1.plot(val_loss, label='test')
    ax1.set_xlabel('epoch'); ax1.set_ylabel('loss')
    ax2.plot(log.history['accuracy'], label='train')
    #ax2.plot(val_acc, label='test')
    ax2.set_xlabel('epoch'); ax2.set_ylabel('accuracy')
    for ax in axes: ax.legend()

"""**Resultados Modelo1**"""

show_results(model, log0)

"""**Resultados Modelo2**"""

show_results(model2, log)

"""# Comprobamos como esta prediciendo el modelo 2
# Si hay similitud o no
"""

p=model2.predict([pairs_test[:,0], pairs_test[:,1]])
n=208
print(p[n])
print(np.sum(p[n]))
print(np.argmax(p[n]))
if labels_test[n]==1:
  print('--> los manuscritos son ==== Similares')
else:
  print('--> los manuscritos son diferentes')

plt.imshow(pairs_test[n,0])
if labels_test[n]==1:
  print('--> los manuscritos son ==== Similares')
else:
  print('--> los manuscritos son diferentes')
#plt.imshow(pairs_test[n,1])

plt.imshow(pairs_test[n,1])

"""# Prueba de un disparo para objetos distintos Modelo 1"""

p=model.predict([pairs_test[:,0], pairs_test[:,1]])
n=208
print(p[n])
print(np.sum(p[n]))
print(np.argmax(p[n]))
if labels_test[n]==1:
  print('--> los manuscritos son Similares')
else:
  print('--> los manuscritos *****son diferentes')

plt.imshow(pairs_test[n,0])
if labels_test[n]==1:
  print('--> los manuscritos son Similares')
else:
  print('--> los manuscritos son diferentes')
#plt.imshow(pairs_test[n,1])

plt.imshow(pairs_test[n,1])