import logging
import os
import uvicorn
from fastapi import FastAPI, status, Request, HTTPException
import base64
import io
import PIL
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from match_deployment.wall_api import WallMatching
from match_deployment.milvus import MilvusSearchEngine

FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')

log_level = os.getenv('LOG_LEVEL', 'ERROR').upper()
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {log_level}")

format_status = os.environ.get('FORMAT_STATUS', default='PROD')

logging.config.dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters':
            {
                'json':
                    {
                        '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                        'format': FORMAT
                    },
                'simple':
                    {
                        'format': '%(asctime)s - %(levelname)s - %(message)s',
                    },
            },
        'handlers':
            {
                'consoleHandler':
                    {
                        'class': 'logging.StreamHandler',
                        'formatter': 'json' if format_status == 'PROD' else 'simple',
                    },
            },
        'root': {
            'level': numeric_level,
            'handlers': ['consoleHandler'],
        }
    }
)
logger = logging.getLogger(__name__)

# Initialize API Server
app = FastAPI(
    title='Wall Detection',
    description='API for Wall detection in Production',
    version='test',
    terms_of_service=None,
    contact=None,
    license_info=None
)

zilliz_uri = "https://in01-a79e60d0bae2a62.aws-ap-southeast-1.vectordb.zillizcloud.com:19532"
token = 'db_admin:ContextualCommerceW00t'
collection_name = 'au_prod_wall_demo'
num_res = 3

# initial WallMatching
wm = WallMatching(zilliz_uri, token, collection_name, num_res)
milvus_engine = MilvusSearchEngine(uri=zilliz_uri, token=token, collection_name=collection_name,
                                                size=num_res)

@app.get('/ping', status_code=status.HTTP_200_OK)
def ping():
    return {"message": "ok"}


# Create an FaceLandmarker object.
# 这里模型参数要根据实际情况改一下
base_options = python.BaseOptions(model_asset_path='face_landmarker_v2_with_blendshapes.task')
options = vision.FaceLandmarkerOptions(base_options=base_options,
                                       output_face_blendshapes=False,
                                       output_facial_transformation_matrixes=True,
                                       num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)


@app.post('/invocations')
async def wall_detection(request: Request):
    body = await request.json()
    image_byte = body['instances'][0]
    image_b64 = image_byte["image_bytes"]["b64"]
    base64_decoded = base64.b64decode(image_b64)
    image = io.BytesIO(base64_decoded)
    pil_image = PIL.Image.open(image)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(pil_image))
    re = detector.detect(image).json()
    # max_confidence = 0
    # mask = []
    # for i in range(len(re['results'])):
    #     score = float(re['results'][i][0].split("(")[-1].split(")")[0])
    #     if score > max_confidence:
    #         mask = np.asanyarray(re['results'][i][2]).squeeze()
    #         max_confidence = score
    # return mask, pil_image
    return re



@app.post('/wall')
async def return_wall_res(request: Request):
    try:
        avg = await wall_detection(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Detection failed!{e}')
    if not avg:
        raise HTTPException(status_code=500,
                            detail=f'Detection failed!')
    
    # img = np.array(pil_image)
    # channels = [img[:,:,0], img[:,:,1], img[:,:,2]]
    # avgs = []
    # for i in range(len(maskes)):
    #     mask = 1 - maskes[i]
    #     avgs.append([])
    #     for i in range(3):
    #         x = np.ma.array(channels[i], mask=mask)
    #         avgs[-1][i] = int(x.mean())
    # wall_res = []
    # for avg in avgs:
    #     wall_res.append(milvus_engine.query_wall(avg))
    wall_res = milvus_engine.query_wall(avg)
    res = {'wall': {'products': wall_res}}

    return res


if __name__ == '__main__':
    uvicorn.run(app, port=8020, host='0.0.0.0')
