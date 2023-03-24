from datetime import datetime
import json
import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import azure.functions as func
import os

from cosmo_lib import upload_data

def main(msg: func.QueueMessage) -> None:
    
    # monta a lista de resultados
    result_final_audio_features = []

    # pega o genero pela mensagem
    genero = msg.get_json()

    #pega as credenciais do spotfy
    cid = os.environ["SPOTFY_CLIENT_ID"]
    secret = os.environ["SPOTFY_CLIENT_SECRET"]

    #instancia o cliente do spotify
    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    sp = spotipy.Spotify(client_credentials_manager= client_credentials_manager)

    # buscaas playlists no spotfy
    results = sp.search( genero["category"] , limit=5 , offset=0 , type='playlist')

    #print(results)
    count_playlist = 0

    # passa em cada uma das playlists
    for playlist in results['playlists']['items']:
        
        count_playlist += 1
        #print(playlist['id'])

        # pega as musicas da playlist
        playlist_items = sp.playlist_items( playlist['id'])   

        # passa em cada um dos itens da playlist
        for item in playlist_items['items']:

            # se tem track
            if item['track'] is not None and item['track']['id'] is not None:

                #pega as features da musica
                audio_features = sp.audio_features(tracks=[item['track']['id']])

                # se tem features
                if audio_features[0] is not None:
                    audio_features[0]["playlist_id"] = playlist['id']
                    #add categoria e data de criação na lista
                    audio_features[0]["category"] = genero["category"]
                    audio_features[0]["category_id"] = genero["category_id"]
                    audio_features[0]["creation_date"] = datetime.now().strftime('%Y-%m-%dT%H:%M%S')
                    
                    
                    result_final_audio_features += audio_features 
        print(count_playlist)

    # sobe pra base do cosmos
    config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'songs'
    }
    result = upload_data(config, result_final_audio_features)
