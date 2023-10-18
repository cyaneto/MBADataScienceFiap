import json
import logging
import joblib
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from io import BytesIO
import azure.functions as func
import os
from spotify_lib import enrich_songs, get_base, join_lists, model_columns
import numpy as np

def main(req: func.HttpRequest) -> func.HttpResponse:
        
        dummies= os.environ['MODEL_DUMMIES']
        # pega a base de treino
        df, df_musics = get_base(with_songs=True)
        

        X = df[model_columns+['user']]

        dummies= int(os.environ['MODEL_DUMMIES'])-1
        #faz a dummificação
        for d in range (dummies):
                for column in model_columns:
                        X[f'{column}_{d+1}'] = X.groupby('user')[column].shift(d)

        #remove as colunas de modelo
        X= X[[ c for c in X if c not in  model_columns and c != 'user']].dropna()


        # monta o dicionairo de reesponsta
        best_music_attributes={}

        # passa em cada uma das colunas do modelo
        for column in model_columns:
                try: 
                        # intancia o arquvio
                        file = BytesIO()

                        # instncia o blob
                        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
                        container_name = "modeldata"
                        container_client = blob_service_client.get_container_client(container_name)
                        file.write(container_client.download_blob(f"rf_best_next_music_model_{column}.joblib").readall())

                        #returns the file to te begining
                        file.seek(0)
                        #carrega o modelo pelo joblib
                        model = joblib.load(file )
                        
                        # preve a proxima melhor music5
                        best_music_attributes[column] = model.predict(X.tail(1))[0]
                except Exception as err:
                        logging.info(str(err))

        #calcula as proximidades
        df_musics = df_musics.fillna(0)
        proximidades = np.zeros(len(df_musics))
        for column in best_music_attributes.keys():
                proximidades += df_musics[column].apply(lambda x: (x-best_music_attributes[column])**2)
        df_musics['proximidade']= np.sqrt(proximidades)

        # retorna as 5 melhores musicas
        result = list(df_musics.sort_values('proximidade').head(5)['id'])
        return func.HttpResponse(
                json.dumps(result),
                status_code=200
        )