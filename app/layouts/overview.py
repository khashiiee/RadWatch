# app/layouts/overview.py
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_processing import DataProcessor

def create_overview_layout(data_processor):
    stats = data_processor.get_sensor_stats()
    
    # Create time series plot with standardized column names
    hourly_data = data_processor.static_readings.copy()
    hourly_data['hour'] = hourly_data[DataProcessor.TIMESTAMP].dt.floor('H')
    hourly_avg = hourly_data.groupby('hour')[DataProcessor.VALUE].mean().reset_index()
    
    time_series_fig = px.line(
        hourly_avg, 
        x='hour', 
        y=DataProcessor.VALUE,
        title='Average Radiation Levels Over Time'
    )
    
    return dbc.Container([
        # Statistics Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Static Sensors", className="card-title"),
                        html.H2(f"{stats['static_sensor_count']}", className="text-primary"),
                        html.P(f"Total readings: {stats['static_reading_count']:,}")
                    ])
                ], className="mb-4")
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Mobile Sensors", className="card-title"),
                        html.H2(f"{stats['mobile_sensor_count']}", className="text-primary"),
                        html.P(f"Total readings: {stats['mobile_reading_count']:,}")
                    ])
                ], className="mb-4")
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Citizen Scientists", className="card-title"),
                        html.H2(f"{stats['unique_users']}", className="text-primary"),
                        html.P("Active participants")
                    ])
                ], className="mb-4")
            ], width=4)
        ]),
        
        # Map and Controls Container
        dbc.Row([
            # Map Column
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Sensor Network Map"),
                    dbc.CardBody([
                        dcc.Graph(id='sensor-map')
                    ])
                ])
            ], width=8),
            
            # Controls Column
            dbc.Col([
                # Time Range Selection
                dbc.Card([
                    dbc.CardHeader("Time Range"),
                    dbc.CardBody([
                        dcc.DatePickerRange(
                            id='date-range',
                            start_date=stats['date_range'][0],
                            end_date=stats['date_range'][1],
                            display_format='YYYY-MM-DD'
                        )
                    ])
                ], className="mb-4"),
                
                # Layer Controls
                dbc.Card([
                    dbc.CardHeader("Map Layers"),
                    dbc.CardBody([
                        dbc.Checklist(
                            id='map-layers',
                            options=[
                                {"label": "Static Sensors", "value": "static"},
                                {"label": "Mobile Sensors", "value": "mobile"},
                                {"label": "Neighborhood Boundaries", "value": "boundaries"},
                                {"label": "Radiation Heatmap", "value": "heatmap"}
                            ],
                            value=["static", "mobile", "boundaries"],
                            inline=False,
                            className="mb-2"
                        )
                    ])
                ])
            ], width=4)
        ]),

        # Time Series Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Radiation Levels Timeline"),
                    dbc.CardBody([
                        dcc.Graph(figure=time_series_fig, id='time-series-plot')
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True)