import numpy as np
import pandas as pd
from urllib import request
from bokeh.plotting import figure, output_file, show


def get_data():
    data = request.urlopen("http://paulbarry.itcarlow.ie/weatherdata/weather_reports.csv")
    csv_data = pd.read_csv(data, sep='|', dayfirst=True,  parse_dates=[0])
    return csv_data


def create_multiIndex(data):
    data = data.set_index(["Date","Time"], drop=False)
    return data


def fix_windspeed(data):
    def use_higher(row):
        if  pd.isnull(row['Wind Speed (kts)']):
            row['Wind Speed (kts)'] = ''

        if 'Gust' in row['Wind Speed (kts)'] :
            temp = row['Wind Speed (kts)'].split('Gust')
            if int(temp[0]) > int(temp[1]):
                gust = temp[0]
            else:
                gust = temp[1]

            return gust

    data['Wind Speed (kts)'] = data.apply(use_higher, axis=1)
    data['Wind Speed (kts)'] = data['Wind Speed (kts)'].fillna('0')
    return data


def fill_trace(data):
    def set_trace(row):
        if row['Rain (mm)'] == 'Trace':
            rain = '0.00'
        elif row['Rain (mm)'] == 'n/a':
            rain = '0.00'
        else:
            rain = row['Rain (mm)']

        return rain
        
    data['Rain (mm)'] = data.apply(set_trace, axis=1)

    return data


def fill_dashes(row,items,value, col_names):
    if row[items] == 'n/a':
        row[items] = value
    if row[items] == '--':
        new_value = value
    else:
        new_value = row[items]
    return new_value


def fill_numeric_blanks(data):
    col_names = ['Wind Speed (kts)','Rain (mm)', 'Pressure (hPa)', 'Temp (◦C)', 'Humidity (%)' ]
    for items in col_names:
        value = '0'
        data[items] = data.apply(fill_dashes, axis=1, args=(items,value, col_names))
        data[items] = data[items].fillna('0')

    return data


def fill_descriptive_blanks(data):
    col_names = ['Date', 'Time', 'Location', 'Wind Direction','Weather' ]
    for items in col_names:
        value = 'Unknown'
        data[items] = data.apply(fill_dashes, axis=1, args=(items,value, col_names))
    return data


def change_types(data):
    data['Rain (mm)'] = data['Rain (mm)'].astype(float)
    data['Wind Speed (kts)'] = data['Wind Speed (kts)'].astype(int)
    data['Temp (◦C)'] = data['Temp (◦C)'].astype(int)
    data['Humidity (%)'] = data['Humidity (%)'].astype(int)
    data['Pressure (hPa)'] = data['Pressure (hPa)'].astype(int)

    return data


data = get_data()
data = create_multiIndex(data)
data = fix_windspeed(data)
data = fill_trace(data)
data = fill_numeric_blanks(data)
data = change_types(data)

graph1_data = data.groupby(['Location'])['Rain (mm)'].mean()
print(graph1_data)
print(type(graph1_data))
output_file('graph1.html')
p = figure(plot_width=400, plot_height=400)
#p = vbar(x=data[])
#print(data.loc[data['Location'] == 'MARKREE SLIGO(A)'])



