import datetime
import json
import logging
import os
from datetime import datetime
from uuid import uuid4
import azure.functions as func
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from azure.storage.blob import BlobServiceClient
from cosmo_lib import upload_data
from spotify_lib import get_token



# A FAZER
# Validar se nao esta ainda na mesma musica
# colocar possiblidade de multiplos usuarios
# fazer a autenticacao por codigo 


def main(mytimer: func.TimerRequest) -> None:
    user=  "5e3b7511-4336-453e-8199-a4ec14956742"
 
    # instncia o blob
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    container_name = "last-listens"
    container_client = blob_service_client.get_container_client(container_name)
    last_listen = json.loads(container_client.download_blob(f"spotify_{user}_last_listen.json").readall())

    #get_token()
    # Set up the Spotify API client
    
    scope = "user-read-currently-playing"
    
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    # Get what the user is listening now
    result = sp.current_user_playing_track()

    #se for uma faixa
    if result and result['item']['type'] == 'track' and last_listen['music']!=result['item']["id"]:    

        logging.info (f'Ele esta ouvindo {result["item"]["name"]}')

        # monta o registro para o banco
        record = {
            "id":str(uuid4()),
            "user": user,
            "music": result['item']["id"],
            "datetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        }

        #salva a ouvida no banco
        config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'listens'
        }   

        # sobe os dados no banco
        result = upload_data(config, [record])

        # marca a ultima ouvida
        blob_client = blob_service_client.get_blob_client(container_name, f"spotify_{user}_last_listen.json")
        if blob_client.exists():
            blob_client.delete_blob()
        blob_client.upload_blob(json.dumps(record),  blob_type="BlockBlob")