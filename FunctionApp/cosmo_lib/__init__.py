import azure.cosmos.cosmos_client as cosmos_client


def upload_data(config, data):
    """
    Sobe os dados para o banco cosmos
    """


    # Cria um cliente do Cosmos DB
    client = cosmos_client.CosmosClient(url_connection=config['ENDPOINT'],auth= {'masterKey': config['PRIMARYKEY']})

    # Cria um novo container no banco de dados, caso ele ainda não exista
    # database = client.get_database_client(config['DATABASE'])
    # container = database.get_container_client(config['CONTAINER'])

    container_link = f"dbs/{config['DATABASE']}/colls/{config['CONTAINER']}"
    # Insere cada dicionário da lista como uma linha no banco de dados
    for record in data:
        #container.upsert_item(body=record)
        client.UpsertItem(container_link,record)
    # retorna sucesso
    return {"success": True, "message":"Sucesso ao subir "+str(len(data))+" registros para o banco de "+config['CONTAINER']}


def retrieve_data(config):
    """
    Puax os dados do banco cosmos
    """

    # Cria um cliente do Cosmos DB
    client = cosmos_client.CosmosClient(url_connection=config['ENDPOINT'],auth= {'masterKey': config['PRIMARYKEY']})

    # Cria um novo container no banco de dados, caso ele ainda não exista
    # database = client.get_database_client(config['DATABASE'])
    # container = database.get_container_client(config['CONTAINER'])

    # puxa os dados
    #items  = container.read_all_items()
    container_link = f"dbs/{config['DATABASE']}/colls/{config['CONTAINER']}"
    items  = client.ReadItems(container_link)

    # retorna sucesso
    return {"success": True,"message":"sucesso :)","result":[item for item in items]}


def search_data(config, query):
    """
    Puax os dados do banco cosmos
    """

    # Cria um cliente do Cosmos DB
    client = cosmos_client.CosmosClient(url=config['ENDPOINT'],credential= {'masterKey': config['PRIMARYKEY']})

    # Cria um novo container no banco de dados, caso ele ainda não exista
    database = client.get_database_client(config['DATABASE'])
    container = database.get_container_client(config['CONTAINER'])

    # puxa os dados
    items  = container.query_items(query)

    # retorna sucesso
    return {"success": True,"message":"sucesso :)","result":[item for item in items]}