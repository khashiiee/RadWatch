# # app/callbacks/analysis_callbacks.py
from dash.dependencies import Input, Output, State
from dash import callback_context
import pandas as pd
import json
from layouts.overview import create_overview_layout
from layouts.analysis import create_analysis_layout  # Add this import
from utils.mapping import MapVisualizer
from utils.data_processing import DataProcessor
from main import app


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




# Add info panel toggle callback
# app/callbacks/analysis_callbacks.py

@app.callback(
    Output('coverage-map', 'figure'),
    [Input('analysis-date-range', 'start_date'),
     Input('analysis-date-range', 'end_date')]
)
def update_coverage_analysis(start_date, end_date):
    """Update the coverage analysis map"""
    print("\n=== Coverage Analysis Callback Triggered ===")
    print(f"Date range: {start_date} to {end_date}")
    
    try:
        # Filter data for time period
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
        
        print(f"\nFiltered data stats:")
        print(f"Static readings: {len(filtered_static)} records")
        print(f"Mobile readings: {len(filtered_mobile)} records")
        
        # Create map
        map_viz = MapVisualizer()
        return map_viz.create_data_coverage_map(
            filtered_static,
            filtered_mobile,
            data_processor.static_sensors
        )
        
    except Exception as e:
        print(f"ERROR in coverage analysis callback: {str(e)}")
        import traceback
        print(traceback.format_exc())
        map_viz = MapVisualizer()
        return map_viz.create_base_map(['boundaries'])

def create_error_message_map(message):
    """Create a map with an error message overlay"""
    fig = go.Figure(go.Scattermapbox())
    fig.update_layout(
        annotations=[
            dict(
                text=f"Error: {message}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="red")
            )
        ]
    )
    return fig
