'''filter out invalid entries and split the file into three separate files for lipsticks, eyeshadows, and blushes.'''
import csv

lipstick_cates = ['Lip Kits', 'Lipstick', 'Customisable Looks', 'Makeup Kits', 'Lip Liner', 'Lip Gloss',
                  'Hot Lips 2', 'Collections - Pillow Talk', 'Hot Lips', "Liquid Lips", "Lips", "Hydrating Lipstick"]

eyeshadow_cates = ["Customisable Looks", "Makeup Kits", "Eye Kits", "Cream Eyeshadow", "Luxury Palette", "Eyeshadow",
                   "Collections - Pillow Talk", "Eyeshadow Pencil", "Eyeshadow Palette"]

blush_cates = ['Customisable Looks', 'Makeup Kits', 'Cheek Kits', 'Cheek', 'Collections - Pillow Talk', 'Powder Blush',
               'Highlighter', 'Bronzer', 'Face Palettes']


def parse_file(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')

        # Prepare to write filtered data to different files
        lipstick_file = open('Charlotte_Tilbury_lipsticks.csv', 'w', newline='', encoding='utf-8')
        eyeshadow_file = open('Charlotte_Tilbury_eyeshadows.csv', 'w', newline='', encoding='utf-8')
        blush_file = open('Charlotte_Tilbury_blushes.csv', 'w', newline='', encoding='utf-8')

        lipstick_writer = csv.DictWriter(lipstick_file, fieldnames=reader.fieldnames)
        eyeshadow_writer = csv.DictWriter(eyeshadow_file, fieldnames=reader.fieldnames)
        blush_writer = csv.DictWriter(blush_file, fieldnames=reader.fieldnames)

        # Write headers to each file
        lipstick_writer.writeheader()
        eyeshadow_writer.writeheader()
        blush_writer.writeheader()

        for row in reader:
            product_type = row['product_type']
            if product_type in lipstick_cates:
                lipstick_writer.writerow(row)
            elif product_type in eyeshadow_cates:
                eyeshadow_writer.writerow(row)
            elif product_type in blush_cates:
                blush_writer.writerow(row)

        # Close the files
        lipstick_file.close()
        eyeshadow_file.close()
        blush_file.close()


# Example usage:
file_path = 'Charlotte_Tilbury.csv'
parsed_data = parse_file(file_path)
