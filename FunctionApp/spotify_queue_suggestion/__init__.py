import datetime
import json
import logging
import os
from datetime import datetime
from uuid import uuid4
import azure.functions as func
from requests import post
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
    pass

    # # se estiver com a varivel marcada para rodar 
    # if (int(os.environ['QUEUE_SUGGESTION'])):

    #     #monta o escopo e o cliente
    #     scope = "user-modify-playback-state"  
    #     sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    #     # prediz as melhores proximas musicas
    #     with post('http://localhost:7071/api/predict_best_next_songs') as response:

    #         for song_id in response.json():
    #             sp.add_to_queue(f'spotify:track:{song_id}')

