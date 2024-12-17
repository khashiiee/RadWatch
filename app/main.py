# app/main.py
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
from utils.data_processing import DataProcessor
from layouts.overview import create_overview_layout
from layouts.analysis import create_analysis_layout  # Add this import
from layouts.static_sensors import create_static_sensors_layout
from layouts.mobile_sensor import create_mobile_sensors_layout
from utils.mapping import MapVisualizer
import os
import plotly.graph_objects as go
import plotly.express as px
from dash.exceptions import PreventUpdate
import pandas as pd
from dash import callback_context
from datetime import datetime, timedelta
from callbacks.mobile_callbacks import register_callbacks as register_mobile_callbacks
from layouts.sensor_comparison import create_comparison_layout
from callbacks.comparison_callbacks import register_comparison_callbacks



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
                dbc.Tab(label="Sensor Comparison", tab_id="tab-comparison"),
                dbc.Tab(label="Analysis", tab_id="tab-analysis")
            ], id="tabs", active_tab="tab-overview")
        ])
    ]),
    
    html.Div(id="tab-content"),
    
    # Add stores for sharing data between callbacks
    dcc.Store(id='static-sensor-data'),
    dcc.Store(id='mobile-sensor-data'),
    dcc.Store(id='comparison-data'),
    
    # Add loading spinner
    dcc.Loading(
        id="loading-spinner",
        type="default",
        children=html.Div(id="loading-output")
    )
], fluid=True)


app = register_comparison_callbacks(app, data_processor)  # Add this line
app = register_mobile_callbacks(app, data_processor)



# Tab content callback
@app.callback(
    [Output('tab-content', 'children'),
     Output('loading-output', 'children')],
    Input('tabs', 'active_tab')
)
def render_tab_content(active_tab):
    """Route to the appropriate layout based on selected tab"""
    try:
        if active_tab == "tab-overview":
            return create_overview_layout(data_processor), ""
        elif active_tab == "tab-static":
            return create_static_sensors_layout(data_processor), ""
        elif active_tab == "tab-mobile":
            return create_mobile_sensors_layout(data_processor), ""
        elif active_tab == "tab-comparison":
            return create_comparison_layout(data_processor), ""
        elif active_tab == "tab-analysis":
            return create_analysis_layout(data_processor), ""
        return "No content", ""
    except Exception as e:
        print(f"Error rendering tab content: {str(e)}")
        return html.Div([
            html.H4("Error Loading Content"),
            html.P(f"An error occurred: {str(e)}")
        ]),
# Overview map callback (keep existing implementation)
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
        print(traceback.format_exc())
        raise

# Static sensors callbacks
# Static Sensor Selector Callback
@app.callback(
    [Output('static-sensor-selector', 'options'),
     Output('static-sensor-selector', 'value')],
    Input('tabs', 'active_tab')
)
def init_static_sensor_selector(active_tab):
    if active_tab != "tab-static":
        raise PreventUpdate
        
    try:
        sensor_ids = sorted(data_processor.static_sensors[DataProcessor.SENSOR_ID].unique())
        options = [
            {'label': f'Sensor {sensor_id}', 'value': sensor_id}
            for sensor_id in sensor_ids
        ]
        # Initialize with first sensor selected
        initial_value = [sensor_ids[0]] if sensor_ids else None
        return options, initial_value
    except Exception as e:
        print(f"Error initializing sensor selector: {str(e)}")
        return [], None
    
