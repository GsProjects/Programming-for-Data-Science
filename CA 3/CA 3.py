import pandas as pd
from datetime import datetime
import numpy as np


def change_date_type(data):
    def change_type(row):
        print(row)
        data = pd.to_datetime(row)
        print('data: ', data)
        return data

    data['Date'] = data.apply(change_type, axis=1)
    return data


data = pd.read_csv('weather_reports.csv', sep='|')
print(data)
#print(data)
#print(data['Date'])
#data = change_date_type(data)
