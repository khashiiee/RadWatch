# app/layouts/static_sensors.py

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go


def create_static_sensors_layout(data_processor):
    """Create the layout for the static sensors tab"""
    return dbc.Container([
        # Top row - Overview metrics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Total Static Sensors"),
                        html.H2(id="static-sensor-count", className="text-primary"),
                        html.P(id="static-reading-count")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Average Radiation Level"),
                        html.H2(id="static-avg-radiation", className="text-info"),
                        html.P("counts per minute (cpm)")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Data Quality Score"),
                        html.H2(id="static-quality-score", className="text-success"),
                        html.P(id="quality-description")
                    ])
                ])
            ], width=4),
        ], className="mb-4"),

        # Second row - Time series and map
        dbc.Row([
            # Left column - Time series
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Radiation Levels Over Time"),
                        dcc.Dropdown(
                            id='static-sensor-selector',
                            placeholder="Select sensors to display...",
                            multi=True
                        ),
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id='static-time-series'),
                        dcc.RangeSlider(
                            id='static-time-range',
                            min=0,
                            max=10,
                            step=2,
                            value=[0, 10]
                        )
                    ])
                ])
            ], width=8),
            
            # Right column - Statistics
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Sensor Statistics"),
                    dbc.CardBody([
                        html.Div(id='static-sensor-stats'),
                        dcc.Graph(id='static-boxplot')
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        # Third row - Heatmap and patterns
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Spatial Distribution"),
                        dbc.RadioItems(
                            id='static-map-metric',
                            options=[
                                {'label': 'Average Radiation', 'value': 'avg'},
                                {'label': 'Maximum Radiation', 'value': 'max'},
                                {'label': 'Uncertainty', 'value': 'std'}
                            ],
                            value='avg',
                            inline=True
                        )
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id='static-heatmap')
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Temporal Patterns"),
                        dbc.RadioItems(
                            id='static-pattern-type',
                            options=[
                                {'label': 'Daily', 'value': 'daily'},
                                {'label': 'Weekly', 'value': 'weekly'},
                                {'label': 'Monthly', 'value': 'monthly'}
                            ],
                            value='daily',
                            inline=True
                        )
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id='static-patterns')
                    ])
                ])
            ], width=6)
        ])
    ], fluid=True)

