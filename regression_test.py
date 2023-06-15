# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 15:01:55 2023

@author: erwan
"""

import requests
import base64
import pytest
from datetime import datetime
import pandas as pd
import os
client_id = "9a5feb10-b937-4bc9-b64c-6c9c275b618b"
client_secret = "22bb2cde-e3df-444d-aade-c2c82cb14fce"
authorization = f"{client_id}:{client_secret}"
authorization_64bit = base64.b64encode(authorization.encode()).decode()
token_url = "https://digital.iservices.rte-france.com/token/oauth/"
token_autho = {
    "Authorization": "Basic " + authorization_64bit,
    "Content-Type": "application/x-www-form-urlencoded",
}

response = requests.post(token_url, headers=token_autho)
token_json = response.json()

token = token_json
data_url = "http://digital.iservices.rte-france.com/open_api/actual_generation/v1/actual_generations_per_production_type?start_date=2022-12-01T00:00:00%2B02:00&end_date=2022-12-10T00:00:00%2B02:00"

data_autho = {
    "Authorization": "Bearer " + token_json["access_token"],
    "Content-Type": "application/soap+xml",
    "charset": "UTF-8",
}
df_production = pd.read_csv("df_production.csv", parse_dates=['start_date'])
df_mean_byhour = pd.read_csv("df_mean_byhour.csv")

def test_auth_api_availability():


    assert response.status_code == 200
    
    assert "access_token" in token_json

def test_data_api_availability():
    response = requests.get(data_url, headers=data_autho)
    assert response.status_code == 200
    data_json = response.json()
    assert "actual_generations_per_production_type" in data_json

def test_data_conversion():
    assert df_production['start_date'].dtype == 'datetime64[ns, pytz.FixedOffset(120)]'
    assert df_production['start_date'].dtype == 'datetime64[ns, pytz.FixedOffset(120)]'
    assert df_production['start_date'].dtype == 'datetime64[ns, pytz.FixedOffset(120)]'
    assert df_production['start_date'].dtype == 'datetime64[ns, pytz.FixedOffset(120)]'

#def test_utc_uniqueness():
    #unique_offsets = df_production['start_date'].dt.tz.utcoffset()
    #assert len(unique_offsets.unique()) == 1




def test_mean_calculation():
   

    expected_results = {
        ('BIOMASS', 0): (0, 1000),
        ('FOSSIL_GAS', 0): (0, 5000),
        ('FOSSIL_HARD_COAL', 0): (0, 100),
        ('FOSSIL_OIL', 0): (0, 500),
        ('HYDRO_PUMPED_STORAGE', 0): (0, 1000),
        ('HYDRO_RUN_OF_RIVER_AND_POUNDAGE', 0): (4000, 8000),
        ('HYDRO_WATER_RESERVOIR', 0): (1000, 3000),
        ('NUCLEAR', 0): (25000, 35000),
        ('SOLAR', 0): (3000, 6000),
        ('TOTAL', 0): (40000, 60000),
        ('WASTE', 0): (0, 500),
        ('WIND_ONSHORE', 0): (1000, 4000),
    }

    for index, row in df_mean_byhour.iterrows():
        production_type = index[0]
        hour = index[1]
        expected_min, expected_max = expected_results.get((production_type, hour), (None, None))
        if expected_min is not None and expected_max is not None:
            assert row['value_value'] >= expected_min and row['value_value'] <= expected_max
        else:
            assert False, f"No expected result defined for production_type: {production_type}, hour: {hour}"
            
            
pytest.main()

