import logging
import joblib
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from io import BytesIO
import azure.functions as func
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    
    # intancia o arquvio
    file = BytesIO()

    # instncia o blob
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    container_name = "modeldata"
    container_client = blob_service_client.get_container_client(container_name)
    file.write(container_client.download_blob("rf_plalist_classification_model.joblib").readall())

    #carrega o modelo pelo joblib
    model = joblib.load(file)
    
    

    return func.HttpResponse(
            "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200
    )