@app.callback(
    [Output('static-sensor-data', 'data')],
    [Input('tabs', 'active_tab')]
)
def initialize_static_data(active_tab):
    if active_tab != "tab-static":
        raise PreventUpdate
        
    try:
        # Prepare basic sensor data for storage
        sensor_data = {
            'sensor_ids': data_processor.static_sensors[DataProcessor.SENSOR_ID].unique().tolist(),
            'total_readings': len(data_processor.static_readings),
            'time_range': [
                data_processor.static_readings[DataProcessor.TIMESTAMP].min().strftime('%Y-%m-%d %H:%M:%S'),
                data_processor.static_readings[DataProcessor.TIMESTAMP].max().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        return [sensor_data]
    except Exception as e:
        print(f"Error initializing static data: {str(e)}")
        return [{}]


# Time Range Initialization
@app.callback(
    [Output('static-time-range', 'min'),
     Output('static-time-range', 'max'),
     Output('static-time-range', 'marks'),
     Output('static-time-range', 'value')],
    Input('tabs', 'active_tab')
)
def init_time_range(active_tab):
    if active_tab != "tab-static":
        raise PreventUpdate
        
    try:
        # Convert timestamps to unix timestamps for the slider
        timestamps = data_processor.static_readings[DataProcessor.TIMESTAMP]
        min_time = timestamps.min().timestamp()
        max_time = timestamps.max().timestamp()
        
        # Create marks for the slider (show 5 marks)
        time_range = np.linspace(min_time, max_time, 5)
        marks = {
            int(ts): pd.to_datetime(ts, unit='s').strftime('%Y-%m-%d')
            for ts in time_range
        }
        
        # Initialize with full range selected
        return min_time, max_time, marks, [min_time, max_time]
    except Exception as e:
        print(f"Error initializing time range: {str(e)}")
        return 0, 1, {}, [0, 1]

# Time Series and Statistics Update
@app.callback(
    [Output('static-time-series', 'figure'),
     Output('static-sensor-stats', 'children'),
     Output('static-boxplot', 'figure')],
    [Input('static-sensor-selector', 'value'),
     Input('static-time-range', 'value')]
)
def update_static_sensor_analysis(selected_sensors, time_range):
    if not selected_sensors:
        raise PreventUpdate
        
    try:
        # Convert to list if single value
        if not isinstance(selected_sensors, list):
            selected_sensors = [selected_sensors]
            
        # Filter data
        filtered_data = data_processor.static_readings[
            data_processor.static_readings[DataProcessor.SENSOR_ID].isin(selected_sensors)
        ]
        
        if len(filtered_data) == 0:
            raise ValueError("No data found for selected sensors")
        
        # Create time series figure
        time_series = px.line(
            filtered_data,
            x=DataProcessor.TIMESTAMP,
            y=DataProcessor.VALUE,
            color=DataProcessor.SENSOR_ID,
            title="Radiation Levels Over Time"
        )
        time_series.update_layout(
            height=400,
            hovermode='x unified',
            xaxis_title="Time",
            yaxis_title="Radiation Level (cpm)"
        )
        
        # Create box plot
        boxplot = px.box(
            filtered_data,
            x=DataProcessor.SENSOR_ID,
            y=DataProcessor.VALUE,
            title="Radiation Level Distribution by Sensor",
            labels={
                DataProcessor.VALUE: "Radiation Level (cpm)",
                DataProcessor.SENSOR_ID: "Sensor ID"
            }
        )
        boxplot.update_layout(height=300)
        
        # Calculate statistics
        stats = []
        for sensor_id in selected_sensors:
            sensor_data = filtered_data[filtered_data[DataProcessor.SENSOR_ID] == sensor_id]
            if len(sensor_data) > 0:
                stats.append(html.Div([
                    html.H6(f"Sensor {sensor_id}", className="mt-3"),
                    dbc.Table([
                        html.Tbody([
                            html.Tr([
                                html.Td("Total Readings:", className="font-weight-bold"),
                                html.Td(f"{len(sensor_data):,}")
                            ]),
                            html.Tr([
                                html.Td("Average Radiation:", className="font-weight-bold"),
                                html.Td(f"{sensor_data[DataProcessor.VALUE].mean():.2f} cpm")
                            ]),
                            html.Tr([
                                html.Td("Maximum:", className="font-weight-bold"),
                                html.Td(f"{sensor_data[DataProcessor.VALUE].max():.2f} cpm")
                            ]),
                            html.Tr([
                                html.Td("Minimum:", className="font-weight-bold"),
                                html.Td(f"{sensor_data[DataProcessor.VALUE].min():.2f} cpm")
                            ]),
                            html.Tr([
                                html.Td("Std Deviation:", className="font-weight-bold"),
                                html.Td(f"{sensor_data[DataProcessor.VALUE].std():.2f} cpm")
                            ])
                        ])
                    ], bordered=True, size="sm", className="mb-3")
                ]))
        
        stats_div = html.Div(stats) if stats else html.Div("No data available for selected sensors")
        
        return time_series, stats_div, boxplot
        
    except Exception as e:
        print(f"Error updating static sensor analysis: {str(e)}")
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No data available",
            annotations=[{
                'text': "Select sensors to view data",
                'xref': "paper",
                'yref': "paper",
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        return empty_fig, html.Div("Error calculating statistics"), empty_fig


# Heatmap Update
# Add these imports if not already present
import plotly.graph_objects as go
import numpy as np
import pandas as pd

@app.callback(
    Output('static-heatmap', 'figure'),
    [Input('static-map-metric', 'value')]
)
def update_static_heatmap(metric):
    try:
        print("\n=== Updating Static Heatmap ===")
        print(f"Selected metric: {metric}")
        
        # Verify data availability
        if data_processor.static_sensors is None or data_processor.static_readings is None:
            raise ValueError("Static sensor data not properly loaded")
            
        # Print data shapes for debugging
        print(f"Static sensors shape: {data_processor.static_sensors.shape}")
        print(f"Static readings shape: {data_processor.static_readings.shape}")
        
        # Create base map
        map_viz = MapVisualizer()
        fig = map_viz.create_base_map(['boundaries'])
        
        # Get sensor locations and verify
        sensor_lats = data_processor.static_sensors[DataProcessor.LATITUDE]
        sensor_lons = data_processor.static_sensors[DataProcessor.LONGITUDE]
        
        print(f"Number of sensors: {len(sensor_lats)}")
        print(f"Lat range: [{sensor_lats.min():.4f}, {sensor_lats.max():.4f}]")
        print(f"Lon range: [{sensor_lons.min():.4f}, {sensor_lons.max():.4f}]")
        
        # Calculate metrics
        sensor_metrics = {}
        for sensor_id in data_processor.static_sensors[DataProcessor.SENSOR_ID].unique():
            sensor_readings = data_processor.static_readings[
                data_processor.static_readings[DataProcessor.SENSOR_ID] == sensor_id
            ][DataProcessor.VALUE]
            
            if len(sensor_readings) > 0:
                sensor_metrics[sensor_id] = {
                    'avg': sensor_readings.mean(),
                    'max': sensor_readings.max(),
                    'std': sensor_readings.std()
                }
                
        print(f"Calculated metrics for {len(sensor_metrics)} sensors")
        
        # Set visualization parameters
        if metric == 'avg':
            values = [sensor_metrics[sid]['avg'] for sid in sensor_metrics]
            title = "Average Radiation Levels"
            colorscale = 'Viridis'
            hover_text = "<b>Sensor %{text}</b><br>Average: %{marker.color:.1f} cpm"
        elif metric == 'max':
            values = [sensor_metrics[sid]['max'] for sid in sensor_metrics]
            title = "Maximum Radiation Levels"
            colorscale = 'Plasma'
            hover_text = "<b>Sensor %{text}</b><br>Maximum: %{marker.color:.1f} cpm"
        else:  # uncertainty
            values = [sensor_metrics[sid]['std'] for sid in sensor_metrics]
            title = "Radiation Level Uncertainty"
            colorscale = 'RdBu'
            hover_text = "<b>Sensor %{text}</b><br>Std Dev: %{marker.color:.2f} cpm"
        
        # Add sensor markers
        fig.add_trace(go.Scattermapbox(
            lat=sensor_lats,
            lon=sensor_lons,
            mode='markers',
            marker=dict(
                size=12,
                color=values,
                colorscale=colorscale,
                showscale=True,
                colorbar=dict(
                    title=dict(text=f"{title} (cpm)", side="right"),
                    thickness=15,
                    len=0.9
                )
            ),
            text=data_processor.static_sensors[DataProcessor.SENSOR_ID],
            hovertemplate=hover_text,
            name="Sensors"
        ))
        
        # Calculate the center and zoom level
        center_lat = sensor_lats.mean()
        center_lon = sensor_lons.mean()
        lat_range = sensor_lats.max() - sensor_lats.min()
        lon_range = sensor_lons.max() - sensor_lons.min()
        zoom = min(10, max(8, -np.log2(max(lat_range, lon_range))))
        
        print(f"Map center: ({center_lat:.4f}, {center_lon:.4f}), zoom: {zoom}")
        
        # Update layout
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=500,
            title=dict(
                text=title,
                x=0.5,
                xanchor='center'
            )
        )
        
        print("Map update completed successfully")
        return fig
        
    except Exception as e:
        print(f"\nERROR creating spatial distribution map: {str(e)}")
        print("Full traceback:")
        import traceback
        print(traceback.format_exc())
        
        # Return a more informative error figure
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text=f"Error loading map data: {str(e)}",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="red")
                )
            ],
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        return fig
    
    
@app.callback(
    [Output("static-sensor-count", "children"),
     Output("static-reading-count", "children"),
     Output("static-avg-radiation", "children"),
     Output("static-quality-score", "children"),
     Output("quality-description", "children")],
    [Input('tabs', 'active_tab'),
     Input('static-sensor-selector', 'value')]  # Add sensor selection input
)
def update_static_overview_stats(active_tab, selected_sensors=None):
    if active_tab != "tab-static":
        raise PreventUpdate
        
    try:
        if data_processor.static_readings is None or data_processor.static_sensors is None:
            raise ValueError("Data not properly loaded")
            
        # Filter data if specific sensors are selected
        readings_df = data_processor.static_readings
        if selected_sensors:
            if not isinstance(selected_sensors, list):
                selected_sensors = [selected_sensors]
            readings_df = readings_df[readings_df[DataProcessor.SENSOR_ID].isin(selected_sensors)]
        
        # Calculate basic stats
        n_sensors = len(selected_sensors) if selected_sensors else len(data_processor.static_sensors[DataProcessor.SENSOR_ID].unique())
        n_readings = len(readings_df)
        avg_radiation = readings_df[DataProcessor.VALUE].mean()
        
        # Time range calculation
        time_range = pd.date_range(
            readings_df[DataProcessor.TIMESTAMP].min(),
            readings_df[DataProcessor.TIMESTAMP].max(),
            freq='1H'
        )
        
        # Quality score calculation
        sensor_scores = {}
        overall_completeness = 0
        overall_consistency = 0
        
        # Calculate per-sensor metrics
        for sensor_id in (selected_sensors or data_processor.static_sensors[DataProcessor.SENSOR_ID].unique()):
            sensor_readings = readings_df[readings_df[DataProcessor.SENSOR_ID] == sensor_id]
            
            # Completeness (percentage of expected readings present)
            expected_readings = len(time_range)  # One reading per hour
            actual_readings = len(sensor_readings)
            completeness = min(100, (actual_readings / expected_readings) * 100)
            
            # Consistency (based on variation from mean)
            std_dev = sensor_readings[DataProcessor.VALUE].std()
            mean_val = sensor_readings[DataProcessor.VALUE].mean()
            if mean_val > 0:
                cv = (std_dev / mean_val) * 100  # Coefficient of variation
                consistency = 100 - min(100, cv)
            else:
                consistency = 0
                
            sensor_scores[sensor_id] = {
                'completeness': completeness,
                'consistency': consistency,
                'quality_score': (completeness + consistency) / 2
            }
            
            # Add to overall scores
            overall_completeness += completeness
            overall_consistency += consistency
        
        # Calculate final overall scores
        if sensor_scores:
            overall_completeness /= len(sensor_scores)
            overall_consistency /= len(sensor_scores)
            overall_quality = (overall_completeness + overall_consistency) / 2
        else:
            overall_quality = 0
            
        # Quality description with more context
        quality_desc = ("Excellent (High reliability)" if overall_quality >= 90 else 
                       "Good (Reliable)" if overall_quality >= 75 else 
                       "Fair (Some gaps/variations)" if overall_quality >= 50 else 
                       "Poor (Significant issues)")
        
        # Add completeness and consistency details to description
        quality_details = f"Completeness: {overall_completeness:.1f}%, Consistency: {overall_consistency:.1f}%"
        
        return (
            str(n_sensors),
            f"{n_readings:,} readings",
            f"{avg_radiation:.1f}",
            f"{overall_quality:.0f}%",
            f"Data Quality: {quality_desc} {quality_details}"
        )
        
    except Exception as e:
        print(f"Error updating static overview: {str(e)}")
        return "N/A", "No readings available", "N/A", "N/A", "Data quality unavailable"


