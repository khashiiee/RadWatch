# app/layouts/analysis.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime

def create_analysis_layout(data_processor):
    # Calculate time steps based on data
    start_date = data_processor.start_date
    end_date = data_processor.end_date

    return dbc.Container([
        # Time Controls Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Analysis Controls", className="fw-bold"),
                    dbc.CardBody([
                        dbc.Row([
                            # Date Range Selection
                            dbc.Col([
                                html.Label("Analysis Period:", className="fw-bold mb-2"),
                                dcc.DatePickerRange(
                                    id='analysis-date-range',
                                    start_date=start_date,
                                    end_date=end_date,
                                    display_format='YYYY-MM-DD',
                                    className="mb-3"
                                ),
                            ], width=6),
                            
                            # Time Step Selection
                            dbc.Col([
                                html.Label("Time Interval:", className="fw-bold mb-2"),
                                dcc.Dropdown(
                                    id='time-aggregation',
                                    options=[
                                        {'label': '15 Minutes', 'value': '15T'},
                                        {'label': '30 Minutes', 'value': '30T'},
                                        {'label': '1 Hour', 'value': '1H'},
                                        {'label': '2 Hours', 'value': '2H'},
                                        {'label': '4 Hours', 'value': '4H'},
                                        {'label': '12 Hours', 'value': '12H'},
                                        {'label': '1 Day', 'value': '1D'}
                                    ],
                                    value='1H',
                                    clearable=False
                                ),
                            ], width=6),
                        ], className="mb-3"),
                        
                        # Layer Selection
                        dbc.Row([
                            dbc.Col([
                                html.Label("Display Layers:", className="fw-bold mb-2"),
                                dbc.Checklist(
                                    id='analysis-layers',
                                    options=[
                                        {"label": "Static Sensors", "value": "static"},
                                        {"label": "Mobile Sensors", "value": "mobile"},
                                        {"label": "Static Radiation Heatmap", "value": "static_heatmap"},
                                        {"label": "Mobile Radiation Heatmap", "value": "mobile_heatmap"},
                                        {"label": "Neighborhood Boundaries", "value": "boundaries"}
                                    ],
                                    value=["static", "mobile", "boundaries"],
                                    inline=True
                                ),
                            ], width=12),
                        ]),
                    ])
                ], className="mb-3")
            ], width=12)
        ]),

        # Map and Timeline Container
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(html.H5("Radiation Analysis", className="mb-0"), width=6),
                            dbc.Col([
                                html.H5(id='current-timestamp', className="text-end mb-0")
                            ], width=6)
                        ])
                    ]),
                    dbc.CardBody([
                        # Map
                        dcc.Graph(id='analysis-map', style={'height': 'vh'}),
                        
                        # Timeline Controls
                        html.Div([
                            # Playback Controls
                            # dbc.ButtonGroup([
                            #     dbc.Button("⏮", id="first-frame", n_clicks=0, className="me-1"),
                            #     dbc.Button("⏪", id="prev-frame", n_clicks=0, className="me-1"),
                            #     dbc.Button(
                            #         html.I(className="fas fa-play"), 
                            #         id="playpause-button",
                            #         n_clicks=0,
                            #         className="me-1"
                            #     ),
                            #     dbc.Button("⏩", id="next-frame", n_clicks=0, className="me-1"),
                            #     dbc.Button("⏭", id="last-frame", n_clicks=0),
                            # ], className="mb-3 mt-3 d-flex justify-content-center"),
                            
                            # Timeline Slider with Marks
                            # dcc.Slider(
                            #     id='time-slider',
                            #     min=0,
                            #     max=100,
                            #     step=1,
                            #     value=0,
                            #     marks={},  # Will be updated by callback
                            #     tooltip={"placement": "bottom", "always_visible": True}
                            # ),
                            
                            # Animation Speed Control
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Animation Speed:", className="fw-bold mt-3 mb-2"),
                                    dcc.Slider(
                                        id='animation-speed',
                                        min=0.5,
                                        max=2,
                                        step=0.5,
                                        value=1,
                                        marks={
                                            0.5: 'Slow',
                                            1: 'Normal',
                                            2: 'Fast'
                                        }
                                    ),
                                ], width=12)
                            ], className="mt-3")
                        ], className="mt-3"),
                    ])
                ])
            ], width=12)
        ]),

        # Statistics Panel
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Time Period Statistics", className="fw-bold"),
                    dbc.CardBody(id='time-period-stats')
                ])
            ], width=12, className="mt-3")
        ]),
        
        # Store for timeline data
        dcc.Store(id='timeline-data'),
        # Store for animation state
        dcc.Store(id='animation-state', data={'is_playing': False}),
        # Interval for animation
        dcc.Interval(id='animation-interval', interval=1000, disabled=True)
    ], fluid=True)