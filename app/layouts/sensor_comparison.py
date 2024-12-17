# app/layouts/sensor_comparison.py
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px

def create_comparison_layout(data_processor):
    """Create layout for comparing static and mobile sensors with improved visualization"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("Static vs Mobile Sensor Comparison", className="mb-4")
            ])
        ]),
        
        # Time Range Selection
        dbc.Row([
            dbc.Col([
                html.Label("Select Time Range"),
                dcc.DatePickerRange(
                    id='comparison-date-range',
                    start_date=data_processor.start_date,
                    end_date=data_processor.end_date,
                    className="mb-3"
                )
            ])
        ]),
        
        # Coverage Statistics Card with Detailed Breakdown
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Coverage Statistics"),
                    dbc.CardBody([
                        dbc.Row([
                            # Static Sensors Stats
                            dbc.Col([
                                html.H6("Static Sensors", className="text-primary"),
                                html.Div(id="static-coverage-stats")
                            ], width=6),
                            # Mobile Sensors Stats
                            dbc.Col([
                                html.H6("Mobile Sensors", className="text-success"),
                                html.Div(id="mobile-coverage-stats")
                            ], width=6)
                        ]),
                        # Overall Coverage
                        html.Div(id="overall-coverage-stats", className="mt-3")
                    ])
                ], className="mb-4")
            ])
        ]),
        
        # Map and Analysis Options
        dbc.Row([
            # Map
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Sensor Coverage Comparison"),
                    dbc.CardBody([
                        # Analysis Options Inline
                        dbc.Row([
                            dbc.Col([
                                html.Label("View Options:"),
                                dbc.RadioItems(
                                    id="comparison-metric",
                                    options=[
                                        {"label": " Average Radiation", "value": "avg"},
                                        {"label": " Maximum Radiation", "value": "max"},
                                        {"label": " Reading Frequency", "value": "freq"},
                                        {"label": " Coverage Area", "value": "coverage"}
                                    ],
                                    value="avg",
                                    inline=True,
                                    className="mb-3"
                                ),
                            ])
                        ]),
                        # Map with increased size
                        dcc.Graph(
                            id="comparison-map",
                            style={"height": "600px"},
                            config={'displayModeBar': True}
                        )
                    ])
                ], className="mb-4")
            ], width=12)
        ]),
        
        # Comparison Charts
        dbc.Row([
            # Time series comparison
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Radiation Readings Over Time"),
                    dbc.CardBody([
                        dcc.Graph(id="comparison-timeseries")
                    ])
                ], className="mb-4")
            ], width=6),
            
            # Statistical comparison
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Statistical Comparison"),
                    dbc.CardBody([
                        dcc.Graph(id="comparison-stats")
                    ])
                ], className="mb-4")
            ], width=6)
        ])
        
    ])