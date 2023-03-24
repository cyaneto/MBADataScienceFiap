import azure.cosmos.cosmos_client as cosmos_client


def upload_data(config, data):
    """
    Sobe os dados para o banco cosmos
    """


    # Cria um cliente do Cosmos DB
    client = cosmos_client.CosmosClient(url=config['ENDPOINT'],credential= {'masterKey': config['PRIMARYKEY']})

    # Cria um novo container no banco de dados, caso ele ainda não exista
    database = client.get_database_client(config['DATABASE'])
    container = database.get_container_client(config['CONTAINER'])

    # Insere cada dicionário da lista como uma linha no banco de dados
    for record in data:
        container.upsert_item(body=record)

    # retorna sucesso
    return {"success": True, "message":"Sucesso ao subir "+str(len(data))+" registros para o banco de "+config['CONTAINER']}


def retrieve_data(config):
    """
    Puax os dados do banco cosmos
    """

    # Cria um cliente do Cosmos DB
    client = cosmos_client.CosmosClient(url=config['ENDPOINT'],credential= {'masterKey': config['PRIMARYKEY']})

    # Cria um novo container no banco de dados, caso ele ainda não exista
    database = client.get_database_client(config['DATABASE'])
    container = database.get_container_client(config['CONTAINER'])

    # puxa os dados
    items  = container.read_all_items()

    # retorna sucesso
    return {"success": True,"message":"sucesso :)","result":[item for item in items]}