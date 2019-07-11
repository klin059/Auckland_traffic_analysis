# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 16:19:00 2019

@author: KML
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import folium
import branca
from datetime import datetime
from dateutil.relativedelta import relativedelta



app = dash.Dash(__name__)
server = app.server

df = pd.read_csv(r'data/merged_date.csv', parse_dates = ['count_date'])
df.set_index('count_date', inplace = True)
df.drop_duplicates(inplace = True)
df.sort_index(inplace = True)
df = df[df.index > '2016-12-01']  # for now set this restriction to limit resources
epoch = datetime.utcfromtimestamp(0)
def unix_time_millis(dt):
    return (dt - epoch).total_seconds() #* 1000.0

def get_marks_from_start_end(start, end):
    ''' Returns dict with one item per month
    {1440080188.1900003: '2015-08',
    '''
    result = []
    current = start
    while current <= end:
        result.append(current)
        current += relativedelta(months=1)
    return {unix_time_millis(m):(str(m.strftime('%Y-%m'))) for m in result}
min_date, max_date = unix_time_millis(pd.to_datetime(df.index.min())), unix_time_millis(pd.to_datetime(df.index.max()))

#volume_cols = ['5 Day ADT', '7 Day ADT', 'Saturday Volume', 'Sunday Volume',
#       'AM Peak Volume', 'Mid Peak Volume', 'PM Peak Volume']
#"""
#Index(['Road Name', 'Carriageway Start Name', 'Carriageway End Name',
#       '5 Day ADT', '7 Day ADT', 'Saturday Volume', 'Sunday Volume',
#       'AM Peak Volume', 'AM Peak Hour', 'Mid Peak Volume', 'Mid Peak Hour',
#       'PM Peak Volume', 'PM Peak Hour', 'Car', 'LCV', 'MCV', 'HCV-I',
#       'HCV-II', 'HCV Total', 'latitude', 'longitude'],
#      dtype='object')
#"""

initial_col = 'adt'
#date_range_min = '2018-05-01'
#date_rage_max = '2018-05-31'

# settings for the map

def create_visualization(df_, date_range_min_, date_rage_max_, selected_volumes, radius = 10):
    col_ = 'adt'
    colorscale = branca.colormap.linear.YlGnBu_09.scale(0, max(df_[col_]))
    df_ = df_.loc[date_range_min_:date_rage_max_]
    df_ = df_[(df_[col_] > selected_volumes[0]) & (df_[col_] < selected_volumes[1])]
    
    m = folium.Map(location = [-36.848461, 174.763336])  #show Auckland
    for long, lat, volume, road, date in zip(df_['longitude'], df_['latitude'], df_[col_], df_['road_name'], df_.index):
        folium.CircleMarker(location=(lat, long),
                        popup = f'road:{road}, volume:{volume}, date:{date}',
                        radius=radius,
                        color=colorscale(volume),
                        fill=True).add_to(m)
    cmap = colorscale.to_step(10)
    cmap.caption = "7-day average daily traffic count"
    cmap.add_to(m)
    m.save('Auckland_map.html')
#    m._repr_html_()
    return m

def get_df_sub_by_coord(df, long, lat):
    # get records of a certain coordinate
    return df[(df['longitude'] == long) & (df['latitude'] == lat)]

#def plot_time_series(df, long, lat):
#    temp = get_df_sub_by_coord(df, long, lat)
#    plt.plot(temp['adt'])
    
#create_visualization(df, date_range_min, date_rage_max, initial_col)
#percentile_range = ['1%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '99%']
time_period_range = {'One month ahead':1, 'Two months ahead':2, 
                     'Three months ahead':3, 'Six months ahead':6, 'One year ahead':12, 'To the most recent date':60}
