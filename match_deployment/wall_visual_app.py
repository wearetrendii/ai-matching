'''
visualise beauty matching results for an input image.
'''
import base64
import os
from io import BytesIO

import requests
import streamlit as st
from PIL import Image, ImageDraw
from pymilvus import (
    connections,
    Collection
)

class MilvusSearchEngine:
    def __init__(self, uri=None, token=None, collection_name=None, size=None):
        self.query_size = size
        self.metric_type = 'L2'
        self.topk = size
        connections.connect(uri=uri,
                            token=token,
                            timeout=30)
        self.collection = Collection(collection_name)
        self.collection.load()

    def query_wall(self, color):
        vector_field = 'colour_value'
        search_param = {
            "data": [color],
            "anns_field": vector_field,
            "param": {"metric_type": self.metric_type},
            "limit": self.topk,
            # 这里也要根据milvus具体情况改一下
            "output_fields": ['unique_id', 'retailer_id', 'brand', 'price', 'currency', 'image', 'product_url',
                              'product_info'],
            "expr": f'category in ["wall paint"]'
        }
        product_infos = []
        results = self.collection.search(**search_param)
        for result in results:
            for res in result:
                product_infos.append(res.fields)
        return product_infos

    def get_wall_target_colors(self, cate):
        query_param = {
            "expr": f'category in ["{cate}"]',
            "output_fields": ["colour_value"]
        }
        target_colors_with_id = self.collection.query(**query_param)
        return target_colors_with_id

class WallMatching:
    def __init__(self, zilliz_uri, token, collection_name, num_res):
        self.milvus_engine = MilvusSearchEngine(uri=zilliz_uri, token=token, collection_name=collection_name,
                                                size=num_res)
        # 目录名字暂定是"wall"
        self.wall_target_colors_with_id = self.milvus_engine.get_wall_target_colors('wall paint')

    def get_wall_ave_color(self, wall_colors):
        colors = [l for wall_color_list in wall_colors for l in wall_color_list]
        average_color = [sum(col) / len(colors) for col in zip(*colors)]
        return average_color

    def search_wall_in_milvus(self, wall_colors):
        ave_wall_color = self.get_wall_ave_color(wall_colors)
        wall_res = self.milvus_engine.query_wall(ave_wall_color)
        return wall_res

def draw_bbox_on_image(image_path, bbox):
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        draw.rectangle(bbox, outline="red", width=3)
        return img

def get_b64_payload(file_path):
    with open(file_path, 'rb') as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')
        payload_json = {"instances": [{"image_bytes": {"b64": encoded_image}}]}
        return payload_json


def get_wall_res(payload_json, wall_api_url):
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", wall_api_url, headers=headers, json=payload_json, timeout=10)
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
            st.text(img_url)
            response = requests.get(img_url, timeout=20)
            img_bytes = response.content
            img = Image.open(BytesIO(img_bytes))
            images.append(img)
        except:
            continue

    if len(images) > 1:
        # If more than 3 results, dynamically create enough columns for each result
        cols = st.columns(len(images))
    else:
        # If 3 or fewer, put them all in one row
        # Use 1 as the argument to create a single column, then use that column multiple times
        cols = [st.columns(1)[0] for _ in range(len(images))]


    for col, img in zip(cols, images):
        if len(res) > 1:
            col.image(img, use_column_width=True)
        else:
            # When fewer than 4 images, let width decide size
            col.image(img, width=150)


def main():

    # 参数改一下
    wall_api_url = "https://47275qn2fe.execute-api.ap-southeast-2.amazonaws.com/beta/segment"
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    image_path = "C:\\Users\yaoxufan\\Desktop\\wall_test"

    zilliz_uri = "https://in01-a79e60d0bae2a62.aws-ap-southeast-1.vectordb.zillizcloud.com:19532"
    token = 'db_admin:ContextualCommerceW00t'
    collection_name = 'au_prod_wall_demo'
    num_res = 3

    # initial WallMatching
    wm = WallMatching(zilliz_uri, token, collection_name, num_res)
    milvus_engine = MilvusSearchEngine(uri=zilliz_uri, token=token, collection_name=collection_name,
                                                    size=num_res)

    for file_name in os.listdir(image_path):
        print(f'doing: {file_name}')
        # st.markdown("---")
        if not any(file_name.lower().endswith(ext) for ext in image_extensions): continue
        file_path = os.path.join(image_path, file_name)

        payload_json = get_b64_payload(file_path)
        try:
            avg = get_wall_res(payload_json, wall_api_url)
        except:
            print(file_name)
            continue

        if len(avg) < 3:
            st.text('failed to detect')
            continue
        
        wall_res = milvus_engine.query_wall(avg)
        for prod in wall_res:
            st.text(prod['image'])

        try:
            st.image(file_path, caption=file_name, width=400)
            show_res(wall_res)
        except:
            print(file_name)
            continue


if __name__ == '__main__':
    main()
