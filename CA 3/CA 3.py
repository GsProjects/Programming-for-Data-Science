import numpy as np
import pandas as pd
from urllib import request
from bokeh.plotting import figure, output_file, show
from bokeh.models import DatetimeTickFormatter,tickers
import altair as alt


def get_data():
    data = request.urlopen("http://paulbarry.itcarlow.ie/weatherdata/weather_reports.csv")
    csv_data = pd.read_csv(data, sep='|', dayfirst=True,  parse_dates=[0])
    return csv_data


def create_multiIndex(data):
    data['Dates'] = data['Date']
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
    row.fillna(value)
    return new_value


def fill_numeric_blanks(data):
    col_names = ['Wind Speed (kts)','Rain (mm)', 'Pressure (hPa)', 'Temp (◦C)', 'Humidity (%)' ]
    for items in col_names:
        value = '0'
        data[items] = data.apply(fill_dashes, axis=1, args=(items,value, col_names))
        data[items] = data[items].fillna('0')

    return data


def fill_descriptive_blanks(data):
    col_names = ['Date', 'Time', 'Location', 'Wind Direction','Weather','Dates' ]
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


def create_graph1(data):
    graph1_data = data.groupby(['Location'])['Rain (mm)'].mean()
    temp_df = graph1_data.to_frame()
    temp_df.reset_index(level=0, inplace=True)  # index gets converted to a column

    output_file('avg_rainfall.html')
    p = figure(x_range=temp_df['Location'].tolist(), plot_width=3200, plot_height=400)
    p.xaxis[0].axis_label = 'Location'
    p.yaxis[0].axis_label = 'Rainfall (mm)'

    p.line(temp_df['Location'].tolist(), temp_df['Rain (mm)'].tolist(), line_width=2)
    p.circle(temp_df['Location'].tolist(), temp_df['Rain (mm)'].tolist(), fill_color="blue", size=8)

    show(p)


def create_graph2(data):
    graph1_data = data.groupby(['Location'])['Temp (◦C)'].mean()
    temp_df = graph1_data.to_frame()
    temp_df.reset_index(level=0, inplace=True)  # index gets converted to a column

    output_file('avg_temp.html')
    p = figure(x_range=temp_df['Location'].tolist(), plot_width=3200, plot_height=400)
    p.xaxis[0].axis_label = 'Location'
    p.yaxis[0].axis_label = 'Temperature (◦C)'

    p.line(temp_df['Location'].tolist(), temp_df['Temp (◦C)'].tolist(), line_width=2)
    p.circle(temp_df['Location'].tolist(), temp_df['Temp (◦C)'].tolist(), fill_color="red", size=8)

    show(p)


def create_graph3(data):
    #how has rainfall rates changed over time

    graph1_data = data.groupby(['Dates'])['Rain (mm)'].mean()
    temp_df = graph1_data.to_frame()
    temp_df.reset_index(level=0, inplace=True)  # index gets converted to a column

    output_file('rain_vs_temp.html')
    p = figure(x_axis_type="datetime", plot_width=1200, plot_height=400)
    p.xaxis[0].axis_label = 'Date'
    p.yaxis[0].axis_label = 'Rainfall (mm)'

    p.line(temp_df['Dates'].tolist(), temp_df['Rain (mm)'].tolist(), line_width=2)
    p.xaxis.formatter = DatetimeTickFormatter(days=["%d/%b"])
    p.xaxis[0].ticker.desired_num_ticks = 10
    show(p)

def create_windSpeed_bin(data):
    means = data.groupby(['Location'])['Wind Speed (kts)'].mean()
    means = means.to_frame()
    bins = pd.cut(means['Wind Speed (kts)'], 3, labels=['Low', 'Average', 'High'])
    bins = bins.to_frame()

    means.columns.values[0] = 'Max Wind Speed (kts)'

    new_df = pd.concat([means, bins], axis=1, join_axes=[means.index])
    new_df.reset_index(level=0, inplace=True)  # convert index to a column
    new_df
    alt.Chart(new_df).mark_bar().encode(
        x='Location',
        y='Max Wind Speed (kts)',
        color='Wind Speed (kts)'
    )



data = get_data()
data = create_multiIndex(data)
data = fix_windspeed(data)
data = fill_trace(data)
data = fill_numeric_blanks(data)
data = change_types(data)
create_graph1(data)
create_graph2(data)
create_graph3(data)
create_windSpeed_bin(data)



a = data.groupby(['Location'])['Wind Speed (kts)'].mean()
a = a.to_frame()
a
b = pd.cut(a['Wind Speed (kts)'], 3, labels=['Low','Average','High'])
b.to_frame()
df = data.groupby(['Location'])['Wind Speed (kts)'].mean()
df= df.to_frame()
df.columns.values[0] = 'Max Wind Speed (kts)'

temp_df = b.to_frame()
new_df = pd.concat([df,temp_df],axis=1,join_axes=[df.index])

alt.Chart(new_df).mark_bar().encode(
    x='Location',
    y='Max Wind Speed (kts)',
    color= 'Wind Speed (kts)'
)



