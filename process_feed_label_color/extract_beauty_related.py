'''
extract beauty categories from feeds using cm.
'''

from tqdm import tqdm
from cm import cr
import csv


def extract_beauty_entries(file_path):
    # Open files for writing entries
    lipstick_file = open('lipstick_entries_2.txt', 'w')
    eyeshadow_file = open('eyeshadow_entrie_2.txt', 'w')
    blush_file = open('blush_entries_2.txt', 'w')

    try:
        with open(file_path, 'r') as file:
            first_line = next(file, None).strip()  # Read the first line and remove trailing newline

            # Write the first line to all three files
            lipstick_file.write(first_line + '\n')
            eyeshadow_file.write(first_line + '\n')
            blush_file.write(first_line + '\n')

            # Process the rest of the file
            for line in tqdm(file):
                try:
                    content = line.strip()
                    cates = cr.extract_cat(content)
                    print(cates)

                    # Save content to appropriate file based on response
                    if 'lipstick' in cates:
                        lipstick_file.write(content + '\n')
                    elif 'eyeshadow' in cates:
                        eyeshadow_file.write(content + '\n')
                    elif 'blush' in cates:
                        blush_file.write(content + '\n')
                except Exception as e:
                    print(e)
                    continue

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close all opened files
        lipstick_file.close()
        eyeshadow_file.close()
        blush_file.close()

def parse_row(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        # Using csv.DictReader to automatically use the first line as dictionary keys
        # Specify the delimiter according to your file's format
        # If it's space-separated with quotes around complex fields, handling might need to be adjusted
        reader = csv.DictReader(file, delimiter='\t', quotechar='"')

        for row in reader:
            # Each 'row' here is a dictionary with keys from the first line and values from the current line
            # Convert row to dict if necessary (row is already a dict, but this ensures compatibility)
            entry = dict(row)
            sku = entry['sku']
            # Process or print each entry dictionary as needed
            print(entry)


if __name__ == '__main__':
    # extract_beauty_entries(file_path='becc9ab231ae7be8c617816cc52cb5a6.txt_598273.tmp')
    parse_row(file_path="lipstick_entries.txt")