app.layout = html.Div([
    html.H1('Auckland Traffic Visualization'),
    html.P(id = 'dispaly_info'),
   
    html.Div([
        html.Div([
            html.Iframe(id = 'map', srcDoc = open('default_Auckland_map.html', 'r').read(), width = '90%', height = '600')
        ], className = 'seven columns'),
        # next div here    
        html.Div([
            html.Div([
                html.H3('Select traffic volume range:'),
                dcc.RangeSlider(
                        id='volume_slider',
                        min=0,
                        max=df['adt'].max(),
                        step=1000,
                        value=[30000, df['adt'].max()]
                    ),
                
                html.P(id = 'volume_slider_display'),
#                dcc.Dropdown(
#                        id = 'percentile_dropdown',
#                        options = [{'label': p, 'value': int(p.strip('%'))} for p in percentile_range],
#            #            placeholder = '80%'
#                        value = 80
#                        ),
                html.H3('Select time period:'),
                html.P('Time period start date:'),
                dcc.Slider(
                        id = 'datetime_Slider',
                        updatemode = 'mouseup', #don't let it update till mouse released
                        min = min_date,
                        max = max_date,
                        value = unix_time_millis(pd.to_datetime(df.index.min())),
                        step = unix_time_millis(pd.to_datetime('20180601')) - unix_time_millis(pd.to_datetime('20180501')),
                        # add markers for key dates
                        marks=get_marks_from_start_end(pd.to_datetime(df.index.min()),
                                                       pd.to_datetime(df.index.max()))
                        ),
                html.P('Select period length:'),
                dcc.Dropdown(
                        id = 'time_period_dropdown',
                        options = [{'label': ind, 'value': value} for ind, value in time_period_range.items()],
                        value = 1,
            #            placeholder = 'One month ahead'
                        ),                
                
                html.P(id = 'time_period_display')
            ], className = 'four columns')
                
        ], className = 'row')
    ], className = 'row')

    
], className = 'row')

@app.callback(dash.dependencies.Output('time_period_display', 'children'),
              [dash.dependencies.Input('time_period_dropdown', 'value'), 
                 dash.dependencies.Input('datetime_Slider', 'value')])
def display_time_period(selected_period, selected_date_value):
    d = datetime.fromtimestamp(selected_date_value)
    d_ub = min(d + relativedelta(months = selected_period), pd.to_datetime(df.index.max()))
    return f"Selecting dates between {d.strftime('%Y-%m-%d')} to {d_ub.strftime('%Y-%m-%d')}"

@app.callback(dash.dependencies.Output('volume_slider_display', 'children'),
              [dash.dependencies.Input('volume_slider', 'value')])
def display_volume_slider_range(volumes):
    return f'Selecting traffic volume between {volumes[0]} and {volumes[1]}'

@app.callback(dash.dependencies.Output('dispaly_info', 'children'),
              [dash.dependencies.Input('volume_slider', 'value'),
                 dash.dependencies.Input('time_period_dropdown', 'value'), 
                 dash.dependencies.Input('datetime_Slider', 'value')
                 ])
def display_value(selected_volumes, selected_period, selected_date_value):
    d = datetime.fromtimestamp(selected_date_value)
    d_ub = min(d + relativedelta(months = selected_period), pd.to_datetime(df.index.max())) 
    return f"Displaying 7-day average daily traffic records collected from {d.strftime('%Y-%m-%d')} to {d_ub.strftime('%Y-%m-%d')} with traffic count between {selected_volumes[0]} and {selected_volumes[1]}."

@app.callback(
    dash.dependencies.Output('map', 'srcDoc'),
    [#dash.dependencies.Input('volume_dropdown', 'value'),
     dash.dependencies.Input('volume_slider', 'value'),
     dash.dependencies.Input('time_period_dropdown', 'value'), 
     dash.dependencies.Input('datetime_Slider', 'value')
     ])
def update_map(selected_volumes, selected_period, selected_date_value):
#    date_range_min = selected_date
    selected_date = datetime.fromtimestamp(selected_date_value)
    selected_date_ub = selected_date + relativedelta(months = selected_period)
    create_visualization(df, selected_date.date(), selected_date_ub.date(), selected_volumes, radius = 10)
    return open('Auckland_map.html', 'r').read()  #m._repr_html_()
#test = df.loc[selected_date:selected_date_ub]
#app.css.append_css({
#        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
#})
    
if __name__ == '__main__':
    app.run_server(debug=True)