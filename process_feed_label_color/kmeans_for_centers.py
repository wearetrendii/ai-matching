'''We are not using this anymore!!!!!!!!'''

import csv
from sklearn.cluster import KMeans
import numpy as np
from scipy.spatial.distance import cdist


def get_all_colors(read_path):
    ave_colors = []
    with open(read_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            ave_color_str = row.get('ave_color', '')
            ave_color = [int(color) for color in ave_color_str.strip('[]').split() if color.strip()]
            ave_colors.append(ave_color)
    return ave_colors


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


def assign_to_centers_append_to_file(write_path, cluster_centers, read_path):
    with open(read_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')

        for row in reader:
            ave_color_str = row.get('ave_color', '')  # Default to empty string if key not found
            # Ensure splitting handles spaces after commas and captures numbers accurately
            ave_color = [int(color) for color in ave_color_str.strip('[]').split() if color.strip()]

            # Compute the distance to all cluster centers and find the closest
            distances = cdist(np.array(ave_color).reshape(1, -1), cluster_centers)
            closest_center_idx = np.argmin(distances)
            closest_center = cluster_centers[closest_center_idx]

            # Append this information to the row and write it out
            row['center'] = closest_center
            write_entry_to_file(row, write_path)


def kmeans(ave_colors, num_clusters=8):
    np.random.seed(42)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(np.array(ave_colors))
    cluster_centers = kmeans.cluster_centers_
    cluster_centers_round = [[round(number) for number in sublist] for sublist in cluster_centers]

    return cluster_centers_round


def main(write_path, read_path, num_clusters):
    ave_colors = get_all_colors(read_path)
    cluster_centers = kmeans(ave_colors, num_clusters)
    assign_to_centers_append_to_file(write_path, cluster_centers, read_path)


if __name__ == '__main__':
    main('eyeshadow_entries_with_color_with_center.txt', 'eyeshadow_entries_with_color_filtered.txt', num_clusters=5)
