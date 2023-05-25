

from io import BytesIO
import json
import os
import time
import pandas as pd
import requests 
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

from cosmo_lib import retrieve_data

# separa as colunas por tipo
categorical_columns = ['mode', 'time_signature', 'explicit',  'disc_number']
float_columns = ['danceability', 'energy', 'loudness',  'speechiness', 'acousticness', 'instrumentalness',
       'liveness', 'valence' , 'tempo','duration_ms', 'popularity']
model_columns = float_columns+categorical_columns+['time_gap']



def join_lists(list1, list2):
    lookup = {item['id']: item for item in list2}
    # Join the dictionaries from list1 and list2 based on 'id'
    joined_list = []
    for item in list1:
        item2 = lookup.get(item['id'])
        if item2:
            joined_dict = {**item, **item2}
            joined_list.append(joined_dict)

    return joined_list
  
def enrich_songs(ids):
    #pega as credenciais do SPOTIFY e o chunksize
    cid = os.environ["SPOTIFY_CLIENT_ID"]
    secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    chunk_size = int(os.environ["SPOTIFY_CHUNK_SIZE"])

    #instancia o cliente do spotify
    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    sp = spotipy.Spotify(client_credentials_manager= client_credentials_manager)

    features=[]
    #passa nos ids em chunks 
    for id_chunk in [ids[i * chunk_size:(i + 1) * chunk_size] for i in range((len(ids) + chunk_size - 1) // chunk_size )]:

        #busca os dados no spotify
        features.extend(sp.audio_features(tracks=id_chunk))
    
    # mistura  as listas
    return features
    
# gera o token
def get_token(user = 'eb1060ace869470199dfb41aaecca2ab'):

    try: 

        # instncia o blob
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        container_name = "auth"
        container_client = blob_service_client.get_container_client(container_name)
        data = json.loads(container_client.download_blob(f"spotify_{user}_credentials.json").readall())

        # se o token venceu
        if 'expires' not in data.keys() or  int(time.time())> int(data['expires']):

            # se ele tem refresh_token
            if 'refresh_token' in data.keys():

                    
                request_data = {
                'client_id': os.environ["SPOTIPY_CLIENT_ID"],
                'client_secret':os.environ["SPOTIPY_CLIENT_SECRET"],
                'grant_type': 'refresh_token',
                'refresh_token': data['refresh_token'],
                'redirect_uri': os.environ["SPOTIPY_REDIRECT_URI"],
                }

                # refresca ao token
                with requests.post('https://accounts.spotify.com/api/token', data=request_data) as response:

                    blob_client = blob_service_client.get_blob_client(container_name, "spotify_eb1060ace869470199dfb41aaecca2ab_credentials.json")
                    blob_client.delete_blob()
                    blob_client.upload_blob(response.content,  blob_type="BlockBlob")

    except Exception as err:
        pass


    # pede um novo token
    request_data = {
    'client_id': os.environ["SPOTIPY_CLIENT_ID"],
    'client_secret':os.environ["SPOTIPY_CLIENT_SECRET"],
    'scope': 'user-read-currently-playing',
    'response_type': 'code',
    'redirect_uri': os.environ["SPOTIPY_REDIRECT_URI"],
    }

    # refresca ao token
    with requests.get('https://accounts.spotify.com/pt-BR/authorize', params=request_data) as response:

        blob_client = blob_service_client.get_blob_client(container_name, "spotify_eb1060ace869470199dfb41aaecca2ab_credentials.json")
        blob_client.delete_blob()
        json_response = json.loads(response.content)
        blob_client.upload_blob(json.dumps(json_response|{'expires': time.time()+json_response['expires_in']}),  blob_type="BlockBlob")


def get_base(user = '', with_songs = False):

    # monta a configuração do banco
    config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'songs'
    }
    
    # puxa os dados do banco de ouvidas
    result_musics = retrieve_data(config)
    
    # enriquece a base de musicas ouvidas
    features = enrich_songs([i['id'] for i in result_musics['result'] if 'label' not in i and '-' not in i['id']])
    musics_data = join_lists(result_musics['result'], features )
    df_musics = pd.DataFrame([r for r in musics_data if  r.get('id') and  '-' not in r.get('id')])

    # puxa os dados de listens
    result_listens = retrieve_data(config|{'CONTAINER': 'listens'})
    df_listens = pd.DataFrame([r for r in result_listens['result'] if  r.get('music') and  '-' not in r.get('music')])

    # monta o dataframe juntanto so dois dados
    df= df_listens.merge(df_musics, how='inner', left_on='music', right_on='id').sort_values( 'datetime')



    # formata elas
    df[categorical_columns] =df[categorical_columns].apply(lambda x: x.astype('category'))
    df[float_columns] =df[float_columns].apply(lambda x: x.astype('float64'))


    #formata a coluna de data e cria uma coluna medindo o tempo emtre uma ouvida e outra por usuairo
    df['datetime'] = pd.to_datetime(df['datetime'], format="%Y-%m-%dT%H:%M:%S")
    df['time_gap']  =   df.groupby([ 'user'])['datetime'].diff().dt.seconds


    if not user:
        if with_songs:
            return df, df_musics
        return df
    
    df=df[df['user']==user]
    if with_songs:
        return df, df_musics
    return df
