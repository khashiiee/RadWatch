# app/layouts/mobile_sensors.py
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go


def create_mobile_sensors_layout(data_processor):
    """Create the layout for the mobile sensors tab"""
    return dbc.Container([
        # Top row - Overview metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Active Mobile Sensors"),
                        html.H2(id="mobile-sensor-count", className="text-primary"),
                        html.P(id="mobile-user-count")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Coverage Area"),
                        html.H2(id="mobile-coverage", className="text-info"),
                        html.P("square kilometers")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Potentially Contaminated"),
                        html.H2(id="contaminated-count", className="text-warning"),
                        html.P("vehicles identified")
                    ])
                ])
            ], width=4),
        ], className="mb-4"),

        # Second row - Movement tracking
       dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Vehicle Movement Tracking"),
                        dcc.Dropdown(
                            id='mobile-sensor-selector',
                            placeholder="Select vehicles to track...",
                            multi=True
                        ),
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id='movement-map'),
                        dcc.RangeSlider(
                            id='mobile-time-range',
                            min=0,
                            max=10,
                            step=1,
                            value=[0, 10]
                        )
                    ])
                ])
            ], width=8),
            
            
            # Right column - Vehicle stats
           dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Vehicle Statistics"),
                    dbc.CardBody([
                        dcc.Graph(id='mobile-time-series'),
                        html.Div(id='mobile-sensor-stats')
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        # Third row - Coverage and comparison
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Coverage Analysis"),
                        dbc.RadioItems(
                            id='coverage-metric',
                            options=[
                                {'label': 'Time Coverage', 'value': 'time'},
                                {'label': 'Spatial Coverage', 'value': 'spatial'},
                                {'label': 'Data Density', 'value': 'density'}
                            ],
                            value='spatial',
                            inline=True
                        )
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id='coverage-map')
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Static vs Mobile Comparison"),
                        dbc.RadioItems(
                            id='comparison-type',
                            options=[
                                {'label': 'Radiation Levels', 'value': 'levels'},
                                {'label': 'Uncertainty', 'value': 'uncertainty'},
                                {'label': 'Coverage', 'value': 'coverage'}
                            ],
                            value='levels',
                            inline=True
                        )
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id='sensor-comparison')
                    ])
                ])
            ], width=6)
        ])
    ], fluid=True)