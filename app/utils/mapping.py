# app/utils/mapping.py
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import Point
import os
import numpy as np  # Added numpy import
from .data_processing import DataProcessor

class MapVisualizer:
    def __init__(self, shapefile_path='../data/StHimarkNeighborhoodShapefile/StHimark.shp'):
        print("\n=== Initializing MapVisualizer ===")
        print(f"Looking for shapefile at: {os.path.abspath(shapefile_path)}")
        
        try:
            if not os.path.exists(shapefile_path):
                print(f"ERROR: Shapefile not found at {shapefile_path}")
                print("Current working directory:", os.getcwd())
                parent_dir = os.path.dirname(shapefile_path)
                if os.path.exists(parent_dir):
                    print(f"Contents of {parent_dir}:", os.listdir(parent_dir))
                else:
                    print(f"Directory {parent_dir} does not exist")
                self.gdf = None
                return
                
            self.gdf = gpd.read_file(shapefile_path)
            print("Successfully loaded shapefile")
            print("Shapefile columns:", self.gdf.columns.tolist())
            print("Number of neighborhoods:", len(self.gdf))
            
            # Print first few rows of data
            print("\nSample of neighborhood data:")
            print(self.gdf[['Nbrhood']].head())
            
            if self.gdf.crs != 'EPSG:4326':
                print(f"Converting CRS from {self.gdf.crs} to EPSG:4326")
                self.gdf = self.gdf.to_crs('EPSG:4326')
                
        except Exception as e:
            print(f"ERROR loading shapefile: {str(e)}")
            import traceback
            print(traceback.format_exc())
            self.gdf = None

    def create_base_map(self, active_layers=None):
        """Create base map with neighborhood boundaries"""
        print("\n=== Creating Base Map ===")
        if active_layers is None:
            active_layers = ['static', 'mobile', 'boundaries']
                
        fig = go.Figure()
        
        # Add neighborhood boundaries if available
        if self.gdf is not None and 'boundaries' in active_layers:
            print(f"Adding neighborhoods. Number of neighborhoods: {len(self.gdf)}")
            
            # Convert each polygon to line coordinates
            for idx, row in self.gdf.iterrows():
                try:
                    # Extract polygon coordinates
                    if row.geometry.type == 'Polygon':
                        coords = row.geometry.exterior.coords
                        lons, lats = zip(*coords)
                    elif row.geometry.type == 'MultiPolygon':
                        lons, lats = [], []
                        for polygon in row.geometry.geoms:
                            coords = polygon.exterior.coords
                            poly_lons, poly_lats = zip(*coords)
                            lons += list(poly_lons) + [None]
                            lats += list(poly_lats) + [None]
                    
                    # Add boundary lines
                    fig.add_trace(go.Scattermapbox(
                        lon=lons,
                        lat=lats,
                        mode='lines',
                        line=dict(
                            width=2,
                            color='rgb(70,70,70)'
                        ),
                        name=f"Neighborhood: {row.get('Nbrhood', 'unnamed')}",
                        hoverinfo='text',
                        text=f"Neighborhood: {row.get('Nbrhood', 'unnamed')}",
                        showlegend=False
                    ))
                    
                    # Add neighborhood labels at centroid
                    centroid = row.geometry.centroid
                    fig.add_trace(go.Scattermapbox(
                        lon=[centroid.x],
                        lat=[centroid.y],
                        mode='text',
                        text=[row.get('Nbrhood', '')],
                        textfont=dict(size=10, color='rgb(50,50,50)'),
                        showlegend=False,
                        hoverinfo='none'
                    ))
                    
                except Exception as e:
                    print(f"Error adding neighborhood {idx}: {str(e)}")
        
        # Set map center and zoom
        center_lat = 42.0
        center_lon = -71.0
        zoom = -1
        
        if self.gdf is not None:
            bounds = self.gdf.geometry.total_bounds
            print(f"Map bounds: {bounds}")
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            
            # Calculate zoom level based on bounds
            lat_range = bounds[3] - bounds[1]
            if lat_range > 0:
                zoom = 10.75
        
        print(f"Map center: ({center_lat}, {center_lon}), Zoom: {zoom}")
        
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=750,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)"
            )
        )
        
        return fig
    
    def add_sensors(self, fig, static_sensors, mobile_readings=None, active_layers=None):
        """Add sensor locations to the map"""
        if active_layers is None:
            active_layers = ['static', 'mobile']
            
        # Add static sensors
        if 'static' in active_layers:
            fig.add_trace(go.Scattermapbox(
                lat=static_sensors[DataProcessor.LATITUDE],
                lon=static_sensors[DataProcessor.LONGITUDE],
                mode='markers',
                marker=dict(
                    size=10,
                    color='red',
                    opacity=0.8
                ),
                name='Static Sensors',
                text=static_sensors[DataProcessor.SENSOR_ID],
                hovertemplate="<b>Static Sensor</b><br>ID: %{text}<br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>"
            ))
        
        # Add mobile sensors
        if mobile_readings is not None and 'mobile' in active_layers:
            latest_readings = mobile_readings.sort_values(DataProcessor.TIMESTAMP).groupby(DataProcessor.SENSOR_ID).last()
            fig.add_trace(go.Scattermapbox(
                lat=latest_readings[DataProcessor.LATITUDE],
                lon=latest_readings[DataProcessor.LONGITUDE],
                mode='markers',
                marker=dict(
                    size=8,
                    color='blue',
                    opacity=0.7
                ),
                name='Mobile Sensors',
                text=latest_readings[DataProcessor.USER_ID],
                hovertemplate="<b>Mobile Sensor</b><br>User: %{text}<br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>"
            ))
        
        return fig

    def add_radiation_heatmap(self, fig, readings, static_sensors, active_layers=None):
        """Add radiation heatmap layer"""
        print("\n=== Adding Radiation Heatmap ===")
        if active_layers is None or 'heatmap' not in active_layers:
            return fig
            
        try:
            # Merge readings with sensor locations
            heatmap_data = pd.merge(
                readings,
                static_sensors,
                on=DataProcessor.SENSOR_ID,
                how='inner'
            )
            
            # Calculate average values for each location
            heatmap_data = heatmap_data.groupby(
                [DataProcessor.LATITUDE, DataProcessor.LONGITUDE]
            )[DataProcessor.VALUE].mean().reset_index()
            
            print(f"Generated heatmap data: {len(heatmap_data)} locations")
            
            # Add heatmap layer with optimized properties
            fig.add_trace(go.Densitymapbox(
                lat=heatmap_data[DataProcessor.LATITUDE],
                lon=heatmap_data[DataProcessor.LONGITUDE],
                z=heatmap_data[DataProcessor.VALUE],
                radius=75,  # Increased for better coverage
                colorscale='Viridis',
                name='Radiation Levels',
                hovertemplate=(
                    "<b>Radiation Level</b><br>" +
                    "Value: %{z:.2f} cpm<br>" +
                    "Lat: %{lat:.4f}<br>" +
                    "Lon: %{lon:.4f}<extra></extra>"
                ),
                colorbar=dict(
                    title=dict(
                        text='Radiation Level (cpm)',
                        side='right'
                    ),
                    thickness=15,
                    len=0.7,
                    tickformat='.1f'
                ),
                opacity=0.7,  # Slightly reduced for better overlay
                showscale=True,
                zmin=heatmap_data[DataProcessor.VALUE].min(),  # Set explicit range
                zmax=heatmap_data[DataProcessor.VALUE].max()
            ))
            
            return fig
            
        except Exception as e:
            print(f"ERROR creating heatmap: {str(e)}")
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())
            return fig
        
    def add_animated_radiation_data(self, fig, readings, sensors, sensor_type, time_agg, animation_speed, active_layers):
        """Add animated radiation visualization for either static or mobile sensors with improved heatmap handling"""
        try:
            # Prepare data
            if sensor_type == 'static':
                data = pd.merge(
                    readings,
                    sensors,
                    on=DataProcessor.SENSOR_ID,
                    how='inner'
                )
            else:
                data = readings.copy()
            
            # Group data by time period
            time_groups = data.groupby([
                pd.Grouper(key=DataProcessor.TIMESTAMP, freq=time_agg),
                DataProcessor.LATITUDE,
                DataProcessor.LONGITUDE
            ])[DataProcessor.VALUE].agg(['mean', 'count']).reset_index()
                        
            # Create frames for animation
            frames = []
            timestamps = sorted(time_groups[DataProcessor.TIMESTAMP].unique())
            
            for timestamp in timestamps:
                frame_data = time_groups[time_groups[DataProcessor.TIMESTAMP] == timestamp]
                    
                # Add sensor markers and heatmap
                traces = []
                
                # Add sensor markers
                if sensor_type == 'static' and 'static' in active_layers:
                    traces.append(go.Scattermapbox(
                        lat=frame_data[DataProcessor.LATITUDE],
                        lon=frame_data[DataProcessor.LONGITUDE],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color='red',
                            opacity=0.8
                        ),
                        name='Static Sensors'
                    ))
                elif sensor_type == 'mobile' and 'mobile' in active_layers:
                    traces.append(go.Scattermapbox(
                        lat=frame_data[DataProcessor.LATITUDE],
                        lon=frame_data[DataProcessor.LONGITUDE],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color='blue',
                            opacity=0.7
                        ),
                        name='Mobile Sensors'
                    ))
                
                # Add appropriate heatmap layer
                if f'{sensor_type}_heatmap' in active_layers:
                    heatmap_settings = {
                        'static': {
                            'radius': 75,
                            'colorscale': 'Viridis',
                            'name': 'Static Radiation Levels',
                            'opacity': 0.6,
                            'colorbar_x': 1.02 if 'mobile_heatmap' in active_layers else 1.0,
                            'below': '' if 'mobile_heatmap' not in active_layers else 'traces'
                        },
                        'mobile': {
                            'radius': 60,
                            'colorscale': 'Plasma',
                            'name': 'Mobile Radiation Levels',
                            'opacity': 0.6,
                            'colorbar_x': 1.1 if 'static_heatmap' in active_layers else 1.0,
                            'below': None
                        }
                    }[sensor_type]
                    
                    traces.append(go.Densitymapbox(
                        lat=frame_data[DataProcessor.LATITUDE],
                        lon=frame_data[DataProcessor.LONGITUDE],
                        z=frame_data['mean'],
                        radius=heatmap_settings['radius'],
                        colorscale=heatmap_settings['colorscale'],
                        name=heatmap_settings['name'],
                        hovertemplate=(
                            f"<b>{sensor_type.title()} Radiation Level</b><br>" +
                            "Value: %{z:.2f} cpm<br>" +
                            "Lat: %{lat:.4f}<br>" +
                            "Lon: %{lon:.4f}<extra></extra>"
                        ),
                        colorbar=dict(
                            title=dict(
                                text=f'{sensor_type.title()} Radiation (cpm)',
                                side='right'
                            ),
                            thickness=15,
                            len=0.7,
                            tickformat='.1f',
                            x=heatmap_settings['colorbar_x']
                        ),
                        opacity=heatmap_settings['opacity'],
                        showscale=True,
                        zmin=time_groups['mean'].min(),
                        zmax=time_groups['mean'].max(),
                        below=heatmap_settings['below']
                    ))
                
                frames.append(go.Frame(
                    data=traces,
                    name=timestamp.strftime('%Y-%m-%d %H:%M')
                ))
            
            # Add initial frame data to figure
            if frames:
                for trace in frames[0].data:
                    fig.add_trace(trace)
            
            # Update layout with animation controls
            frame_duration = int(1000 / animation_speed)
            fig.frames = frames
            fig.update_layout(
                updatemenus=[{
                    'type': 'buttons',
                    'direction': 'left',
                    'showactive': False,
                    'x': 0.1,
                    'y': 1.2,
                    'pad': {'r': 10, 'l': 10, 't': 0, 'b': 0},
                    'buttons': [
                        {
                            'args': [None, {
                                'frame': {'duration': frame_duration, 'redraw': True},
                                'fromcurrent': True,
                                'transition': {'duration': 30}
                            }],
                            'label': '▶️',
                            'method': 'animate'
                        },
                        {
                            'args': [[None], {
                                'frame': {'duration': 0, 'redraw': False},
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }],
                            'label': '⏸️',
                            'method': 'animate'
                        }
                    ]
                }],
                sliders=[{
                    'currentvalue': {
                        'prefix': 'Time: ',
                        'visible': True,
                        'xanchor': 'right',
                        'font': {'size': 14, 'color': '#666'}
                    },
                    'pad': {'t': 0, 'b': 10},
                    'len': 0.9,
                    'x': 0.05,
                    'xanchor': 'left',
                    'y': 1.17,
                    'yanchor': 'top',
                    'steps': [{
                        'args': [[f.name], {
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }],
                        'label': f.name,
                        'method': 'animate'
                    } for f in frames],
                    'transition': {'duration': 300, 'easing': 'cubic-in-out'}
                }]
            )
            
            return fig
            
        except Exception as e:
            print(f"ERROR in animated visualization: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return fig