import datetime
import logging
import os
from datetime import datetime
from uuid import uuid4
import azure.functions as func
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

from cosmo_lib import upload_data
from spotify_lib import get_token



# A FAZER
# Validar se nao esta ainda na mesma musica
# colocar possiblidade de multiplos usuarios
# fazer a autenticacao por codigo 


def main(mytimer: func.TimerRequest) -> None:
 
    get_token()
    # Set up the Spotify API client
    try: 
        auth_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(auth_manager=auth_manager)
    except:
        print('nao rolou')
        scope = "user-read-currently-playing"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    # Get what the user is listening now
    result = sp.current_user_playing_track()

    #se for uma faixa
    if result and result['type'] == 'track':    

        logging.info (f'Ele esta ouvindo {result["item"]["name"]}')
        #salva a ouvida no banco
        config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'listens'
        }   

        # sobe os dados no banco
        result = upload_data(config, [{
            "id":str(uuid4()),
            "user": "5e3b7511-4336-453e-8199-a4ec14956742",
            "music": result['item']["id"],
            "datetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        }])