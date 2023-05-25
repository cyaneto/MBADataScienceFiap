import datetime
import json
import logging
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from io import BytesIO, StringIO
import azure.functions as func
import requests


def main(mytimer: func.TimerRequest) -> None:
    
    # pega o token atual do blob
    # intancia o arquvio
    file = BytesIO()

    # instncia o blob
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    container_name = "auth"
    container_client = blob_service_client.get_container_client(container_name)
    data = json.loads(container_client.download_blob("spotify_eb1060ace869470199dfb41aaecca2ab_credentials.json").readall())

    #carrega os dados em um dict
    
    
    request_data = {
    'client_id': os.environ["SPOTIPY_CLIENT_ID"],
    'grant_type': 'refresh_token',
    'refresh_token': data['refresh_token'],
    'redirect_uri': os.environ["SPOTIPY_REDIRECT_URI"],
    }

    with requests.post('https://accounts.spotify.com/api/token', data=request_data) as response:

        blob_client = blob_service_client.get_blob_client(container_name, "spotify_eb1060ace869470199dfb41aaecca2ab_credentials.json")
        blob_client.delete_blob()
        blob_client.upload_blob(response.content,  blob_type="BlockBlob")