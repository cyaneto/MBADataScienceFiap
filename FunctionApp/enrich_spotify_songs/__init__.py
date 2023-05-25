import datetime
import logging
import os
import azure.functions as func
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from cosmo_lib import retrieve_data, upload_data
from spotify_lib import enrich_songs, join_lists




def main(mytimer: func.TimerRequest) -> None:

    """
    Enriquece as musicas que ainda nao tem metadados enriquecidos
    """
   
    # monta a configuração do banco
    config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'songs'
    }

    #puxa na base de dados as musicas
    _songs = retrieve_data(config)

    # puxa da base de dados as musicas que nao foram enriqeucidas ainda
    ids= [i['id'] for i in _songs['result'] if 'label' not in i and 'duration_ms' in i]
    
    features = enrich_songs(ids)
    
    # mistura  as listas
    data = join_lists(_songs['result'], features)

    #sobe para o banco
    result = upload_data(config, data)
