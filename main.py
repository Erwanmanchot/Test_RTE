import requests
import base64
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request
from threading import Lock
import matplotlib.pyplot as plt
import os 
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath("main.py")))

#----------------------------- Récupération du token -------------------------

#Récupération du code d'authentification en base 64
client_id = "9a5feb10-b937-4bc9-b64c-6c9c275b618b"
client_secret = "22bb2cde-e3df-444d-aade-c2c82cb14fce"
authorization = f"{client_id}:{client_secret}"
authorization_64bit = base64.b64encode(authorization.encode()).decode()

# URL pour l'obtention du jeton d'accès
token_url = "https://digital.iservices.rte-france.com/token/oauth/"

token_autho={
    "Authorization":"Basic "+authorization_64bit,
    "Content-Type": "application/x-www-form-urlencoded",
}

# Envoi de la requête POST pour obtenir le jeton d'accès
response = requests.post(token_url, headers=token_autho)

# Vérification du code de statut de la réponse
print(response.status_code)

#Extraction du token dans le json
token_json = response.json()
token=token_json["access_token"]
print(token)

#----------------------------- Récupération de la data via l'API -------------------------
# URL pour l'obtention des data
data_url = "http://digital.iservices.rte-france.com/open_api/actual_generation/v1/actual_generations_per_production_type? start_date=2022-12-01 & end_date=2022-12-10"
data_autho={
    "Authorization":"Bearer "+ token,
    "Content-Type": "application/soap+xml",
    "charset":"UTF-8",
}

# Envoi de la requête GET pour obtenir les datas
data_response = requests.get(data_url, headers=data_autho)

# Vérification du code de statut de la réponse
print(data_response.status_code)
#Data finale
#A décommenter dès que j'ai un code 200
data_json = data_response.json()
print(data_json)

#----------------------------- Transformation du json en Dataframe-------------------------
# Charger le JSON dans un dictionnaire
data = []

for production in data_json['actual_generations_per_production_type']:
    start_date = production['start_date']
    end_date = production['end_date']
    production_type = production['production_type']
    for value in production['values']:
        value_start_date = value['start_date']
        value_end_date = value['end_date']
        #value_updated_date = value['updated_date']
        value_value = value['value']
        data.append([start_date, end_date, production_type, value_start_date, value_end_date, value_value])

# Création du DF
df_production = pd.DataFrame(data, columns=['start_date','end_date', 'production_type', 'value_start_date', 'value_end_date', 'value_value'])

#-----------------------------  Récupération des Heures de la journée pour chaque Ligne-------------------------

df_production['start_date'] = pd.to_datetime(df_production['start_date'], format='%Y-%m-%dT%H:%M:%S%z', errors='coerce')
df_production['end_date'] = pd.to_datetime(df_production['end_date'], format='%Y-%m-%dT%H:%M:%S%z', errors='coerce')
df_production['value_start_date'] = pd.to_datetime(df_production['value_start_date'], format='%Y-%m-%dT%H:%M:%S%z', errors='coerce')
df_production['value_end_date'] = pd.to_datetime(df_production['value_end_date'], format='%Y-%m-%dT%H:%M:%S%z', errors='coerce')

#df_production[(df_production['date'] > '2022-12-01') & (df_production['date'] < '2022-12-10')]
print(df_production.to_string())


#-----------------------------  Vérification que toutes les données soient bien dans le même UTC-------------------------
#
first_UTC = df_production['start_date'].dt.tz
def verify_UTC(row):
    if row['start_date'].tz == first_UTC:
        val = 0
    else:
        val = 1
    return val

df_production['UTC_compliance'] = df_production.apply(verify_UTC, axis=1)

#Si 0 alors UTC commun
sum_UTC=df_production['UTC_compliance'].sum()
del df_production['UTC_compliance']
print(sum_UTC)

#Enlever les product type total
df_production = df_production[df_production['production_type'] != 'TOTAL']

#-----------------------------  Moyenne par heure par type de production--------------------------

#extract de l heure sur les dates de start
df_production["Hour"] = df_production['value_start_date'].dt.hour
#groupby mean par heure
df_mean_byhour= df_production.groupby(['production_type', 'Hour'])['value_value'].mean().reset_index()
print(df_production.dtypes)
len(df_production.axes[0])
len(df_production.axes[1])

#-----------------------------  Moyenne par heure par type de production-------------------------
# Écriture de df_production en CSV
script_dir = os.path.dirname(os.path.abspath("main.py"))
csv_path = os.path.join(script_dir, 'df_production.csv')
df_production.to_csv(csv_path, index=False)

# Écriture de df_production en CSV
script_dir = os.path.dirname(os.path.abspath("main.py"))
csv_path = os.path.join(script_dir, 'df_mean_byhour.csv')
df_mean_byhour.to_csv(csv_path, index=False)


#----------------------------- Flask-------------------------
app = Flask(__name__, template_folder='templates')

@app.route('/')
def graph():

    stacked_data = []
    labels = []

    for production_type, group in df_mean_byhour.groupby('production_type'):
        stacked_data.append({
            'label': production_type,
            'data': group['value_value'].tolist(),
        })

    labels = df_mean_byhour['Hour'].tolist()

    # Rendu du modèle HTML avec le graphique en passant les variables
    return render_template('main.html', stacked_data=stacked_data, labels=labels)


if __name__=="__main__":
    app.run()
    

