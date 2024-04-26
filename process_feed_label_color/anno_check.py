'''
streamlit app to check color annotations visually.
'''
import csv
from io import BytesIO
from PIL import Image

import requests
import streamlit as st


# Function to convert RGB to Hex
def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % tuple(rgb)


def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")


# Main function to load and display the data
def load_and_display_data(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            image_urls = [
                row.get('Image'), row.get('Image2'), row.get('Image3'),
                row.get('Image4'), row.get('Image5')
            ]

            # Filter out empty URLs
            image_urls = [url for url in image_urls if url and is_valid_url(url)]

            ave_color_str = row.get('ave_color', '')  # Default to empty string if key not found
            # Ensure splitting handles spaces after commas and captures numbers accurately
            ave_color = [int(color) for color in ave_color_str.strip('[]').split() if color.strip()]

            # Verify the tuple's integrity
            if len(ave_color) == 3:
                ave_color_hex = rgb_to_hex(ave_color)
            else:
                # Log unexpected format for review
                print(f"Unexpected ave_color format: '{ave_color_str}'")
                ave_color_hex = "#000000"  # Fallback color

                # Create columns for images + 1 for the color square
            num_columns = len(image_urls) + 1
            cols = st.beta_columns(num_columns)

            # Display each image in its column
            for i, url in enumerate(image_urls):
                response = requests.get(url)
                image_bytes = BytesIO(response.content)
                image = Image.open(image_bytes)
                cols[i].image(image, use_column_width=True)

            # Display the average color in the last column
            cols[-1].markdown(f"<div style='width:100px; height:100px; background-color: {ave_color_hex};'></div>",
                              unsafe_allow_html=True)

            # Add some space after each entry
            st.write("---")


def write_entry_to_file(entry, filename):
    with open(filename, 'a', newline='') as f:
        fieldnames = entry.keys()
        # Use QUOTE_NONNUMERIC to quote all non-numeric fields
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', quotechar='"', quoting=csv.QUOTE_NONNUMERIC,
                                extrasaction='ignore')
        f.seek(0, 2)  # Move to the end of the file
        if f.tell() == 0:  # If file is empty, write headers
            writer.writeheader()
        writer.writerow(entry)


def filter_incorrect_entries(write_path, read_path):
    with open(read_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')

        for row in reader:
            try:
                ave_color_str = row.get('ave_color', '')
                ave_color = [int(color) for color in ave_color_str.strip('[]').split() if color.strip()]
            except:
                continue
            write_entry_to_file(row, write_path)


if __name__ == '__main__':
    read_path = 'eyeshadow_entries_with_color.txt'
    write_path = 'eyeshadow_entries_with_color_filtered.txt'
    filter_incorrect_entries(write_path, read_path)
    # load_and_display_data(file_path)
