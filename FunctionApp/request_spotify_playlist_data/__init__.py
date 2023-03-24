import datetime
import json
import logging

import azure.functions as func
from azure.storage.queue import (
        QueueClient,
        BinaryBase64EncodePolicy,
        BinaryBase64DecodePolicy
)

import os, uuid

def main(mytimer: func.TimerRequest) -> None:
    
    # pega a lista de generos de um blob do azure HARDCODEADO
    generos = [
    {"category_id": 1, "category": "Rock"},
    {"category_id": 2, "category": "Pop"},
    {"category_id": 3, "category": "Hip Hop"},
    {"category_id": 4, "category": "R&B"},
    {"category_id": 5, "category": "Country"},
    {"category_id": 6, "category": "Jazz"},
    {"category_id": 7, "category": "Blues"},
    {"category_id": 8, "category": "Reggae"},
    {"category_id": 9, "category": "Soul"},
    {"category_id": 10, "category": "Funk"},
    {"category_id": 11, "category": "Punk Rock"},
    {"category_id": 12, "category": "Heavy Metal"},
    {"category_id": 13, "category": "Alternative Rock"},
    {"category_id": 14, "category": "Grunge"},
    {"category_id": 15, "category": "Indie Rock"},
    {"category_id": 16, "category": "EDM"},
    {"category_id": 17, "category": "House"},
    {"category_id": 18, "category": "Techno"},
    {"category_id": 19, "category": "Trance"},
    {"category_id": 20, "category": "Dubstep"},
    {"category_id": 21, "category": "Trap"},
    {"category_id": 22, "category": "Folk"},
    {"category_id": 23, "category": "Bluegrass"},
    {"category_id": 24, "category": "Americana"},
    {"category_id": 25, "category": "Gospel"},
    {"category_id": 26, "category": "Christian Rock"},
    {"category_id": 27, "category": "Contemporary Christian"},
    {"category_id": 28, "category": "Classical"},
    {"category_id": 29, "category": "Opera"},
    {"category_id": 30, "category": "Broadway"},
    {"category_id": 31, "category": "Disney"},
    {"category_id": 32, "category": "Swing"},
    {"category_id": 33, "category": "Big Band"},
    {"category_id": 34, "category": "Acoustic"},
    {"category_id": 35, "category": "Singer-Songwriter"},
    {"category_id": 36, "category": "World Music"},
    {"category_id": 37, "category": "Latin Music"},
    {"category_id": 38, "category": "Salsa"},
    {"category_id": 39, "category": "Reggaeton"},
    {"category_id": 40, "category": "Mariachi"},
    {"category_id": 41, "category": "Tejano"},
    {"category_id": 42, "category": "Merengue"},
    {"category_id": 43, "category": "Bachata"},
    {"category_id": 44, "category": "Cumbia"},
    {"category_id": 45, "category": "Flamenco"},
    {"category_id": 46, "category": "Afrobeat"},
    {"category_id": 47, "category": "K-pop"},
    {"category_id": 48, "category": "J-pop"},
    {"category_id": 49, "category": "Ambient"},
    {"category_id": 50, "category": "New Age"},
    {"category_id": 51, "category": "Avant-garde"},
    {"category_id": 52, "category": "Experimental"},
    {"category_id": 53, "category": "Noise"},
    {"category_id": 54, "category": "Industrial"},
    {"category_id": 55, "category": "Goth"},
    {"category_id": 56, "category": "Emo"},
    {"category_id": 57, "category": "Screamo"},
    {"category_id": 58, "category": "Hardcore Punk"},
    {"category_id": 59, "category": "Post-Punk"},
    {"category_id": 60, "category": "New Wave"},
    {"category_id": 61, "category": "Synthpop"},
    {"category_id": 62, "category": "Trip-hop"},
    {"category_id": 63, "category": "Rave"},
    {"category_id": 64, "category": "Drum and Bass"},
    {"category_id": 65, "category": "Jungle"},
    {"category_id": 66, "category": "Dub"},
    {"category_id": 67, "category": "Roots Rock"},
    {"category_id": 68, "category": "Southern Rock"},
    {"category_id": 69, "category": "Jam Band"},
    {"category_id": 70, "category": "Psychedelic Rock"},
    {"category_id": 71, "category": "Prog Rock"},
    {"category_id": 72, "category": "Classic"}]

    # instancia a fila do azure
    queue_client = QueueClient.from_connection_string(os.environ["AzureWebJobsStorage"], "generos")
    
    # Enfilera cada um dos generos
    for genero in generos:

        queue_client.send_message(json.dumps(genero))
