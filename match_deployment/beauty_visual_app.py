'''
visualise beauty matching results for an input image.
'''
import base64
import os
from io import BytesIO

import requests
import streamlit as st
from PIL import Image, ImageDraw


def draw_bbox_on_image(image_path, bbox):
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        draw.rectangle(bbox, outline="red", width=3)
        return img


def get_eye_shadow_bbox(payload_json):
    detect_url = 'http://52.62.40.78:8020/invocations'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", detect_url, headers=headers, json=payload_json, timeout=10)
        response_json = response.json()
        bbox = response_json['eysshadows']['eyeshadow_bbox']
    except Exception as e:
        print(f"Error during API call: {e}")
        return None
    if not bbox:
        return None
    return bbox


def get_b64_payload(file_path):
    with open(file_path, 'rb') as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')
        payload_json = {"instances": [{"image_bytes": {"b64": encoded_image}}]}
        return payload_json


def get_beauty_res(payload_json, beauty_api_url):
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", beauty_api_url, headers=headers, json=payload_json, timeout=10)
    if response.status_code != 200:
        raise Exception('API failed')
    res = response.json()
    return res


def show_res(res):


    images = []
    for prod in res:
        # Simplified the try/except block
        try:
            img_url = prod.get('image')
            response = requests.get(img_url, timeout=20)
            img_bytes = response.content
            img = Image.open(BytesIO(img_bytes))
            images.append(img)
        except:
            continue

    if len(images) > 1:
        # If more than 3 results, dynamically create enough columns for each result
        cols = st.beta_columns(len(images))
    else:
        # If 3 or fewer, put them all in one row
        # Use 1 as the argument to create a single column, then use that column multiple times
        cols = [st.beta_columns(1)[0] for _ in range(len(images))]



    for col, img in zip(cols, images):
        if len(res) > 1:
            col.image(img, use_column_width=True)
        else:
            # When fewer than 4 images, let width decide size
            col.image(img, width=150)


def main():
    beauty_api_url = 'http://52.62.40.78:8020/beauty'
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    iamge_path = "../all_images"

    for file_name in os.listdir(iamge_path):
        print(f'doing: {file_name}')
        # st.markdown("---")
        if not any(file_name.lower().endswith(ext) for ext in image_extensions): continue
        file_path = os.path.join(iamge_path, file_name)

        payload_json = get_b64_payload(file_path)
        try:
            res = get_beauty_res(payload_json, beauty_api_url)
            # bbox = get_eye_shadow_bbox(payload_json)
            # bbox = tuple(map(float, bbox.values()))
        except:
            print(file_name)
            continue

        try:
            lipstick_res = res['lipsticks']
            # original_img_with_bbox = draw_bbox_on_image(file_path, bbox)
            st.image(file_path, caption=file_name, width=400)
            st.text('lipsticks')
            show_res(lipstick_res)
        except:
            print(file_name)
            continue

        try:
            eyeshadows_res = res['eyeshadows']
            st.text('eyeshadows')
            show_res(eyeshadows_res)
        except:
            print(file_name)
            continue

        try:

            blushes_res = res['blushes']
            st.text('blushes')
            show_res(blushes_res)
        except:
            print(file_name)
            continue


if __name__ == '__main__':
    main()
