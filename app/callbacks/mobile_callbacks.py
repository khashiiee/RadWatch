import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from utils.mapping import MapVisualizer

def register_callbacks(app, data_processor):
    """Register all mobile sensor related callbacks"""
    
    # Initialize time range and sensor selector
    @app.callback(
        [Output('mobile-time-range', 'min'),
         Output('mobile-time-range', 'max'),
         Output('mobile-time-range', 'marks'),
         Output('mobile-time-range', 'value')],
        [Input('tabs', 'active_tab')]
    )
    def init_mobile_controls(active_tab):
        if active_tab != "tab-mobile":
            raise PreventUpdate
        
        try:
            # Get time range from data
            min_time = data_processor.mobile_readings['timestamp'].min().timestamp()
            max_time = data_processor.mobile_readings['timestamp'].max().timestamp()
            
            # Create marks every 6 hours
            time_points = pd.date_range(
                start=pd.Timestamp.fromtimestamp(min_time),
                end=pd.Timestamp.fromtimestamp(max_time),
                freq='6H'
            )
            marks = {
                int(t.timestamp()): t.strftime('%m/%d %h:%M')
                for t in time_points
            }
            
            return min_time, max_time, marks, [min_time, max_time]
        except Exception as e:
            print(f"Error initializing mobile controls: {str(e)}")
            return 0, 1, {}, [0, 1]

    @app.callback(
    [Output('mobile-sensor-selector', 'options'),
     Output('mobile-sensor-selector', 'value')],  # Add value output
    [Input('tabs', 'active_tab')]
    )
    def init_sensor_dropdown(active_tab):
        if active_tab != "tab-mobile":
            raise PreventUpdate
            
        try:
            # Get unique sensor IDs with reading counts
            sensor_counts = data_processor.mobile_readings['sensor_id'].value_counts()
            
            options = [
                {'label': f'Vehicle {sid} ({count} readings)', 'value': sid}
                for sid, count in sensor_counts.items()
            ]
            
            # Sort options by value
            sorted_options = sorted(options, key=lambda x: x['value'])
            
            # Select the first sensor by default
            default_value = sorted_options[0]['value'] if sorted_options else None
            
            return sorted_options, default_value
            
        except Exception as e:
            print(f"Error initializing sensor dropdown: {str(e)}")
            return [], None

    # Overview metrics
    @app.callback(
        [Output('mobile-sensor-count', 'children'),
         Output('mobile-user-count', 'children'),
         Output('mobile-coverage', 'children'),
         Output('contaminated-count', 'children')],
        [Input('tabs', 'active_tab'),
         Input('mobile-time-range', 'value')]
    )
    def update_mobile_metrics(active_tab, time_range):
        if active_tab != "tab-mobile":
            raise PreventUpdate
            
        try:
            # Filter by time range
            filtered_data = data_processor.mobile_readings
            if time_range:
                start_time = pd.to_datetime(time_range[0], unit='s')
                end_time = pd.to_datetime(time_range[1], unit='s')
                filtered_data = filtered_data[
                    (filtered_data['timestamp'] >= start_time) &
                    (filtered_data['timestamp'] <= end_time)
                ]
            
            # Calculate metrics
            sensor_count = len(filtered_data['sensor_id'].unique())
            user_count = len(filtered_data['user_id'].unique())
            
            # Calculate coverage (unique locations * approx area per point)
            unique_locs = filtered_data[['latitude', 'longitude']].drop_duplicates()
            coverage = len(unique_locs) * 0.01  # km² (approximate)
            
            # Count potentially contaminated vehicles (above threshold)
            threshold = 35  # cpm
            contaminated = len(filtered_data[
                filtered_data['value'] > threshold
            ]['sensor_id'].unique())
            
            return (
                str(sensor_count),
                f"{user_count} unique users",
                f"{coverage:.1f}",
                str(contaminated)
            )
        except Exception as e:
            print(f"Error updating metrics: {str(e)}")
            return "N/A", "N/A users", "0.0", "N/A"

    # Vehicle movement tracking
    @app.callback(
        Output('movement-map', 'figure'),
        [Input('mobile-sensor-selector', 'value'),
         Input('mobile-time-range', 'value'),
         Input('tabs', 'active_tab')]
    ) 
    def update_vehicle_tracking(selected_sensors, time_range, active_tab):
        if not selected_sensors or active_tab != "tab-mobile":
            raise PreventUpdate
            
        try:
            # Filter data
            if not isinstance(selected_sensors, list):
                selected_sensors = [selected_sensors]
                
            filtered_data = data_processor.mobile_readings[
                data_processor.mobile_readings['sensor_id'].isin(selected_sensors)
            ]
            
            if time_range:
                start_time = pd.to_datetime(time_range[0], unit='s')
                end_time = pd.to_datetime(time_range[1], unit='s')
                filtered_data = filtered_data[
                    (filtered_data['timestamp'] >= start_time) &
                    (filtered_data['timestamp'] <= end_time)
                ]
            
            # Create base map
            map_viz = MapVisualizer()
            fig = map_viz.create_base_map()
            
            
            
            # Add vehicle paths
            for sensor_id in selected_sensors:
                sensor_data = filtered_data[
                    filtered_data['sensor_id'] == sensor_id
                ].sort_values('timestamp')
                
                if len(sensor_data) > 0:
                    # Add path line with radiation color scale
                    fig.add_trace(go.Scattermapbox(
                        lat=sensor_data['latitude'],
                        lon=sensor_data['longitude'],
                        mode='lines+markers',
                        name=f'Vehicle {sensor_id}',
                        line=dict(width=2),
                        marker=dict(
                            size=8,
                            color=sensor_data['value'],
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(title='Radiation (cpm)')
                        ),
                        hovertemplate=(
                            'Vehicle %{text}<br>' +
                            'Time: %{customdata}<br>' +
                            'Radiation: %{marker.color:.1f} cpm<br>' +
                            '<extra></extra>'
                        ),
                        text=[f'{sensor_id}'] * len(sensor_data),
                        customdata=sensor_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                    ))
            
            # Update layout
            center_lat = filtered_data['latitude'].mean()
            center_lon = filtered_data['longitude'].mean()
            
            fig.update_layout(
                mapbox=dict(
                    style='carto-positron',
                    zoom=12,
                    center=dict(lat=center_lat, lon=center_lon)
                ),
                margin=dict(l=0, r=0, t=10, b=10),
                # height=500,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            print(f"Error updating vehicle tracking: {str(e)}")
            return create_empty_map()

    # Vehicle statistics
    @app.callback(
        [Output('mobile-time-series', 'figure'),
         Output('mobile-sensor-stats', 'children')],
        [Input('mobile-sensor-selector', 'value'),
         Input('mobile-time-range', 'value'),
         Input('tabs', 'active_tab')]
    )
    def update_vehicle_stats(selected_sensors, time_range, active_tab):
        if not selected_sensors or active_tab != "tab-mobile":
            raise PreventUpdate
            
        try:
            # Filter data
            if not isinstance(selected_sensors, list):
                selected_sensors = [selected_sensors]
                
            filtered_data = data_processor.mobile_readings[
                data_processor.mobile_readings['sensor_id'].isin(selected_sensors)
            ]
            
            if time_range:
                start_time = pd.to_datetime(time_range[0], unit='s')
                end_time = pd.to_datetime(time_range[1], unit='s')
                filtered_data = filtered_data[
                    (filtered_data['timestamp'] >= start_time) &
                    (filtered_data['timestamp'] <= end_time)
                ]
            
            # Create time series
            fig = px.line(
                filtered_data,
                x='timestamp',
                y='value',
                color='sensor_id',
                title='Radiation Readings Over Time'
            )
            
            fig.update_layout(
                height=300,
                xaxis_title='Time',
                yaxis_title='Radiation Level (cpm)',
                showlegend=True,
                margin=dict(l=50, r=20, t=40, b=30)
            )
            
            # Calculate statistics
            stats = []
            for sensor_id in selected_sensors:
                sensor_data = filtered_data[filtered_data['sensor_id'] == sensor_id]
                if len(sensor_data) > 0:
                    stats.append(dbc.Card([
                        dbc.CardBody([
                            html.H6(f"Vehicle {sensor_id}"),
                            html.P(f"Readings: {len(sensor_data):,}"),
                            html.P(f"Average: {sensor_data['value'].mean():.1f} cpm"),
                            html.P(f"Maximum: {sensor_data['value'].max():.1f} cpm"),
                            html.P(f"Latest: {sensor_data.iloc[-1]['value']:.1f} cpm")
                        ])
                    ], className="mb-3"))
            
            stats_div = html.Div(stats) if stats else "No data available"
            
            return fig, stats_div
            
        except Exception as e:
            print(f"Error updating vehicle stats: {str(e)}")
            return px.line(), "Error calculating statistics"

    # Coverage Analysis
    @app.callback(
        Output('mobile-coverage-display', 'figure'),
        [Input('mobile-coverage-metric', 'value'),
         Input('mobile-time-range', 'value'),
         Input('tabs', 'active_tab')]
    )
    def update_coverage_display(metric, time_range, active_tab):
        print("update_coverage_display called")
        print("metric:", metric)
        print("time_range:", time_range)
        print("active_tab:", active_tab)
        if not metric or active_tab != "tab-mobile":
            raise PreventUpdate
            
        try:
            # Filter data
            filtered_data = data_processor.mobile_readings
            if time_range:
                start_time = pd.to_datetime(time_range[0], unit='s')
                end_time = pd.to_datetime(time_range[1], unit='s')
                filtered_data = filtered_data[
                    (filtered_data['timestamp'] >= start_time) &
                    (filtered_data['timestamp'] <= end_time)
                ]
                
            # Create visualizations based on metric
            if metric == 'spatial':
                fig = px.density_mapbox(
                    filtered_data,
                    lat='latitude',
                    lon='longitude',
                    radius=20,
                    title='Spatial Coverage'
                )
            elif metric == 'time':
                # Group by hour and location
                filtered_data['hour'] = filtered_data['timestamp'].dt.hour
                coverage = filtered_data.groupby(
                    ['latitude', 'longitude', 'hour']
                ).size().reset_index(name='count')
                
                fig = px.density_mapbox(
                    coverage,
                    lat='latitude',
                    lon='longitude',
                    z='count',
                    radius=20,
                    title='Temporal Coverage'
                )
            else:  # density
                fig = px.density_mapbox(
                    filtered_data,
                    lat='latitude',
                    lon='longitude',
                    z='value',
                    radius=20,
                    title='Reading Density'
                )
                
            # Update layout
            fig.update_layout(
                mapbox_style='carto-positron',
                mapbox=dict(
                    center=dict(
                        lat=filtered_data['latitude'].mean(),
                        lon=filtered_data['longitude'].mean()
                    ),
                    zoom=11
                ),
                height=400,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            return fig
            
        except Exception as e:
            print("Error in update_coverage_display:", e)
            return create_empty_map()
    return app

def create_empty_map():
    """Create an empty map figure for error cases"""
    fig = go.Figure(go.Scattermapbox())
    fig.update_layout(
        mapbox=dict(style='carto-positron', zoom=10),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500
    )
    return fig