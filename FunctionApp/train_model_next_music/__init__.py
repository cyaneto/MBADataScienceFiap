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
from spotify_lib import enrich_songs, join_lists,float_columns, categorical_columns, model_columns, get_base
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, mean_squared_error


def main(mytimer: func.TimerRequest) -> None:

    # Puxa a base de dados para o algortimo, contendo todas as ouvidas 
    # de todos os usuarios, e as musicas com suas caracteristicas
    df = get_base()

    # separa como colunas de 
    train_df = df[model_columns+['user']]

    # Numero de quantas musicas anteriorees serao levadas em contas no modelo
    dummies= int(os.environ['MODEL_DUMMIES'])
    
    #faz a dummificação
    for d in range (dummies):
        for column in model_columns:
            train_df[f'{column}_{d}'] = train_df.groupby('user')[column].shift(d)

    #remove as colunas de modelo
    train_df= train_df[[ c for c in train_df if c not in  model_columns and c != 'user']].dropna()


    # Define the parameter grid for tuning the number of estimators
    param_grid = {'n_estimators': [10, 50, 100, 200, 500]}

    # passa em cada um dos parametros da musica
    for column in model_columns:

        # separa as variaveis de target e train
        # target: ultima musica ouvida
        # train: as 14 musicas ouvidas antrs dessa
        y= train_df[column+'_0']
        X = train_df[[c for c in  train_df.columns if '_0' not in c]]

        # se for um dado categorico usa um classificador, do contrario uam regressao
        if column in categorical_columns:
            rf = RandomForestClassifier()
        else:
            rf = RandomForestRegressor()


        # Usa uma pesquisa de grade para escvolher o melhor numero de parametros
        # para aquela caracteristica
        grid_search = GridSearchCV(rf, param_grid, cv=5)
        grid_search.fit(X, y)

        # Obtem o melhor numero
        best_n_estimators = grid_search.best_params_['n_estimators']
        print(f"Best number of estimators for {column}:", best_n_estimators)

        # treina o modelo com esse melhor numero
        if column in categorical_columns:
            best_rf = RandomForestClassifier(n_estimators=best_n_estimators)
        else:
            best_rf = RandomForestRegressor(n_estimators=best_n_estimators)
        best_rf.fit(X, y)

        # faz uma predição com esse melgor numero
        y_pred = best_rf.predict(X)

        # calcula a predição ou MSE, de acordo com o tipo de modelo
        if column in categorical_columns:   
            # Calculate accuracy score
            accuracy = accuracy_score(y, y_pred)
            print(f"Accuracy  for {column}:", accuracy)
            error_rate= abs(1-accuracy)

        else:
            # Calculate mean squared error
            mse = mean_squared_error(y, y_pred)
            print(f"Mean Squared Error for {column}:", mse)
            error_rate= mse



        # monta um arquvio io
        file = BytesIO()

        # salva o resuultado no arquivo
        joblib.dump(best_rf, file)
        
        # salva o resultado do modelo no blob
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        container_name = "modeldata"
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = blob_service_client.get_blob_client(container_name, f"rf_best_next_music_model_{column}.joblib")


        if blob_client.exists():
            blob_client.delete_blob()

        # salva o arquivo no azure para ser usado depois
        blob_client.upload_blob(file.getvalue(),  blob_type="BlockBlob")


        # Manda os dados de precisao do modelo, para monitorar a precisao e reliability
        config= {
            'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
            'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
            'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
            'CONTAINER': 'models'
        }


        #monta o objeto a ser enviado para o banco
        model_db={"model_type": "random_forest",
                    "estimators": best_n_estimators,
                    "datetime":  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "error_rate": error_rate,
                "id":str(uuid.uuid4())
                 }|({'accuracy': accuracy } if column in categorical_columns else {'mse':mse})
        
        # sobe os dados no banco de modelos
        result = upload_data(config, [model_db])
