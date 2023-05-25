import os
import uuid
import pandas as pd
from io import BytesIO
import sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
import azure.functions as func
import os
import joblib
import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from cosmo_lib import retrieve_data, upload_data
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, confusion_matrix, matthews_corrcoef
from sklearn.model_selection import train_test_split
from spotify_lib import enrich_songs, join_lists,float_columns, categorical_columns, model_columns, get_base
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, mean_squared_error


def main(mytimer: func.TimerRequest) -> None:

    df = get_base()



    train_df = df[model_columns+['user']]

    dummies= int(os.environ['MODEL_DUMMIES'])
    #faz a dummificação
    for d in range (dummies):
        for column in model_columns:
            train_df[f'{column}_{d}'] = train_df.groupby('user')[column].shift(d)

    #remove as colunas de modelo
    train_df= train_df[[ c for c in train_df if c not in  model_columns and c != 'user']].dropna()

    # separa as variaveis de target e 
    y= train_df[[c+'_0' for c in  model_columns]]
    X = train_df[[c for c in  train_df.columns if c not in y.columns]]

    # Define the parameter grid for tuning the number of estimators
    param_grid = {'n_estimators': [10, 50, 100, 200, 500]}

    # passa em cada um dos parametros da musica
    for column in model_columns:

        y= train_df[column+'_0']
        X = train_df[[c for c in  train_df.columns if '_0' not in c]]

        if column in categorical_columns:
            rf = RandomForestClassifier()
        else:
            rf = RandomForestRegressor()


        # Perform a grid search with cross-validation to find the best number of estimators
        grid_search = GridSearchCV(rf, param_grid, cv=5)
        grid_search.fit(X, y)

        # Get the best number of estimators
        best_n_estimators = grid_search.best_params_['n_estimators']
        print(f"Best number of estimators for {column}:", best_n_estimators)

        # Train the Random Forest Classifier with the best number of estimators
        if column in categorical_columns:
            best_rf = RandomForestClassifier(n_estimators=best_n_estimators)
        else:
            best_rf = RandomForestRegressor(n_estimators=best_n_estimators)
        best_rf.fit(X, y)

        # Make predictions with the trained model
        y_pred = best_rf.predict(X)

        if column in categorical_columns:
            # Calculate accuracy score
            accuracy = accuracy_score(y, y_pred)
            print(f"Accuracy  for {column}:", accuracy)
            error_rate= abs(1-accuracy)

        else:
            # Calculate mean squared error
            mse = mean_squared_error(y, y_pred)
            print(f"Mean Squared Error for {column}:", mse)
            error_rate= mse



        # monta um arquvio io
        file = BytesIO()

        # salva o resuultado no arquivo
        joblib.dump(best_rf, file)
        
        # salva o resultado do modelo no blob
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        container_name = "modeldata"
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = blob_service_client.get_blob_client(container_name, f"rf_best_next_music_model_{column}.joblib")


        if blob_client.exists():
            blob_client.delete_blob()

        # salva o arquivo no azure
        blob_client.upload_blob(file.getvalue(),  blob_type="BlockBlob")

        config= {
            'ENDPOINT': os.environ["COSMOS_NORMAL_ENDPOINT"],
            'PRIMARYKEY': os.environ["COSMOS_NORMAL_PRIMARYKEY"],
            'DATABASE': os.environ["COSMOS_NORMAL_DATABASE"],
            'CONTAINER': 'models'
        }


        #monta o objeto a ser enviado para o banco
        model_db={"model_type": "random_forest",
                    "estimators": best_n_estimators,
                    "datetime":  datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "error_rate": error_rate,
                "id":str(uuid.uuid4())
                 }|({'accuracy': accuracy } if column in categorical_columns else {'mse':mse})
        
        # sobe os dados no banco
        result = upload_data(config, [model_db])
