# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 16:38:30 2019

@author: KML
"""

#
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
#import folium
#import branca
from datetime import datetime
from dateutil.relativedelta import relativedelta
#import plotly.plotly as py
import plotly.graph_objs as go


mapbox_access_token = 'pk.eyJ1Ijoia2xpbjA1OSIsImEiOiJjanh3cjh2ZjYwOG1sM2xwYjM3Y3h0NzNwIn0.xpsBQqqKa3rdri09fsJ1OQ'

app = dash.Dash(__name__)
server = app.server
app.name = 'test'

df = pd.read_csv(r'data/merged_date.csv', parse_dates = ['count_date'])
df.set_index('count_date', inplace = True)
df.drop_duplicates(inplace = True)
df.sort_index(inplace = True)
df_original = df.copy()
df = df[df.index > '2010-12-01']  # for now set this restriction to limit resources
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

time_period_range = {'One month ahead':1,  
                     'Three months ahead':3, 'Six months ahead':6, 'One year ahead':12, 'To the most recent date':60}
max_volume = df['adt'].max()

def filter_data(df, date_range_min_ = '2010-01-01', date_rage_max_ = '2020-01-01', selected_volumes = [np.nanpercentile(df['adt'], 90), df['adt'].max()], min_sampling_count = 1):
    col_ = 'adt'
    if min_sampling_count > 1:
        df = df[df['sampling_count'] >= min_sampling_count]
    df = df.loc[date_range_min_:date_rage_max_]
    df = df[(df[col_] > selected_volumes[0]) & (df[col_] < selected_volumes[1])]
    return df

def define_data(df):
    return [go.Scattermapbox(
            lat=df['latitude'],
            lon=df['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=12,
                opacity = 0.5,
                color = df['adt'], 
                cmin = 0,
                cmax = max_volume,
                colorbar=dict(
                    title='Daily traffic count',
#                    tickvals = [0, max_volume]
                ), 
#                https://github.com/plotly/plotly.js/blob/5bc25b490702e5ed61265207833dbd58e8ab27f1/src/components/colorscale/scales.js
                colorscale='Reds'
            ),
            text=df['road_name'],
        )]
def define_layout():
    return go.Layout(
#        autosize=True,
        width = 850,
        height = 400,        
        margin={'l': 10, 'b': 10, 't': 10, 'r': 10},
        hovermode='closest',
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=-36.848461,
                lon=174.763336
            ),
            pitch=0,
            zoom=9
        ),
    )
    
#def create_fig(df, date_range_min_ = '2010-01-01', date_rage_max_ = '2020-01-01', selected_volumes = [np.nanpercentile(df['adt'], 90), df['adt'].max()]):
##    col_ = 'adt'
#    df = filter_data(df)
#    data = define_data(df)
#    layout = define_layout()
#    fig = go.Figure(data=data, layout=layout)
#    return fig

sampling_count = df['sampling_count'].unique()
sampling_count.sort()

app.layout = html.Div([
        html.H3('Auckland Traffic Visualization'),
        html.P(id = 'dispaly_info'),
        html.Div([
            dcc.Graph(id='Auck_map',
#              figure = create_fig(df),
#              animate=True,
#                  style={'margin-top': '20'}
            ), 
            html.P('Click on the marker to display historical traffic counts'),
            dcc.Graph(id = 'time_series_plot')
            
                   
        ], className = 'seven columns'), 
        html.Div([
            html.H4('Select traffic volume range:'),
            dcc.RangeSlider(
                        id='volume_slider',
                        min=0,
                        max=df['adt'].max(),
                        step=1000,
                        value=[0, df['adt'].max()]
                    ),
                
            html.P(id = 'volume_slider_display'),
            ##
            html.H4('Select time period:'),
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
                    value = 60,
                    clearable = False
        #            placeholder = 'One month ahead'
            ),                
            
            html.P(id = 'time_period_display'),
            html.H4('Filter by number of historical traffic counts:'),
            dcc.Dropdown(
                    id = 'sampling_count_dropdown',
                    options = [{'label': value, 'value': value} for value in sampling_count],
                    value = 1,
                    clearable = False
        #            placeholder = 'One month ahead'
            ),
            
        ], className = 'four columns')
            
        
        
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
    dash.dependencies.Output('Auck_map', 'figure'),
    [#dash.dependencies.Input('volume_dropdown', 'value'),
     dash.dependencies.Input('volume_slider', 'value'),
     dash.dependencies.Input('time_period_dropdown', 'value'), 
     dash.dependencies.Input('datetime_Slider', 'value'),
     dash.dependencies.Input('sampling_count_dropdown', 'value')     
     ])
def update_map(selected_volumes, selected_period, selected_date_value, min_sampling_count):
#    date_range_min = selected_date
    selected_date = datetime.fromtimestamp(selected_date_value)
    selected_date_ub = selected_date + relativedelta(months = selected_period)
#    create_fig(df, date_range_min_ = '2010-01-01', date_rage_max_ = '2020-01-01', selected_volumes = [np.nanpercentile(df['adt'], 90), df['adt'].max()]):
    df_sub = filter_data(df, selected_date.date(), selected_date_ub.date(), selected_volumes, min_sampling_count)
    data = define_data(df_sub)
    layout = define_layout()
    return {'data':data, 'layout':layout}  #m._repr_html_()

def filter_data_by_coord(df, lon, lat):
    return df[(df['longitude'] == lon) & (df['latitude'] == lat)]

@app.callback(
    dash.dependencies.Output('time_series_plot', 'figure'),
    [dash.dependencies.Input('Auck_map', 'clickData')])
def display_click_data(clickData):
    if not clickData:
        data = []
    else:
#    print(clickData)
        lon = clickData['points'][0]['lon']
        lat = clickData['points'][0]['lat']
        road_name = clickData['points'][0]['text']
        df_sub = filter_data_by_coord(df_original, lon, lat)
        df_sub.sort_index(inplace = True)
        data = [go.Scatter(x = df_sub.index, y = df_sub['adt'], name = road_name)]
    layout = dict(title = 'Historical traffic counts',
              xaxis = dict(title = 'Date'),
              yaxis = dict(title = 'Daily average traffoc count'),
              )
    return {'data':data, 'layout':layout}
#{
#  "points": [
#    {
#      "curveNumber": 0,
#      "pointNumber": 2,
#      "pointIndex": 2,
#      "lon": 174.78764336020313,
#      "lat": -36.93212108018415,
#      "text": "SH 020-0010/02.54-D",
#      "marker.color": 62559
#    }
#  ]
#}


#py.iplot(fig, filename='Montreal Mapbox')


if __name__ == '__main__':
    app.run_server(debug=True)