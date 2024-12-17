# # app/callbacks/init_callbacks.py
# from dash.dependencies import Input, Output
# from dash.exceptions import PreventUpdate
# import plotly.graph_objects as go
# import plotly.express as px
# import pandas as pd
# import numpy as np
# from utils.mapping import MapVisualizer
# from callbacks.mobile_callbacks import register_callbacks as register_mobile_callbacks

# def init_callbacks(app, data_processor):
#     """Initialize all callbacks for the application"""
    
#     # Tab content callback
#     @app.callback(
#         [Output('tab-content', 'children'),
#          Output('loading-output', 'children')],
#         Input('tabs', 'active_tab')
#     )
#     def render_tab_content(active_tab):
#         try:
#             if active_tab == "tab-overview":
#                 return create_overview_layout(data_processor), ""
#             elif active_tab == "tab-static":
#                 return create_static_sensors_layout(data_processor), ""
#             elif active_tab == "tab-mobile":
#                 return create_mobile_sensors_layout(data_processor), ""
#             elif active_tab == "tab-analysis":
#                 return create_analysis_layout(data_processor), ""
#             return "No content", ""
#         except Exception as e:
#             print(f"Error rendering tab content: {str(e)}")
#             return html.Div([
#                 html.H4("Error Loading Content"),
#                 html.P(f"An error occurred: {str(e)}")
#             ]), ""

#     # Overview map callback
#     @app.callback(
#         Output('sensor-map', 'figure'),
#         Input('map-layers', 'value')
#     )
#     def update_map_layers(active_layers):
#         # Your existing map callback code here
#         pass

#     # Static sensor callbacks
#     @app.callback(
#         [Output('static-sensor-selector', 'options'),
#          Output('static-sensor-selector', 'value')],
#         Input('tabs', 'active_tab')
#     )
#     def init_static_sensor_selector(active_tab):
#         # Your existing static sensor selector callback code here
#         pass

#     @app.callback(
#         [Output('static-sensor-data', 'data')],
#         [Input('tabs', 'active_tab')]
#     )
#     def initialize_static_data(active_tab):
#         # Your existing static data initialization callback code here
#         pass

#     # Time range initialization
#     @app.callback(
#         [Output('static-time-range', 'min'),
#          Output('static-time-range', 'max'),
#          Output('static-time-range', 'marks'),
#          Output('static-time-range', 'value')],
#         Input('tabs', 'active_tab')
#     )
#     def init_time_range(active_tab):
#         # Your existing time range initialization callback code here
#         pass

#     # Analysis callbacks
#     @app.callback(
#         [Output('analysis-map', 'figure'),
#          Output('time-period-stats', 'children')],
#         [Input('analysis-layers', 'value'),
#          Input('analysis-date-range', 'start_date'),
#          Input('analysis-date-range', 'end_date'),
#          Input('time-aggregation', 'value'),
#          Input('animation-speed', 'value')]
#     )
#     def update_analysis_view(active_layers, start_date, end_date, time_agg, animation_speed):
#         # Your existing analysis view callback code here
#         pass

#     @app.callback(
#         [Output('affected-areas-map', 'figure'),
#          Output('affected-areas-stats', 'children')],
#         [Input('radiation-threshold', 'value'),
#          Input('analysis-date-range', 'start_date'),
#          Input('analysis-date-range', 'end_date')]
#     )
#     def update_affected_areas_analysis(threshold_range, start_date, end_date):
#         # Your existing affected areas analysis callback code here
#         pass

#     # Register mobile callbacks
#     app = register_mobile_callbacks(app, data_processor)
    
#     return app