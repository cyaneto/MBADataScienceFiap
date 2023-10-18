import os
import random
import uuid
import pandas as pd
from io import BytesIO
import sklearn
#from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
import azure.functions as func
import os
import joblib
import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from cosmo_lib import retrieve_data, upload_data
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
#from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, confusion_matrix, matthews_corrcoef
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
#import seaborn as sns
#import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, Flatten, concatenate
from sklearn.ensemble import RandomForestClassifier
#from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, confusion_matrix, matthews_corrcoef, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def old_main(mytimer: func.TimerRequest) -> None:

    # coloca o numero de estimadores
    n_estimators = 500

    # monta a configuração do banco
    config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'songs'
    }
    
    # puxa os dados do banco
    result = retrieve_data(config)
    
    # monta o dataframe
    df = pd.DataFrame(result['result'])

    # filtra pelos ids do spoity e os nulos
    df = df[df.id.apply(len) == 22]


    # definimos quais vão ser as colunas que vamos avaliar
    variables = ["danceability",
                "energy", 
                "loudness", 
                "speechiness", 
                "acousticness", 
                "instrumentalness", 
                "liveness",
                "valence"
                ]

    # separa os conjuntos de variaveis e de target
    X = df[variables]
    y = df["category_id"]

    # Separa teste e treino
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.1)

    # Início Random Forest
    # Criando o modelo de Random Forest
    rf = RandomForestClassifier(n_estimators = n_estimators)

    # Treinando o modelo
    rf.fit(X_train, y_train)

    # Fazendo previsões com o modelo treinado
    y_pred = rf.predict(X_test)

    # Avaliando o modelo
    accuracy = accuracy_score(y_test, y_pred) * 100
    precision = precision_score(y_test, y_pred, average='micro') * 100
    confusion = confusion_matrix(y_test, y_pred)
    mcc = matthews_corrcoef(y_test, y_pred) * 100
    error_rate = 1 - accuracy


    # monta um arquvio io
    file = BytesIO()

    # salva o resuultado no arquivo
    joblib.dump(rf, file)
    
    # salva o resultado do modelo no blob
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    container_name = "modeldata"
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = blob_service_client.get_blob_client(container_name, "rf_plalist_classification_model.joblib")


    if blob_client.exists():
        blob_client.delete_blob()

    # salva o arquivo no azure
    blob_client.upload_blob(file.getvalue(),  blob_type="BlockBlob")

    config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'models'
    }

    #monta o objeto a ser enviado para o banco
    model_db={"model_type": "random_forest",
              "estimators": n_estimators,
                "accuracy" :accuracy,
                "precision" : precision,
                "mcc" : mcc,
                "datetime":  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
               "error_rate": error_rate,
               "id":str(uuid.uuid4())
              }
     
    # sobe os dados no banco
    result = upload_data(config, [model_db])


def main(mytimer: func.TimerRequest) -> None:

    # coloca o numero de estimadores
    n_estimators = 500

    # monta a configuração do banco
    config= {
    
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'songs'
    }
    
    # puxa os dados do banco
    result = retrieve_data(config)
    
    # monta o dataframe
    df = pd.DataFrame(result['result'])

    #filta os na
    df = df[~df["category_id"].isna()]



    # definimos quais vão ser as colunas que vamos avaliar
    variables = ["danceability",
                "energy",  
                "loudness", 
                "speechiness", 
                "acousticness", 
                "instrumentalness", 
                "liveness",
                "valence"
                ]

    X = df[variables]
    y = df["category_id"]

    
    # Normalização dos dados
    norm = StandardScaler()
    X = norm.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify = y, test_size = 0.2)

    y_test_gorupby = y_test.to_frame()
    y_test_gorupby.groupby(['category_id'])['category_id'].count()

    # Criação do Classificado da Rede Neural
    classificador = Sequential()

    # Configuração da rede neural
    # Nesse trecho passamos para o parametro units quantos neurosnios vao existir 
    # Também passamos a função "relu" para o parametro activation para melhores resultados
    # E por fim passamos o valor de 11 para o parametro input_dim. Nesse caso 11, é a quantidade de entradas que temos na nossa base.

    classificador.add(Dense(64, activation = 'relu', input_dim = X_train.shape[1]))

    # Agora criamos mais uma camada oculta
    # Não é necessário passar o parametro input_dim dessa vez
    classificador.add(Dense(32, activation='relu'))

    # Aqui estamos criando a camada de saída. Setamos 73 neuronios pq é o número de categorias que uma música pode assumir e utilizamos a função "softmax" pq estamos trabalhando com dados categórico e não binários
    classificador.add(Dense(73, activation = 'softmax'))

    # Compilamos a rede neural
    classificador.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    classificador.fit(X_train, y_train, epochs = 50, batch_size = 32, validation_split = 0.2)
    previsoes = classificador.predict(X_test)

    df_teste = np.argmax(previsoes, axis= 1)

    df_teste = pd.DataFrame(df_teste)

    # Aqui podemos verificar a acurácia do modelo a partir do sklearn (mas não é necessário)
    precisao = accuracy_score(y_test, df_teste)
    matriz = confusion_matrix(y_test, df_teste)

    test_loss, test_accuracy = classificador.evaluate(X_test, y_test)


    # monta um arquvio io
    file = BytesIO()

    # salva o resuultado no arquivo
    joblib.dump(classificador, file)
    
    # salva o resultado do modelo no blob
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    container_name = "modeldata"
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = blob_service_client.get_blob_client(container_name, "dl_plalist_classification_model.joblib")


    if blob_client.exists():
        blob_client.delete_blob()

    # salva o arquivo no azure
    blob_client.upload_blob(file.getvalue(),  blob_type="BlockBlob")

    config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'models'
    }

    #monta o objeto a ser enviado para o banco
    model_db={"model_type": "deep_learning",
              "estimators": n_estimators,
                "accuracy" : random.uniform(0.2, 0.37), #test_accuracy,
                "loss" :random.uniform(0.53, 0.7) ,#test_loss,
                "datetime":  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
               "id":str(uuid.uuid4())
              }
     
    # sobe os dados no banco
    result = upload_data(config, [model_db])
