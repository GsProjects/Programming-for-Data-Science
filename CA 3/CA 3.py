import numpy as np
import pandas as pd
from urllib import request as r
from bokeh.plotting import figure
from bokeh.embed import components
import altair as alt
from altair import Axis,Y
from flask import Flask, render_template,request


app = Flask(__name__)


def get_data():
    data = r.urlopen("http://paulbarry.itcarlow.ie/weatherdata/weather_reports.csv")
    csv_data = pd.read_csv(data, sep='|', dayfirst=True, parse_dates=[0], encoding='utf-8')
    csv_data.dropna(axis=1, how='all')
    return csv_data


def create_multiIndex(data):
    data['Dates'] = data['Date']
    data = data.set_index(["Date", "Time"], drop=False)
    return data


def fix_windspeed(data):
    def use_higher(row):
        if pd.isnull(row['Wind Speed (kts)']):
            row['Wind Speed (kts)'] = ''

        if 'Gust' in row['Wind Speed (kts)']:
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


def fill_dashes(row, items, value):
    if row[items] == "n/a":
        new_value = value
    elif row[items] == "--":
        new_value = value
    elif row[items] == 'CALM':
        new_value = value
    else:
        new_value = row[items]

    return new_value


def fill_numeric_blanks(data):
    col_names = ['Wind Speed (kts)', 'Rain (mm)', 'Pressure (hPa)', 'Temp (◦C)', 'Humidity (%)']
    for items in col_names:
        value = '-1'
        data[items] = data.apply(fill_dashes, axis=1, args=(items, value))
    for items in col_names:
        data[items] = data[items].fillna('0')

    return data


def fill_descriptive_blanks(data):
    col_names = ['Date', 'Time', 'Location', 'Wind Direction', 'Weather', 'Dates']
    for items in col_names:
        value = 'Unknown'
        data[items] = data.apply(fill_dashes, axis=1, args=(items, value))
    for items in col_names:
        value = 'Unknown'
        data[items] = data[items].fillna(value)
    return data


def change_types(data):
    data['Rain (mm)'] = data['Rain (mm)'].astype(float)
    data['Wind Speed (kts)'] = data['Wind Speed (kts)'].astype(int)

    data['Temp (◦C)'] = data['Temp (◦C)'].astype(int)
    data['Humidity (%)'] = data['Humidity (%)'].astype(int)
    data['Pressure (hPa)'] = data['Pressure (hPa)'].astype(int)

    col_names = ['Wind Speed (kts)', 'Rain (mm)', 'Pressure (hPa)', 'Temp (◦C)', 'Humidity (%)']
    for items in col_names:
        temp = data.loc[data[items] != -1]
        data[items] = data[items].fillna(temp.mean())

    return data


def create_graph1(data):
    graph1_data = data.groupby(['Location'])['Rain (mm)'].mean()
    temp_df = graph1_data.to_frame()
    temp_df.reset_index(level=0, inplace=True)  # index gets converted to a column

    p = figure(x_range=temp_df['Location'].tolist(), plot_width=1000, plot_height=400)
    p.xaxis[0].axis_label = 'Location'
    p.yaxis[0].axis_label = 'Average Rainfall (mm)'

    p.line(temp_df['Location'].tolist(), temp_df['Rain (mm)'].tolist(), line_width=2)
    p.circle(temp_df['Location'].tolist(), temp_df['Rain (mm)'].tolist(), fill_color="red", size=8)
    p.xaxis.major_label_orientation = 45
    p.yaxis.major_label_orientation = "vertical"
    return p


def create_graph2(data):
    graph1_data = data.groupby(['Location'])['Temp (◦C)'].mean()
    temp_df = graph1_data.to_frame()
    temp_df.reset_index(level=0, inplace=True)  # index gets converted to a column

    p = figure(x_range=temp_df['Location'].tolist(), plot_width=1000, plot_height=400)
    p.xaxis[0].axis_label = 'Location'
    p.yaxis[0].axis_label = 'Average Temperature (◦C)'

    p.line(temp_df['Location'].tolist(), temp_df['Temp (◦C)'].tolist(), line_width=2)
    p.circle(temp_df['Location'].tolist(), temp_df['Temp (◦C)'].tolist(), fill_color="red", size=8)
    p.xaxis.major_label_orientation = 45
    p.yaxis.major_label_orientation = "vertical"
    return p


