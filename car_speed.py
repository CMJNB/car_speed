import os
import cv2
import dlib
import time
import threading
import math

# 提取车辆的Harr特征
# 加载车辆识别的分类器
carCascade = cv2.CascadeClassifier('myhaar.xml')

VIDEOPATH = "video/"
VIDEONAME = "cars.mp4"
WIDTH = 1280
HEIGHT = 720
carWidht = 1.85


# 定义速度测算函数
def estimateSpeed(location1, location2):
    # 计算像素距离
    d_pixels = math.sqrt(math.pow(location2[0] - location1[0], 2) + math.pow(location2[1] - location1[1], 2))

    ppm = location2[2] / carWidht
    d_meters = d_pixels / ppm
    fps = 18
    speed = d_meters * fps * 3.6
    return speed


def trackMultipleObjects(videopath=VIDEOPATH, videoname=VIDEONAME):
    print(rf"{videopath}{videoname}")
    out_path = f'{videopath}out/'
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    outVideName = out_path + videoname.split('.')[0] + '_out.mp4'
    # 读取视频文件
    video = cv2.VideoCapture(rf"{videopath}{videoname}")
    # 获取视频的帧速率
    video_fps = video.get(cv2.CAP_PROP_FPS)
    # 获取视频的高度
    video_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # 获取视频的宽度
    video_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    print(outVideName, video_fps, video_height, video_width)
    rectangleColor = (0, 0, 225)
    frameCounter = 0
    currentCarID = 0
    fps = 0

    carTracker = {}
    carNumbers = {}
    carLocation1 = {}
    carLocation2 = {}
    speed = [None] * 1000

    # 写入文本
    out = cv2.VideoWriter('outpy.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (WIDTH, HEIGHT))

    # 初始化视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(outVideName, fourcc, video_fps, (WIDTH, HEIGHT), True)

    while True:
        # 读取视频帧
        start_time = time.time()
        rc, image = video.read()
        # 检查是否到达视频末尾
        if type(image) == type(None):
            break

        # 转换帧的大小，以加快处理速度
        image = cv2.resize(image, (WIDTH, HEIGHT))
        resultImage = image.copy()

        frameCounter = frameCounter + 1

        carIDtoDelete = []

        # 建立追踪目标
        for carID in carTracker.keys():
            trackingQuality = carTracker[carID].update(image)

            if trackingQuality < 7:
                carIDtoDelete.append(carID)

        for carID in carIDtoDelete:
            print('Removing carID ' + str(carID) + ' from list of trackers.')  # 从名单
            print('Removing carID ' + str(carID) + ' previous location.')  # 上一个地点
            print('Removing carID ' + str(carID) + ' current location.')  # 当前位置
            carTracker.pop(carID, None)
            carLocation1.pop(carID, None)
            carLocation2.pop(carID, None)

        if not (frameCounter % 10):
            # 将图像转换成灰度图像
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 检测视频中的车辆，并用vector保存车辆的坐标、大小（用矩形表示）
            # x,y表示第n帧第i个运动目标外接矩形的中心横坐标和纵坐标位置，该坐标可以大致描述车辆目标所在的位置。
            # w,h表示第n帧第i个运动目标外接矩形的宽度和长度，可以描述车辆目标的大小
            cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))

            # 车辆检测
            for (_x, _y, _w, _h) in cars:
                x = int(_x)
                y = int(_y)
                w = int(_w)
                h = int(_h)

                x_bar = x + 0.5 * w
                y_bar = y + 0.5 * h

                matchCarID = None

                for carID in carTracker.keys():
                    trackedPosition = carTracker[carID].get_position()

                    t_x = int(trackedPosition.left())
                    t_y = int(trackedPosition.top())
                    t_w = int(trackedPosition.width())
                    t_h = int(trackedPosition.height())

                    t_x_bar = t_x + 0.5 * t_w
                    t_y_bar = t_y + 0.5 * t_h

                    if (t_x <= x_bar <= (t_x + t_w)) and (t_y <= y_bar <= (t_y + t_h)) and (
                            x <= t_x_bar <= (x + w)) and (y <= t_y_bar <= (y + h)):
                        matchCarID = carID

                if matchCarID is None:
                    # 构造追踪器
                    print('Creating new tracker ' + str(currentCarID))

                    tracker = dlib.correlation_tracker()
                    # 设置追踪器的初始位置
                    # 如果识别出车辆，会以Rect(x,y,w,h)的形式返回车辆的位置，然后我们可以用一个矩形网格标识车辆
                    tracker.start_track(image, dlib.rectangle(x, y, x + w, y + h))

                    carTracker[currentCarID] = tracker
                    # 用于生成追踪器所需要的矩形框
                    carLocation1[currentCarID] = [x, y, w, h]

                    currentCarID = currentCarID + 1

        for carID in carTracker.keys():
            # 获得追踪器的当前位置
            trackedPosition = carTracker[carID].get_position()

            t_x = int(trackedPosition.left())
            t_y = int(trackedPosition.top())
            t_w = int(trackedPosition.width())
            t_h = int(trackedPosition.height())

            cv2.rectangle(resultImage, (t_x, t_y), (t_x + t_w, t_y + t_h), rectangleColor, 4)

            carLocation2[carID] = [t_x, t_y, t_w, t_h]

        # 计算时间差
        end_time = time.time()

        # 计算帧率
        if not (end_time == start_time):
            fps = 1.0 / (end_time - start_time)

            # 计算车速
        for i in carLocation1.keys():
            if frameCounter % 1 == 0:
                [x1, y1, w1, h1] = carLocation1[i]
                [x2, y2, w2, h2] = carLocation2[i]

                carLocation1[i] = [x2, y2, w2, h2]

                if [x1, y1, w1, h1] != [x2, y2, w2, h2]:
                    if (speed[i] == None or speed[i] == 0) and y1 >= 275 and y1 <= 285:
                        speed[i] = estimateSpeed([x1, y1, w1, h1], [x2, y2, w2, h2])

                    if speed[i] != None and y1 >= 180:
                        cv2.putText(resultImage, str(int(speed[i])) + " km/h", (int(x1 + w1 / 2), int(y1 - 5)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        # cv2.imshow('result', resultImage)
        # 保存视频
        writer.write(resultImage)

        if cv2.waitKey(33) == 27:
            break

    cv2.destroyAllWindows()
    # 释放
    writer.release()
    # 返回视频地址
    return outVideName

# if __name__ == '__main__':
#     trackMultipleObjects()
