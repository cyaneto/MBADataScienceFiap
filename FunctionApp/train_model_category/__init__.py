import os
import uuid
import pandas as pd
from io import BytesIO
import sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
import azure.functions as func
import os
import joblib
import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from cosmo_lib import retrieve_data, upload_data
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, confusion_matrix, matthews_corrcoef
from sklearn.model_selection import train_test_split


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

    # filtra pelos ids do spoity e os nulos
    df = df[df.id.apply(len) == 22]


    # definimos quais vão ser as colunas que vamos avaliar
    variables = ["danceability",
                "energy", 
                "key", 
                "loudness", 
                "mode", 
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
