'''
visualise beauty matching results for an input image.
'''
import base64
import os
from io import BytesIO
import math
import requests
import json
import streamlit as st
from PIL import Image
from queue import PriorityQueue
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

    def query_wall(self, color, lab = False):
        vector_field = 'colour_value' if not lab else 'colour_value_lab'
        search_param = {
            "data": [color],
            "anns_field": vector_field,
            "param": {"metric_type": self.metric_type},
            "limit": self.topk,
            "output_fields": ['unique_id', 'retailer_id', 'brand', 'price', 'currency', 'image', 'product_url'],
            "expr": f'category in ["wall paint"]'
        }
        if lab:
            search_param["output_fields"].append("colour_value_lab")
        else:
            search_param["output_fields"].append("colour_value")
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
    distances = []
    for prod in res:
        # Simplified the try/except block
        try:
            img_url = prod.get('image')
            response = requests.get(img_url, timeout=20)
            img_bytes = response.content
            img = Image.open(BytesIO(img_bytes))
            images.append(img)
            distances.append(round(prod.get('distance'),4))
        except:
            continue

    if len(images) > 1:
        # If more than 3 results, dynamically create enough columns for each result
        cols = st.columns(len(images))
    else:
        # If 3 or fewer, put them all in one row
        # Use 1 as the argument to create a single column, then use that column multiple times
        cols = [st.columns(1)[0] for _ in range(len(images))]


    for col, img, dis in zip(cols, images, distances):
        if len(res) > 1:
            col.image(img, use_column_width=True)
            col.header(dis)
        else:
            # When fewer than 4 images, let width decide size
            col.image(img, width=150)

def CIEDE2000(Lab_1, Lab_2):
    '''Calculates CIEDE2000 color distance between two CIE L*a*b* colors'''
    C_25_7 = 6103515625 # 25**7
    
    L1, a1, b1 = Lab_1[0], Lab_1[1], Lab_1[2]
    L2, a2, b2 = Lab_2[0], Lab_2[1], Lab_2[2]
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_ave = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(C_ave**7 / (C_ave**7 + C_25_7)))
    
    L1_, L2_ = L1, L2
    a1_, a2_ = (1 + G) * a1, (1 + G) * a2
    b1_, b2_ = b1, b2
    
    C1_ = math.sqrt(a1_**2 + b1_**2)
    C2_ = math.sqrt(a2_**2 + b2_**2)
    
    if b1_ == 0 and a1_ == 0: h1_ = 0
    elif a1_ >= 0: h1_ = math.atan2(b1_, a1_)
    else: h1_ = math.atan2(b1_, a1_) + 2 * math.pi
    
    if b2_ == 0 and a2_ == 0: h2_ = 0
    elif a2_ >= 0: h2_ = math.atan2(b2_, a2_)
    else: h2_ = math.atan2(b2_, a2_) + 2 * math.pi

    dL_ = L2_ - L1_
    dC_ = C2_ - C1_    
    dh_ = h2_ - h1_
    if C1_ * C2_ == 0: dh_ = 0
    elif dh_ > math.pi: dh_ -= 2 * math.pi
    elif dh_ < -math.pi: dh_ += 2 * math.pi        
    dH_ = 2 * math.sqrt(C1_ * C2_) * math.sin(dh_ / 2)
    
    L_ave = (L1_ + L2_) / 2
    C_ave = (C1_ + C2_) / 2
    
    _dh = abs(h1_ - h2_)
    _sh = h1_ + h2_
    C1C2 = C1_ * C2_
    
    if _dh <= math.pi and C1C2 != 0: h_ave = (h1_ + h2_) / 2
    elif _dh  > math.pi and _sh < 2 * math.pi and C1C2 != 0: h_ave = (h1_ + h2_) / 2 + math.pi
    elif _dh  > math.pi and _sh >= 2 * math.pi and C1C2 != 0: h_ave = (h1_ + h2_) / 2 - math.pi 
    else: h_ave = h1_ + h2_
    
    T = 1 - 0.17 * math.cos(h_ave - math.pi / 6) + 0.24 * math.cos(2 * h_ave) + 0.32 * math.cos(3 * h_ave + math.pi / 30) - 0.2 * math.cos(4 * h_ave - 63 * math.pi / 180)
    
    h_ave_deg = h_ave * 180 / math.pi
    if h_ave_deg < 0: h_ave_deg += 360
    elif h_ave_deg > 360: h_ave_deg -= 360
    dTheta = 30 * math.exp(-(((h_ave_deg - 275) / 25)**2))
    
    R_C = 2 * math.sqrt(C_ave**7 / (C_ave**7 + C_25_7))  
    S_C = 1 + 0.045 * C_ave
    S_H = 1 + 0.015 * C_ave * T
    
    Lm50s = (L_ave - 50)**2
    S_L = 1 + 0.015 * Lm50s / math.sqrt(20 + Lm50s)
    R_T = -math.sin(dTheta * math.pi / 90) * R_C

    k_L, k_C, k_H = 1, 1, 1
    
    f_L = dL_ / k_L / S_L
    f_C = dC_ / k_C / S_C
    f_H = dH_ / k_H / S_H
    
    dE_00 = math.sqrt(f_L**2 + f_C**2 + f_H**2 + R_T * f_C * f_H)
    return dE_00



def main():

    wall_api_url = "https://47275qn2fe.execute-api.ap-southeast-2.amazonaws.com/beta/segment"
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    image_path = "C:\\Users\\yaoxufan\\Desktop\\wall_test"

    zilliz_uri = "https://in01-a79e60d0bae2a62.aws-ap-southeast-1.vectordb.zillizcloud.com:19532"
    token = 'db_admin:ContextualCommerceW00t'
    collection_name = 'au_prod_wall_demo'
    num_res = 3

    milvus_engine = MilvusSearchEngine(uri=zilliz_uri, token=token, collection_name=collection_name,
                                                    size=num_res)
    milvus_engine_lab = MilvusSearchEngine(uri=zilliz_uri, token=token, collection_name='au_prod_wall_demo_lab',
                                                    size=10)

    for file_name in os.listdir(image_path):
        print(f'doing: {file_name}')
        # st.markdown("---")
        if not any(file_name.lower().endswith(ext) for ext in image_extensions): continue
        file_path = os.path.join(image_path, file_name)

        payload_json = get_b64_payload(file_path)
        try:
            avg_lab = get_wall_res(payload_json, wall_api_url)["seg_output2"]
        except:
            print(file_name)
            continue

        if len(avg_lab) < 3:
            st.text('failed to detect')
            continue
        
        # wall_res = milvus_engine.query_wall(avg)
        wall_res_lab = milvus_engine_lab.query_wall(avg_lab, True)
        temp = PriorityQueue()
        for res in wall_res_lab:
            res['distance'] = math.dist(avg_lab, res['colour_value_lab'])
            score = CIEDE2000(avg_lab, res['colour_value_lab'])
            temp.put((score, res))
        wall_res_lab, i = [], 0
        while i < 5 and not temp.empty():
            wall_res_lab.append(temp.get()[1])
            i += 1

        try:
            img = Image.open(file_path)
            st.image(img, caption=file_name, width=400)
            # st.text(avg)
            # st.text("RGB matching results")
            # show_res(wall_res)
            st.text("LAB matching results")
            show_res(wall_res_lab)
        except:
            print(file_name)
            continue


if __name__ == '__main__':
    main()
