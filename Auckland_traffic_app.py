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

df = pd.read_csv(r'data/traffic-counts_v1.csv', parse_dates = ['Count Start Date'])
df.set_index('Count Start Date', inplace = True)

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


#start_year = 2018
#start_month = 5
#start_day = 1
#end_year = 2018
#end_month = 6
#end_day = 1
#start_date = 1

volume_cols = ['5 Day ADT', '7 Day ADT', 'Saturday Volume', 'Sunday Volume',
       'AM Peak Volume', 'Mid Peak Volume', 'PM Peak Volume']
"""
Index(['Road Name', 'Carriageway Start Name', 'Carriageway End Name',
       '5 Day ADT', '7 Day ADT', 'Saturday Volume', 'Sunday Volume',
       'AM Peak Volume', 'AM Peak Hour', 'Mid Peak Volume', 'Mid Peak Hour',
       'PM Peak Volume', 'PM Peak Hour', 'Car', 'LCV', 'MCV', 'HCV-I',
       'HCV-II', 'HCV Total', 'latitude', 'longitude'],
      dtype='object')
"""

initial_col = volume_cols[0]
date_range_min = '2018-05-01'
date_rage_max = '2018-05-31'

# settings for the map

def create_visualization(df_, date_range_min_, date_rage_max_, col_, percentile = 80, radius = 10):
    colorscale = branca.colormap.linear.YlGnBu_09.scale(min(df_[col_]), max(df_[col_]))
    df_ = df_.loc[date_range_min_:date_rage_max_]
    df_ = df_[df_[col_] > np.nanpercentile(df_[col_], percentile)]
    
    m = folium.Map(location = [-36.848461, 174.763336])  #show Auckland
    for long, lat, volume, road in zip(df_['longitude'], df_['latitude'], df_[col_], df_['Road Name']):
        folium.CircleMarker(location=(lat, long),
                        popup = f'{road}:{volume}',
                        radius=radius,
                        color=colorscale(volume),
                        fill=True).add_to(m)
    m.save('Auckland_map.html')
#    m._repr_html_()
    return m
    
#create_visualization(df, date_range_min, date_rage_max, initial_col)
percentile_range = ['1%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '99%']
time_period_range = {'One month ahead':1, 'Two months ahead':2, 
                     'Three months ahead':3, 'Six months ahead':6, 'One year ahead':12, 'To the most recent date':60}
app.layout = html.Div([
    html.H1('Auckland Traffic'),
    
   
    html.Div([
        html.Div([
            
            html.Iframe(id = 'map', srcDoc = open('default_Auckland_map.html', 'r').read(), width = '90%', height = '600')
        ], className = 'seven columns'),
        # next div here    
        html.Div([
            html.Div([
                html.P('Select traffic volume metric:'),
                dcc.Dropdown(
                        id = 'volume_dropdown',
                        options = [{'label': col, 'value': col} for col in volume_cols],
                        value = initial_col
                        ),

                html.P('Select percentile:'),
                dcc.Dropdown(
                        id = 'percentile_dropdown',
                        options = [{'label': col, 'value': int(col.strip('%'))} for col in percentile_range],
            #            placeholder = '80%'
                        value = 80
                        ),
                html.P('Select time period:'),
                dcc.Dropdown(
                        id = 'time_period_dropdown',
                        options = [{'label': col, 'value': value} for col, value in time_period_range.items()],
                        value = 1,
            #            placeholder = 'One month ahead'
                        ),
                html.P('Select time:'),
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
                html.P(id = 'dispaly_info')
            ], className = 'four columns')
                
        ], className = 'row')
    ], className = 'row')

    
], className = 'row')

@app.callback(dash.dependencies.Output('dispaly_info', 'children'),
              [dash.dependencies.Input('volume_dropdown', 'value'),
                 dash.dependencies.Input('percentile_dropdown', 'value'),
                 dash.dependencies.Input('time_period_dropdown', 'value'), 
                 dash.dependencies.Input('datetime_Slider', 'value')
                 ])
def display_value(selected_volume, selected_pt, selected_period, selected_date_value):
    d = datetime.fromtimestamp(selected_date_value)
    d_ub = min(d + relativedelta(months = selected_period), pd.to_datetime(df.index.max())) 
    return f"Displaying '{selected_volume}' traffic records with volume that exceeds the upper {selected_pt}% percentile and are collected inbetween {d.strftime('%Y-%m-%d')} and {d_ub.strftime('%Y-%m-%d')}."

@app.callback(
    dash.dependencies.Output('map', 'srcDoc'),
    [dash.dependencies.Input('volume_dropdown', 'value'),
     dash.dependencies.Input('percentile_dropdown', 'value'),
     dash.dependencies.Input('time_period_dropdown', 'value'), 
     dash.dependencies.Input('datetime_Slider', 'value')
     ])
def update_map(selected_volume, selected_pt, selected_period, selected_date_value):
#    date_range_min = selected_date
    selected_date = datetime.fromtimestamp(selected_date_value)
    selected_date_ub = selected_date + relativedelta(months = selected_period)
    if selected_volume in volume_cols:
        create_visualization(df, selected_date.date(), selected_date_ub.date(), selected_volume, selected_pt, radius = 10)
        return open('Auckland_map.html', 'r').read()  #m._repr_html_()
#test = df.loc[selected_date:selected_date_ub]
#app.css.append_css({
#        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
#})
    
if __name__ == '__main__':
    app.run_server(debug=True)