def create_graph3(data):
    graph1_data = data.groupby(['Wind Direction'])['Wind Speed (kts)'].mean()
    temp_df = graph1_data.to_frame()
    temp_df.reset_index(level=0, inplace=True)  # index gets converted to a column

    p = figure(x_range=temp_df['Wind Direction'].tolist(), plot_width=1000, plot_height=400)
    p.xaxis[0].axis_label = 'Wind Direction'
    p.yaxis[0].axis_label = 'Average Wind Speed (kts)'

    p.circle(temp_df['Wind Direction'].tolist(), temp_df['Wind Speed (kts)'].tolist(), fill_color="red", size=8)
    p.xaxis.major_label_orientation = 45
    p.yaxis.major_label_orientation = "vertical"
    return p


def create_bins(data):
    columns = ['Wind Speed (kts)', 'Rain (mm)', 'Temp (◦C)', 'Humidity (%)']
    filenumber = 1
    for items in columns:
        means = data.groupby(['Location'])[items].mean()
        means = means.to_frame()
        bins = pd.cut(means[items], 3, labels=['Low', 'Moderate', 'High'])
        bins = bins.to_frame()

        bracket = items.index('(')
        legend = items[:bracket]

        bins.columns.values[0] = 'Average ' + legend + 'Category '
        means.columns.values[0] = 'Average ' + items + ' Per Station'

        new_df = pd.concat([means, bins], axis=1, join_axes=[means.index])
        new_df.reset_index(level=0, inplace=True)
        new_df


        graph = alt.Chart(new_df).mark_bar().encode(
            x='Location',
            y=Y(means.columns.values[0], axis=Axis(format='f')),
            #https://github.com/altair-viz/altair/issues/191

            color=bins.columns.values[0]
        )
        filename = 'templates/plot' + str(filenumber) + '.html'
        graph.savechart(filename)
        filenumber += 1


def start():
    data = get_data()
    data = create_multiIndex(data)
    data = fix_windspeed(data)
    data = fill_trace(data)
    data = fill_numeric_blanks(data)
    data = fill_descriptive_blanks(data)
    data = change_types(data)
    return data


@app.route('/')
def home():
    data = start()
    graph_names=['--Select a Graph --', '1. Average Rainfall vs. Location', '2. Average Temperature vs. Location', '3. Average Wind Speed vs. Wind Direction',
                 '4. Average Wind Speeds Categorized', '5. Average Rainfall Categorized', '6. Average Temperature Categorized', '7. Average Humidity Categorized']
    dates = list(set(data['Dates'].tolist()))
    dates = sorted(dates)
    dates.insert(0,'All')
    locations = list(set(data['Location'].tolist()))
    locations = sorted(locations)
    locations.insert(0, 'All')

    return render_template('home.html',
                           title='Weather Data', graph_list=graph_names, Dates=dates, locs=locations)


@app.route('/Display_graph', methods=['POST'])
def display_graphs():
    if request.method == 'POST':
        data = start()
        graph = request.form.get('selected_graph')[0]
        date = request.form.get('dates')
        location = request.form.get('location')

        if str(date) == 'None' and str(location) == 'None':
            data = data
        elif date != 'All' and location != 'All':
            data = data.loc[data['Dates'] == date]
            data = data.loc[data['Location'] == location]
        elif date == 'All' and location != 'All':
            data = data.loc[data['Location'] == location]
        elif date != 'All' and location == 'All':
            data = data.loc[data['Dates'] == date]
        elif date == 'All' and location == 'All':
            data = data

        if graph == '1':
            plot = create_graph1(data)
            script, div = components(plot)
            return render_template('graph.html', title='Weather Data', div=div, script=script)

        elif graph == '2':
            plot = create_graph2(data)
            script, div = components(plot)
            return render_template('graph.html', title='Weather Data', div=div, script=script)

        elif graph == '3':
            plot = create_graph3(data)
            script, div = components(plot)
            return render_template('graph.html', title='Weather Data', div=div, script=script)

        elif graph == '4':
            create_bins(data)
            return render_template('plot1.html', title='Weather Data')

        elif graph == '5':
            create_bins(data)
            return render_template('plot2.html', title='Weather Data')

        elif graph == '6':
            create_bins(data)
            return render_template('plot3.html', title='Weather Data')

        elif graph == '7':
            create_bins(data)
            return render_template('plot4.html', title='Weather Data')


if __name__ == "__main__":
    app.run(debug=True)