import json
import os

import azure.functions as func
import pandas as pd
from cosmo_lib import retrieve_data, upload_data


def main(req: func.HttpRequest) -> func.HttpResponse:

    # monta o resultado apra erro
    result = {"success": False, "message": "Endpoint Invalido"}


    # monta a configuração do banco
    config= {
        'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
        'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
        'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
        'CONTAINER': 'models'
    }
    
    # se for get retorna a lista de usuarios
    if req.method == 'GET':


        # puxa os dados do banco
        result = retrieve_data(config)

        #transforma em datafram
        df= pd.DataFrame(result['result'])

        #caso nao seja nenhum dos dois retorna erro
        return func.HttpResponse(body= df.to_csv(), status_code=200 if result.get("success") else 400)
    
    # se for post salva os usuarios na tabela
    elif req.method == 'POST':

        #pega os dados como um json do corpo
        data = req.get_json()
        
        # sobe os dados no banco
        result = upload_data(config, data)


    #caso nao seja nenhum dos dois retorna erro
    return func.HttpResponse(body=json.dumps(result), status_code=200 if result.get("success") else 400)
