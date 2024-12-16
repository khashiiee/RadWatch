# app/layouts/home.py
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
from app.utils.data_processing import DataProcessor

def create_overview_tab():
    # Initialize data processor
    dp = DataProcessor()
    dp.load_data()
    stats = dp.get_sensor_stats()
    
    return dbc.Container([
        dbc.Row([
            # Stats cards
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Static Sensors", className="card-title"),
                        html.H2(str(stats['static_sensor_count'])),
                        html.P(f"Total readings: {stats['static_reading_count']:,}")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Mobile Sensors", className="card-title"),
                        html.H2(str(stats['mobile_sensor_count'])),
                        html.P(f"Total readings: {stats['mobile_reading_count']:,}")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Citizen Scientists", className="card-title"),
                        html.H2(str(stats['unique_users'])),
                        html.P("Active participants")
                    ])
                ])
            ], width=4)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Time Range Selection"),
                    dbc.CardBody([
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            start_date=stats['date_range'][0],
                            end_date=stats['date_range'][1],
                            display_format='YYYY-MM-DD'
                        )
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Radiation Levels Map"),
                    dbc.CardBody([
                        dcc.Graph(id='radiation-map')
                    ])
                ])
            ], width=12)
        ])
    ])