# Temporal Pattern Analysis
@app.callback(
    Output('static-patterns', 'figure'),
    [Input('static-pattern-type', 'value')]
)
def update_temporal_patterns(pattern_type):
    try:
        df = data_processor.static_readings.copy()
        
        if pattern_type == 'daily':
            df['period'] = df[DataProcessor.TIMESTAMP].dt.hour
            title = "Daily Radiation Patterns"
            xlabel = "Hour of Day"
            period_format = lambda x: f"{x:02d}:00"
            tick_angle = 45
        elif pattern_type == 'weekly':
            df['period'] = df[DataProcessor.TIMESTAMP].dt.dayofweek
            title = "Weekly Radiation Patterns"
            xlabel = "Day of Week"
            period_format = lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]
            tick_angle = 0
        else:  # monthly
            df['period'] = df[DataProcessor.TIMESTAMP].dt.month
            title = "Monthly Radiation Patterns"
            xlabel = "Month"
            period_format = lambda x: ['January', 'February', 'March', 'April', 'May', 'June', 
                                     'July', 'August', 'September', 'October', 'November', 'December'][x-1]
            tick_angle = 45
            
        # Calculate statistics
        stats = df.groupby('period').agg({
            DataProcessor.VALUE: ['mean', 'std', 'min', 'max']
        }).reset_index()
        
        fig = go.Figure()
        
        # Add min/max range band
        fig.add_trace(go.Scatter(
            x=list(stats['period']) + list(stats['period'])[::-1],
            y=list(stats[DataProcessor.VALUE]['max']) + list(stats[DataProcessor.VALUE]['min'])[::-1],
            fill='toself',
            fillcolor='rgba(100,150,255,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Min-Max Range',
            showlegend=True
        ))
        
        # Add standard deviation band
        fig.add_trace(go.Scatter(
            x=list(stats['period']) + list(stats['period'])[::-1],
            y=list(stats[DataProcessor.VALUE]['mean'] + stats[DataProcessor.VALUE]['std']) + 
              list(stats[DataProcessor.VALUE]['mean'] - stats[DataProcessor.VALUE]['std'])[::-1],
            fill='toself',
            fillcolor='rgba(100,150,255,0.4)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Standard Deviation',
            showlegend=True
        ))
        
        # Add mean line
        fig.add_trace(go.Scatter(
            x=stats['period'],
            y=stats[DataProcessor.VALUE]['mean'],
            line=dict(color='rgb(0,100,255)', width=2),
            name='Average Radiation',
            showlegend=True
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sup>Showing average levels with standard deviation bands and min/max range</sup>",
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title=xlabel,
                ticktext=[period_format(x) for x in stats['period']],
                tickvals=stats['period'],
                tickangle=tick_angle
            ),
            yaxis=dict(
                title="Radiation Level (cpm)",
                range=[
                    min(stats[DataProcessor.VALUE]['min']) * 0.95,
                    max(stats[DataProcessor.VALUE]['max']) * 1.05
                ]
            ),
            hovermode='x unified',
            showlegend=True,
            height=400,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating temporal patterns: {str(e)}")
        return go.Figure()
    
    
    
# Mobile sensors callbacks




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








# Add info panel toggle callback
# app/callbacks/analysis_callbacks.py

@app.callback(
    Output('analysis-coverage-map', 'figure'),
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

if __name__ == '__main__':
    app.run_server(debug=True)