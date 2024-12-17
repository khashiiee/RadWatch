# app/callbacks/comparison_callbacks.py
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dash import html, dcc
from utils.mapping import MapVisualizer
from dash.exceptions import PreventUpdate




def register_comparison_callbacks(app, data_processor):
    @app.callback(
        [Output("static-coverage-stats", "children"),
         Output("mobile-coverage-stats", "children"),
         Output("overall-coverage-stats", "children")],
        [Input("comparison-date-range", "start_date"),
         Input("comparison-date-range", "end_date")]
    )
    def update_coverage_stats(start_date, end_date):
        """Update detailed coverage statistics"""
        try:
            # Filter data by date range
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
            
            # Static sensor statistics
            static_sensors = len(data_processor.static_sensors)
            static_readings = len(static_data)
            static_avg = static_data['value'].mean()
            
            static_stats = html.Div([
                html.P(f"Number of Sensors: {static_sensors}"),
                html.P(f"Total Readings: {static_readings:,}"),
                html.P(f"Average Reading: {static_avg:.2f} cpm")
            ])
            
            # Mobile sensor statistics
            mobile_sensors = len(mobile_data['sensor_id'].unique())
            mobile_readings = len(mobile_data)
            mobile_avg = mobile_data['value'].mean()
            
            mobile_stats = html.Div([
                html.P(f"Active Vehicles: {mobile_sensors}"),
                html.P(f"Total Readings: {mobile_readings:,}"),
                html.P(f"Average Reading: {mobile_avg:.2f} cpm")
            ])
            
            # Overall coverage calculation
            total_area = 100  # Approximate city area in km²
            static_coverage = static_sensors * 0.5  # Assuming 0.5 km² coverage per static sensor
            mobile_unique_locs = len(mobile_data[['latitude', 'longitude']].drop_duplicates())
            mobile_coverage = mobile_unique_locs * 0.01  # Assuming 0.01 km² per unique mobile reading
            
            total_coverage = min(100, ((static_coverage + mobile_coverage) / total_area) * 100)
            
            overall_stats = html.Div([
                html.H6("Overall Coverage", className="text-dark"),
                html.P([
                    f"Estimated City Coverage: ",
                    html.Strong(f"{total_coverage:.1f}%")
                ]),
                html.P(f"Unique Locations: {mobile_unique_locs:,}"),
                html.Small("Based on combined static and mobile sensor coverage")
            ])
            
            return static_stats, mobile_stats, overall_stats
            
        except Exception as e:
            print(f"Error updating coverage stats: {str(e)}")
            error_div = html.Div("Error calculating statistics")
            return error_div, error_div, error_div
        
    @app.callback(
        Output("comparison-map", "figure"),
        [Input("comparison-date-range", "start_date"),
         Input("comparison-date-range", "end_date"),
         Input("comparison-metric", "value")]
    )
    def update_comparison_map(start_date, end_date, metric):
        """Update the comparison map with dual colorscales"""
        if not metric:
            raise PreventUpdate
            
        try:
            # Filter data
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
            
            # Create base map
            map_viz = MapVisualizer()
            fig = map_viz.create_base_map(['boundaries'])
            
            # Process static sensors
            static_stats = static_data.groupby('sensor_id').agg({
                'value': ['mean', 'max', 'count']
            }).reset_index()
            static_stats.columns = ['sensor_id', 'mean', 'max', 'count']
            
            static_locs = pd.merge(
                data_processor.static_sensors,
                static_stats,
                on='sensor_id'
            )
            
            value_col = {
                'avg': 'mean',
                'max': 'max',
                'freq': 'count',
                'coverage': 'count'
            }[metric]
            
            # Add static sensors with right-side colorbar
            fig.add_trace(go.Scattermapbox(
                lat=static_locs['latitude'],
                lon=static_locs['longitude'],
                mode='markers',
                marker=dict(
                    size=20,
                    color=static_locs[value_col],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(
                    title=dict(
                        text="Static Sensors (cpm)",
                        side='right'
                    ),
                    x=1.02,  # Adjust position
                    y=0.5,
                    len=0.6,  # Make length consistent
                    thickness=15,  # Make width consistent
                    ypad=0,  # Remove padding
                    titleside='right'
                )
                ),
                text=[f"Static {sid}<br>Value: {val:.1f}" 
                    for sid, val in zip(static_locs['sensor_id'], static_locs[value_col])],
                hovertemplate="%{text}<extra></extra>",
                name='Static Sensors',
                showlegend=True
            ))
            
            # Process mobile sensors
            if metric in ['avg', 'max']:
                mobile_stats = mobile_data.groupby('sensor_id').agg({
                    'value': ['mean', 'max'],
                    'latitude': 'last',
                    'longitude': 'last'
                }).reset_index()
                mobile_stats.columns = ['sensor_id', 'mean', 'max', 'latitude', 'longitude']
                
                # Add mobile sensors with left-side colorbar
                fig.add_trace(go.Scattermapbox(
                    lat=mobile_stats['latitude'],
                    lon=mobile_stats['longitude'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=mobile_stats[value_col],
                        colorscale='Plasma',
                        showscale=True,
                        colorbar=dict(
                    title=dict(
                        text="Mobile Sensors (cpm)",
                        side='right'
                    ),
                    x=0.91,  # Position left of static colorbar
                    y=0.5,
                    len=0.6,  # Match static colorbar length
                    thickness=15,  # Match static colorbar width
                    ypad=0,  # Remove padding
                    titleside='right'
                )
                    ),
                    text=[f"Vehicle {sid}<br>Value: {val:.1f}" 
                        for sid, val in zip(mobile_stats['sensor_id'], mobile_stats[value_col])],
                    hovertemplate="%{text}<extra></extra>",
                    name='Mobile Sensors',
                    showlegend=False
                ))
            else:
                # Coverage view with heatmap
                fig.add_trace(go.Densitymapbox(
                    lat=mobile_data['latitude'],
                    lon=mobile_data['longitude'],
                    z=mobile_data['value'],
                    radius=20,
                    colorscale='Plasma',
                    showscale=True,
                    colorbar=dict(
                        title="Mobile Coverage",
                        x=0.85,
                        y=0.5,
                        len=0.8
                    ),
                    name='Mobile Coverage',
                    opacity=0.6,
                    showlegend=False
                ))
            
            # Update layout
            center_lat = static_locs['latitude'].mean()
            center_lon = static_locs['longitude'].mean()
            
            fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    zoom=11,
                    center=dict(lat=center_lat, lon=center_lon)
                ),
                margin=dict(l=0, r=0, t=0, b=0),
                height=600,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor="rgba(255,255,255,0.8)"
                )
            )
            
            return fig
            
        except Exception as e:
            print(f"Error updating comparison map: {str(e)}")
            return go.Figure()
        
    
    @app.callback(
        Output("comparison-timeseries", "figure"),
        [Input("comparison-date-range", "start_date"),
         Input("comparison-date-range", "end_date")]
    )
    def update_comparison_timeseries(start_date, end_date):
        """Update time series comparison"""
        try:
            # Filter data
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
            
            # Calculate hourly averages
            static_hourly = static_data.groupby(
                pd.Grouper(key='timestamp', freq='1H')
            )['value'].agg(['mean', 'std']).reset_index()
            
            mobile_hourly = mobile_data.groupby(
                pd.Grouper(key='timestamp', freq='1H')
            )['value'].agg(['mean', 'std']).reset_index()
            
            # Create figure
            fig = go.Figure()
            
            # Add static sensor data with confidence interval
            fig.add_trace(go.Scatter(
                x=static_hourly['timestamp'],
                y=static_hourly['mean'],
                mode='lines',
                name='Static Sensors',
                line=dict(color='blue'),
                showlegend=True
            ))
            
            fig.add_trace(go.Scatter(
                x=static_hourly['timestamp'],
                y=static_hourly['mean'] + static_hourly['std'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=static_hourly['timestamp'],
                y=static_hourly['mean'] - static_hourly['std'],
                mode='lines',
                line=dict(width=0),
                fillcolor='rgba(0, 0, 255, 0.2)',
                fill='tonexty',
                name='Static Confidence',
                hoverinfo='skip'
            ))
            
            # Add mobile sensor data with confidence interval
            fig.add_trace(go.Scatter(
                x=mobile_hourly['timestamp'],
                y=mobile_hourly['mean'],
                mode='lines',
                name='Mobile Sensors',
                line=dict(color='red'),
                showlegend=True
            ))
            
            fig.add_trace(go.Scatter(
                x=mobile_hourly['timestamp'],
                y=mobile_hourly['mean'] + mobile_hourly['std'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=mobile_hourly['timestamp'],
                y=mobile_hourly['mean'] - mobile_hourly['std'],
                mode='lines',
                line=dict(width=0),
                fillcolor='rgba(255, 0, 0, 0.2)',
                fill='tonexty',
                name='Mobile Confidence',
                hoverinfo='skip'
            ))
            
            fig.update_layout(
                title="Radiation Readings Over Time",
                xaxis_title="Time",
                yaxis_title="Radiation Level (cpm)",
                hovermode='x unified',
                height=400
            )
            
            return fig
            
        except Exception as e:
            print(f"Error updating time series: {str(e)}")
            return go.Figure()

    @app.callback(
        Output("comparison-stats", "figure"),
        [Input("comparison-date-range", "start_date"),
         Input("comparison-date-range", "end_date")]
    )
    def update_comparison_stats(start_date, end_date):
        """Update statistical comparison"""
        try:
            # Filter data
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
            
            # Calculate statistics
            stats = pd.DataFrame({
                'Metric': ['Mean', 'Median', 'Std Dev', 'Max', 'Min'],
                'Static': [
                    static_data['value'].mean(),
                    static_data['value'].median(),
                    static_data['value'].std(),
                    static_data['value'].max(),
                    static_data['value'].min()
                ],
                'Mobile': [
                    mobile_data['value'].mean(),
                    mobile_data['value'].median(),
                    mobile_data['value'].std(),
                    mobile_data['value'].max(),
                    mobile_data['value'].min()
                ]
            })
            
            # Create comparison bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Static Sensors',
                x=stats['Metric'],
                y=stats['Static'],
                marker_color='blue'
            ))
            
            fig.add_trace(go.Bar(
                name='Mobile Sensors',
                x=stats['Metric'],
                y=stats['Mobile'],
                marker_color='red'
            ))
            
            fig.update_layout(
                title="Statistical Comparison",
                yaxis_title="Value (cpm)",
                barmode='group',
                height=400
            )
            
            return fig
            
        except Exception as e:
            print(f"Error updating statistics: {str(e)}")
            return go.Figure()

    return app