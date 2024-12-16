# app/callbacks/analysis_callbacks.py
from dash.dependencies import Input, Output, State
from dash import callback_context
import pandas as pd
import json

# Initialize timeline data
@app.callback(
    [Output('time-slider', 'marks'),
     Output('time-slider', 'max'),
     Output('timeline-data', 'data')],
    [Input('time-aggregation', 'value'),
     Input('analysis-date-range', 'start_date'),
     Input('analysis-date-range', 'end_date')]
)
def update_timeline(time_step, start_date, end_date):
    if not all([time_step, start_date, end_date]):
        return {}, 0, []

    # Generate time steps
    date_range = pd.date_range(start=start_date, end=end_date, freq=time_step)
    max_steps = len(date_range) - 1

    # Create marks for the slider
    marks = {}
    for i, timestamp in enumerate(date_range):
        if i % max(1, len(date_range) // 10) == 0:  # Show ~10 marks
            marks[i] = timestamp.strftime('%m-%d %H:%M')

    # Store full timeline data
    timeline_data = [ts.strftime('%Y-%m-%d %H:%M') for ts in date_range]

    return marks, max_steps, timeline_data

# Handle play/pause and animation
@app.callback(
    [Output('animation-interval', 'disabled'),
     Output('animation-state', 'data'),
     Output('playpause-button', 'children')],
    [Input('playpause-button', 'n_clicks')],
    [State('animation-state', 'data')]
)
def toggle_animation(n_clicks, animation_state):
    if n_clicks is None:
        return True, {'is_playing': False}, html.I(className="fas fa-play")

    is_playing = not animation_state['is_playing']
    return (not is_playing, 
            {'is_playing': is_playing},
            html.I(className="fas fa-pause") if is_playing else html.I(className="fas fa-play"))

# Update slider position
@app.callback(
    Output('time-slider', 'value'),
    [Input('animation-interval', 'n_intervals'),
     Input('next-frame', 'n_clicks'),
     Input('prev-frame', 'n_clicks'),
     Input('first-frame', 'n_clicks'),
     Input('last-frame', 'n_clicks')],
    [State('time-slider', 'value'),
     State('time-slider', 'max'),
     State('animation-state', 'data'),
     State('animation-speed', 'value')]
)
def update_slider_position(intervals, next_click, prev_click, first_click, last_click, 
                         current_value, max_value, animation_state, speed):
    ctx = callback_context
    if not ctx.triggered:
        return 0

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'animation-interval' and animation_state['is_playing']:
        next_value = current_value + 1
        return 0 if next_value > max_value else next_value
    elif trigger_id == 'next-frame':
        return min(current_value + 1, max_value)
    elif trigger_id == 'prev-frame':
        return max(current_value - 1, 0)
    elif trigger_id == 'first-frame':
        return 0
    elif trigger_id == 'last-frame':
        return max_value

    return current_value

# Update timestamp display
@app.callback(
    Output('current-timestamp', 'children'),
    [Input('time-slider', 'value'),
     Input('timeline-data', 'data')]
)
def update_timestamp_display(slider_value, timeline_data):
    if not timeline_data or slider_value is None:
        return "Select time period"

    if 0 <= slider_value < len(timeline_data):
        return f"Current Time: {timeline_data[slider_value]}"
    return "No data available"