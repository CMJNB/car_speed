import os

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import car_speed

app = FastAPI()


@app.post("/file/upload")
async def upload(file: UploadFile = File(...)):
    fn = file.filename
    save_path = f'./file/'
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    # 写出视频
    save_file = os.path.join(save_path, fn)
    f = open(save_file, 'wb')
    data = await file.read()
    f.write(data)
    f.close()
    # 处理视频
    out_file = car_speed.trackMultipleObjects(save_path, fn)
    # 返回视频
    return FileResponse(out_file, media_type="video/mp4")


if __name__ == '__main__':
    uvicorn.run(app=app, host="0.0.0.0", )
