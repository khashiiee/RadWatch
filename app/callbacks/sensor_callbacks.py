# app/callbacks/sensor_callbacks.py
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Static Sensor Callbacks
@app.callback(
    [Output("static-sensor-count", "children"),
     Output("static-reading-count", "children"),
     Output("static-avg-radiation", "children"),
     Output("static-quality-score", "children")],
    [Input("static-time-range", "value")]
)
def update_static_metrics(time_range):
    # Get filtered data based on time range
    filtered_data = data_processor.filter_time_range(
        data_processor.static_readings,
        time_range[0],
        time_range[1]
    )
    
    # Calculate metrics
    sensor_count = len(filtered_data[DataProcessor.SENSOR_ID].unique())
    reading_count = len(filtered_data)
    avg_radiation = filtered_data[DataProcessor.VALUE].mean()
    
    # Calculate quality score (example metric)
    completeness = len(filtered_data) / (sensor_count * 24 * 60)  # Assuming minute-level data
    quality_score = min(100, completeness * 100)
    
    return (
        f"{sensor_count:,}",
        f"{reading_count:,} readings",
        f"{avg_radiation:.1f}",
        f"{quality_score:.0f}%"
    )

@app.callback(
    Output("static-time-series", "figure"),
    [Input("static-sensor-selector", "value"),
     Input("static-time-range", "value")]
)
def update_static_time_series(selected_sensors, time_range):
    if not selected_sensors:
        return go.Figure()
        
    # Filter data
    filtered_data = data_processor.static_readings[
        data_processor.static_readings[DataProcessor.SENSOR_ID].isin(selected_sensors)
    ]
    
    # Create time series
    fig = px.line(
        filtered_data,
        x=DataProcessor.TIMESTAMP,
        y=DataProcessor.VALUE,
        color=DataProcessor.SENSOR_ID,
        title="Radiation Levels Over Time"
    )
    
    return fig

@app.callback(
    Output("static-heatmap", "figure"),
    [Input("static-map-metric", "value")]
)
def update_static_heatmap(metric):
    # Merge readings with sensor locations
    data = pd.merge(
        data_processor.static_readings,
        data_processor.static_sensors,
        on=DataProcessor.SENSOR_ID
    )
    
    # Calculate selected metric
    if metric == 'avg':
        values = data.groupby(DataProcessor.SENSOR_ID)[DataProcessor.VALUE].mean()
    elif metric == 'max':
        values = data.groupby(DataProcessor.SENSOR_ID)[DataProcessor.VALUE].max()
    else:  # std
        values = data.groupby(DataProcessor.SENSOR_ID)[DataProcessor.VALUE].std()
    
    # Create heatmap
    map_viz = MapVisualizer()
    return map_viz.create_radiation_heatmap(data_processor.static_sensors, values)

# Mobile Sensor Callbacks
@app.callback(
    [Output("mobile-sensor-count", "children"),
     Output("mobile-user-count", "children"),
     Output("mobile-coverage", "children"),
     Output("contaminated-count", "children")],
    [Input("mobile-time-range", "value")]
)
def update_mobile_metrics(time_range):
    # Filter data
    filtered_data = data_processor.filter_time_range(
        data_processor.mobile_readings,
        time_range[0],
        time_range[1]
    )
    
    # Calculate metrics
    sensor_count = len(filtered_data[DataProcessor.SENSOR_ID].unique())
    user_count = len(filtered_data[DataProcessor.USER_ID].unique())
    
    # Calculate coverage area (example)
    min_lat = filtered_data[DataProcessor.LATITUDE].min()
    max_lat = filtered_data[DataProcessor.LATITUDE].max()
    min_lon = filtered_data[DataProcessor.LONGITUDE].min()
    max_lon = filtered_data[DataProcessor.LONGITUDE].max()
    coverage = (max_lat - min_lat) * (max_lon - min_lon) * 111  # Rough km² calculation
    
    # Count potentially contaminated vehicles
    contaminated = len(filtered_data[
        filtered_data[DataProcessor.VALUE] > data_processor.CONTAMINATION_THRESHOLD
    ][DataProcessor.SENSOR_ID].unique())
    
    return (
        f"{sensor_count:,}",
        f"{user_count:,} users",
        f"{coverage:.1f}",
        f"{contaminated:,}"
    )

@app.callback(
    Output("movement-map", "figure"),
    [Input("mobile-sensor-selector", "value"),
     Input("mobile-time-range", "value")]
)
def update_movement_map(selected_vehicles, time_range):
    if not selected_vehicles:
        return go.Figure()
        
    # Filter data
    filtered_data = data_processor.mobile_readings[
        data_processor.mobile_readings[DataProcessor.SENSOR_ID].isin(selected_vehicles)
    ]
    
    # Create movement visualization
    map_viz = MapVisualizer()
    return map_viz.create_vehicle_movement_map(filtered_data)

@app.callback(
    Output("sensor-comparison", "figure"),
    [Input("comparison-type", "value")]
)
def update_sensor_comparison(comparison_type):
    # Get static and mobile data
    static_data = data_processor.static_readings
    mobile_data = data_processor.mobile_readings
    
    if comparison_type == 'levels':
        # Create box plots comparing radiation levels
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=static_data[DataProcessor.VALUE],
            name="Static Sensors"
        ))
        fig.add_trace(go.Box(
            y=mobile_data[DataProcessor.VALUE],
            name="Mobile Sensors"
        ))
        fig.update_layout(
            title="Radiation Level Distribution Comparison",
            yaxis_title="Radiation Level (cpm)"
        )
    
    elif comparison_type == 'uncertainty':
        # Calculate and compare uncertainty
        static_uncertainty = static_data.groupby(DataProcessor.SENSOR_ID)[DataProcessor.VALUE].std()
        mobile_uncertainty = mobile_data.groupby(DataProcessor.SENSOR_ID)[DataProcessor.VALUE].std()
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=static_uncertainty,
            name="Static Sensors"
        ))
        fig.add_trace(go.Histogram(
            x=mobile_uncertainty,
            name="Mobile Sensors"
        ))
        fig.update_layout(
            title="Measurement Uncertainty Distribution",
            xaxis_title="Standard Deviation of Readings"
        )
    
    else:  # coverage
        # Compare coverage patterns
        fig = map_viz.create_coverage_comparison(static_data, mobile_data)
    
    return fig