'''
annotate colors from csv file.
'''

import csv
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, callback, ALL, MATCH, ctx
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import json
import dash

# Initialize the Dash app
app = Dash(__name__)


# Parse the space-separated file with quoted fields
def parse_file(filename):
    entries = []
    with open(filename, newline='') as csvfile:
        # Assuming the delimiter is still tab
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            entries.append(row)
    return entries


# your entries file name here!
entries = parse_file('Charlotte_Tilbury_blushes.csv')


# your output file name here!
def write_entry_to_file(entry, filename='Charlotte_Tilbury_blushes_with_color.csv'):
    with open(filename, 'a', newline='') as f:
        fieldnames = entry.keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC,
                                extrasaction='ignore')
        f.seek(0, 2)  # Move to the end of the file
        if f.tell() == 0:  # If file is empty, write headers
            writer.writeheader()
        writer.writerow(entry)


def generate_figure(entry, image_key):
    try:
        image_url = entry.get(image_key)
        if image_url:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            np_img = np.array(img.resize((250, 250)))
            fig = px.imshow(np_img).update_layout(margin=dict(l=10, r=10, t=10, b=10), dragmode='drawrect')
        else:
            raise ValueError("Image URL is missing.")
    except Exception as e:
        print(f"Error processing image {image_key}: {e}")
        fig = px.imshow(np.zeros((100, 100, 3), dtype=np.uint8)).update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return fig


def generate_layout(entries):
    layout = html.Div([
        html.Div([
            html.Div([
                dcc.Graph(
                    id={'type': 'dynamic-graph', 'index': f"{i}-0"},
                    figure=generate_figure(entry, 'image_link'),
                    config={'modeBarButtonsToAdd': ['drawrect', 'eraseshape']}
                ),
                dcc.Graph(
                    id={'type': 'dynamic-graph', 'index': f"{i}-1"},
                    figure=generate_figure(entry, 'additional_image_link'),
                    config={'modeBarButtonsToAdd': ['drawrect', 'eraseshape']}
                ),
                html.Button('Compute Color', id={'type': 'compute-btn', 'index': i}),
                html.Div(id={'type': 'computed-color', 'index': i}, children='Color will be shown here')
            ], style={'marginBottom': '10px'}) for i, entry in enumerate(entries)
        ])
    ])
    return layout


app.layout = generate_layout(entries)


# @app.callback(
#     Output({'type': 'computed-color', 'index': MATCH}, 'children'),
#     Input({'type': 'compute-btn', 'index': MATCH}, 'n_clicks'),
#     [State({'type': 'dynamic-graph', 'index': ALL}, 'relayoutData'),
#      State({'type': 'dynamic-graph', 'index': ALL}, 'id')],
#     prevent_initial_call=True
# )
# def compute_avg_color(n_clicks, relayout_data_list, graph_ids):
#     triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
#     entry_index = json.loads(triggered_id).get('index')
#     selected_entry = entries[entry_index]
#
#     shape_data = None
#     for relayout_data, graph_id in zip(relayout_data_list, graph_ids):
#         if relayout_data and 'shapes' in relayout_data:
#             # Assuming graph_id is structured as {'type': 'dynamic-graph', 'index': 'entryIndex-imageIndexWithinEntry'}
#             _, image_index_str = graph_id['index'].split('-')
#             image_index_within_entry = int(image_index_str)
#             shape_data = relayout_data['shapes'][0]
#
#     if not shape_data:
#         return 'Please draw a rectangle to compute the color.'
#
#     # Now, use image_index_within_entry to get the correct image
#     image_key = 'Image' if image_index_within_entry == 0 else f'Image{image_index_within_entry + 1}'
#     image_url = selected_entry.get(image_key, '')
#     if not image_url:
#         return f"Image not found for key: {image_key}."
#
#     # Proceed with cropping and color calculation...
#     response = requests.get(image_url)
#     image = Image.open(BytesIO(response.content)).convert('RGB')
#     image = image.resize((250, 250))
#     x0, y0, x1, y1 = map(int, [shape_data['x0'], shape_data['y0'], shape_data['x1'], shape_data['y1']])
#     cropped_image = image.crop((x0, y0, x1, y1))
#     np_image = np.array(cropped_image)
#     avg_color = np.mean(np_image, axis=(0, 1)).astype(int)
#     hex_color = '#%02x%02x%02x' % (avg_color[0], avg_color[1], avg_color[2])
#     # Update entry and write to file...
#     selected_entry['ave_color'] = str(avg_color)
#     write_entry_to_file(selected_entry)
#
#     return html.Div([
#         html.Span(f'Computed color: (RGB: {avg_color[0]}, {avg_color[1]}, {avg_color[2]})'),
#         html.Div(style={
#             'display': 'inline-block',
#             'marginLeft': '10px',
#             'width': '20px',
#             'height': '20px',
#             'backgroundColor': hex_color
#         })
#     ])

@app.callback(
    Output({'type': 'computed-color', 'index': MATCH}, 'children'),
    Input({'type': 'compute-btn', 'index': MATCH}, 'n_clicks'),
    [State({'type': 'dynamic-graph', 'index': ALL}, 'relayoutData'),
     State({'type': 'dynamic-graph', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def compute_avg_color(n_clicks, relayout_data_list, graph_ids):
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    entry_index = json.loads(triggered_id).get('index')
    selected_entry = entries[entry_index]

    shape_data = None
    for relayout_data, graph_id in zip(relayout_data_list, graph_ids):
        if relayout_data and 'shapes' in relayout_data:
            # Assuming graph_id is structured as {'type': 'dynamic-graph', 'index': 'entryIndex-imageIndexWithinEntry'}
            _, image_index_str = graph_id['index'].split('-')
            image_index_within_entry = int(image_index_str)
            shape_data = relayout_data['shapes'][0]

    if not shape_data:
        return 'Please draw a rectangle to compute the color.'

    # Now, use image_index_within_entry to get the correct image
    image_key = 'image_link' if image_index_within_entry == 0 else 'additional_image_link'
    image_url = selected_entry.get(image_key, '')
    if not image_url:
        return f"Image not found for key: {image_key}."

    # Proceed with cropping and color calculation...
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert('RGB')
    image = image.resize((250, 250))
    x0, y0, x1, y1 = map(int, [shape_data['x0'], shape_data['y0'], shape_data['x1'], shape_data['y1']])
    cropped_image = image.crop((x0, y0, x1, y1))
    np_image = np.array(cropped_image)
    avg_color = np.mean(np_image, axis=(0, 1)).astype(int)
    hex_color = '#%02x%02x%02x' % (avg_color[0], avg_color[1], avg_color[2])
    # Update entry and write to file...
    selected_entry['ave_color'] = str(avg_color)
    write_entry_to_file(selected_entry)

    return html.Div([
        html.Span(f'Computed color: (RGB: {avg_color[0]}, {avg_color[1]}, {avg_color[2]})'),
        html.Div(style={
            'display': 'inline-block',
            'marginLeft': '10px',
            'width': '20px',
            'height': '20px',
            'backgroundColor': hex_color
        })
    ])


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)
