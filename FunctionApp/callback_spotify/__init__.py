import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
     
     #recebe o callback do spotify
    pass

     #salva no banco

    return func.HttpResponse(status_code=200, body='{}')