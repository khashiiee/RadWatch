# app/main.py
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
from utils.data_processing import DataProcessor
from layouts.overview import create_overview_layout
from layouts.analysis import create_analysis_layout  # Add this import
from utils.mapping import MapVisualizer
import os

# Initialize the Dash app
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    'https://use.fontawesome.com/releases/v5.15.4/css/all.css'
                ],
                suppress_callback_exceptions=True)

# Initialize data processor
data_processor = DataProcessor()
loading_success = data_processor.load_data()

# Create the app layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("RadWatch - St. Himark Radiation Monitoring",
                   className="text-center mb-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Overview", tab_id="tab-overview"),
                dbc.Tab(label="Static Sensors", tab_id="tab-static"),
                dbc.Tab(label="Mobile Sensors", tab_id="tab-mobile"),
                dbc.Tab(label="Analysis", tab_id="tab-analysis")
            ], id="tabs", active_tab="tab-overview")
        ])
    ]),
    
    html.Div(id="tab-content")
], fluid=True)

# Tab content callback
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab')
)
def render_tab_content(active_tab):
    if active_tab == "tab-overview":
        return create_overview_layout(data_processor)
    elif active_tab == "tab-static":
        return html.P("Static Sensors Analysis - Coming Soon")
    elif active_tab == "tab-mobile":
        return html.P("Mobile Sensors Analysis - Coming Soon")
    elif active_tab == "tab-analysis":
        return create_analysis_layout(data_processor)
    return "No content"

# Overview map callback
@app.callback(
    Output('sensor-map', 'figure'),
    Input('map-layers', 'value')
)
def update_map_layers(active_layers):
    print("\n=== Map Callback Triggered ===")
    print(f"Active layers selected: {active_layers}")
    
    try:
        # Create new map with selected layers
        map_viz = MapVisualizer()
        map_fig = map_viz.create_base_map(active_layers=active_layers)
        
        if active_layers:
            # Add sensors
            map_fig = map_viz.add_sensors(
                map_fig,
                data_processor.static_sensors,
                data_processor.mobile_readings,
                active_layers=active_layers
            )
            
            # Add heatmap with both static sensors and readings
            if 'heatmap' in active_layers:
                map_fig = map_viz.add_radiation_heatmap(
                    map_fig,
                    data_processor.static_readings,
                    data_processor.static_sensors,
                    active_layers=active_layers
                )
        
        return map_fig
        
    except Exception as e:
        print(f"ERROR in map callback: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        raise

# Analysis map callback
@app.callback(
    [Output('analysis-map', 'figure'),
     Output('time-period-stats', 'children')],
    [Input('analysis-layers', 'value'),
     Input('analysis-date-range', 'start_date'),
     Input('analysis-date-range', 'end_date'),
     Input('time-aggregation', 'value'),
     Input('animation-speed', 'value')]
)
def update_analysis_view(active_layers, start_date, end_date, time_agg, animation_speed):
    print("\n=== Analysis View Update ===")
    try:
        # Initialize map
        map_viz = MapVisualizer()
        fig = map_viz.create_base_map(active_layers=active_layers)
        
        if active_layers:
            # Filter data by time range
            static_data = data_processor.filter_time_range(
                data_processor.static_readings, 
                start_date, 
                end_date
            )
            mobile_data = data_processor.filter_time_range(
                data_processor.mobile_readings, 
                start_date, 
                end_date
            )
            
            # Create animated visualization
            if 'static' in active_layers or 'static_heatmap' in active_layers:
                fig = map_viz.add_animated_radiation_data(
                    fig, 
                    static_data,
                    data_processor.static_sensors,
                    'static',
                    time_agg,
                    animation_speed,
                    active_layers
                )
                
            if 'mobile' in active_layers or 'mobile_heatmap' in active_layers:
                fig = map_viz.add_animated_radiation_data(
                    fig,
                    mobile_data,
                    None,  # Mobile sensors have coordinates in readings
                    'mobile',
                    time_agg,
                    animation_speed,
                    active_layers
                )
            
            # Calculate statistics
            stats = data_processor.calculate_period_statistics(static_data, mobile_data)
            stats_display = create_stats_display(stats)
        else:
            stats_display = "No layers selected"
        
        return fig, stats_display
        
    except Exception as e:
        print(f"ERROR in analysis view: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

def create_stats_display(stats):
    """Create HTML elements for statistics display"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5("Static Sensors"),
                html.P(f"Average Radiation: {stats['static_mean']:.2f} cpm"),
                html.P(f"Max Radiation: {stats['static_max']:.2f} cpm"),
                html.P(f"Number of Readings: {stats['num_static_readings']:,}")
            ], width=6),
            dbc.Col([
                html.H5("Mobile Sensors"),
                html.P(f"Average Radiation: {stats['mobile_mean']:.2f} cpm"),
                html.P(f"Max Radiation: {stats['mobile_max']:.2f} cpm"),
                html.P(f"Number of Readings: {stats['num_mobile_readings']:,}"),
                html.P(f"Active Sensors: {stats['unique_mobile_sensors']}")
            ], width=6)
        ])
    ])

@app.callback(
    [Output('affected-areas-map', 'figure'),
     Output('affected-areas-stats', 'children')],
    [Input('radiation-threshold', 'value'),
     Input('analysis-date-range', 'start_date'),
     Input('analysis-date-range', 'end_date')]
)
def update_affected_areas_analysis(threshold_range, start_date, end_date):
    """Update the affected areas map and statistics based on the threshold range"""
    # Filter data for the selected time period
    filtered_static = data_processor.filter_time_range(
        data_processor.static_readings,
        start_date,
        end_date
    )
    filtered_mobile = data_processor.filter_time_range(
        data_processor.mobile_readings,
        start_date,
        end_date
    )
    
    # Create map
    map_viz = MapVisualizer()
    fig = map_viz.create_affected_areas_map(
        filtered_mobile,
        threshold_range,
        static_sensors=data_processor.static_sensors
    )
    
    # Calculate statistics
    min_threshold, max_threshold = threshold_range
    static_affected = filtered_static[
        (filtered_static[DataProcessor.VALUE] >= min_threshold) & 
        (filtered_static[DataProcessor.VALUE] <= max_threshold)
    ]
    mobile_affected = filtered_mobile[
        (filtered_mobile[DataProcessor.VALUE] >= min_threshold) & 
        (filtered_mobile[DataProcessor.VALUE] <= max_threshold)
    ]
    
    stats_html = html.Div([
        dbc.Row([
            dbc.Col([
                html.H5(f"Radiation Levels: {min_threshold} - {max_threshold} cpm"),
                html.P([
                    html.Strong("Static Sensors: "),
                    f"{len(static_affected[DataProcessor.SENSOR_ID].unique())} affected sensors",
                ]),
                html.P([
                    html.Strong("Mobile Readings: "),
                    f"{len(mobile_affected)} readings in range",
                ]),
                html.P([
                    html.Strong("Average Radiation: "),
                    f"{mobile_affected[DataProcessor.VALUE].mean():.2f} cpm",
                ]),
            ])
        ])
    ])
    
    return fig, stats_html



if __name__ == '__main__':
    app.run_server(debug=True)