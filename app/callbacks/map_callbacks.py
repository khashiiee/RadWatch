# app/callbacks/map_callbacks.py
from dash.dependencies import Input, Output
from app import app
from utils.mapping import MapVisualizer
from utils.data_processing import DataProcessor

@app.callback(
    Output('sensor-map', 'figure'),
    Input('map-layers', 'value')
)
def update_map_layers(active_layers):
    # Initialize data and map
    data_processor = DataProcessor()
    data_processor.load_data()
    map_viz = MapVisualizer()
    
    # Create new map with selected layers
    map_fig = map_viz.create_base_map(active_layers=active_layers)
    map_fig = map_viz.add_sensors(
        map_fig,
        data_processor.static_sensors,
        data_processor.mobile_readings,
        active_layers=active_layers
    )
    
    if active_layers and 'heatmap' in active_layers:
        map_fig = map_viz.add_radiation_heatmap(
            map_fig,
            data_processor.static_readings,
            active_layers=active_layers
        )
    
    return map_fig