'''
beauty matching api: calling beauty od, get color from the bbox, search similar products in milvus.
'''
import numpy as np
from match_deployment.milvus import MilvusSearchEngine


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
