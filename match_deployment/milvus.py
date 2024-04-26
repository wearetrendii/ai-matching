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
            "expr": f'category in ["lipstick"]'
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


if __name__ == "__main__":
    # 这里需要根据具体存储情况改一下
    zilliz_uri = "https://in01-a79e60d0bae2a62.aws-ap-southeast-1.vectordb.zillizcloud.com:19532"
    token = 'db_admin:ContextualCommerceW00t'
    collection_name = 'au_prod_beauty_v1'
    
    es_engine = MilvusSearchEngine(uri=zilliz_uri, token=token, collection_name=collection_name, size=20)
