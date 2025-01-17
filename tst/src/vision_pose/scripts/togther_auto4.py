#!/home/amov/anaconda3/envs/yolov8/bin/python
# 此处逻辑会开机自动启动这个代码，启动代码后五分钟后自动停止代码，同时识别的数字会记录到日志中，识别的视频会保存下来以供后续发现问题
# 此处还会建立文件夹使得识别到的天井照片储存下来
# 处理过后的天井照片也会储存下来`
# 缓解云台曝光问题
import logging
import time
from collections import Counter
import cv2
import numpy as np
from ultralytics import YOLO
import pos
import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import tf
import datetime
import os

origin_num = 0
rotate_num = 0
crop_num = 0
local_x = 0
local_y = 0
local_z = 0
local_yaw =0

now = datetime.datetime.now()

folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")

if not os.path.exists(f"/home/amov/Desktop/well{folder_name}"):
    os.mkdir(f"/home/amov/Desktop/well{folder_name}")
    os.mkdir(f"/home/amov/Desktop/well{folder_name}/origin")
    os.mkdir(f"/home/amov/Desktop/well{folder_name}/rotate")
    os.mkdir(f"/home/amov/Desktop/well{folder_name}/crop")

# 定义红色在HSV色彩空间的范围
lower_red1 = np.array([0, 50, 50])  # np.array([0, 120, 70])  # np.array([0, 20, 50])  #
upper_red1 = np.array([15, 255, 255])  # np.array([10, 255, 255])  # np.array([20, 255, 255])  #
lower_red2 = np.array([150, 50, 50])  # np.array([170, 120, 70])  # np.array([150, 20, 50])  #
upper_red2 = np.array([180, 255, 255])  # np.array([180, 255, 255])  # np.array([180, 255, 255])  #

# 定义更明亮的粉色区间
lower_pink = np.array([320, 150, 150])  # 提高饱和度和亮度的下限
upper_pink = np.array([360, 255, 255])  # 保持色调上限

# 定义保存视频的格式和编码，这里使用MP4编码
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# 创建VideoWriter对象，指定输出文件名、编码器、帧率和分辨率
out = cv2.VideoWriter(f"/home/amov/Desktop/well{folder_name}/output.mp4", fourcc, 5.0, (1920, 1080))

# logging.basicConfig(
#         filename=f"/home/amov/Desktop/well{folder_name}/output.log",  # 确保这是正确的路径
#         level=logging.INFO,
#         format=''
#     )

start_time = time.time()

# 有两处调节亮度的操作 搜索clip
classes_names = {0: '00', 1: '01', 2: '02', 3: '03', 4: '04', 5: '05', 6: '06', 7: '07', 8: '08', 9: '09', 10: '10', 11: '11', 12: '12', 13: '13', 14: '14', 15: '15', 16: '16', 17: '17', 18: '18', 19: '19', 20: '20', 21: '21', 22: '22', 23: '23', 24: '24', 25: '25', 26: '26', 27: '27', 28: '28', 29: '29', 30: '30', 31: '31', 32: '32', 33: '33', 34: '34', 35: '35', 36: '36', 37: '37', 38: '38', 39: '39', 40: '40', 41: '41', 42: '42', 43: '43', 44: '44', 45: '45', 46: '46', 47: '47', 48: '48', 49: '49', 50: '50', 51: '51', 52: '52', 53: '53', 54: '54', 55: '55', 56: '56', 57: '57', 58: '58', 59: '59', 60: '60', 61: '61', 62: '62', 63: '63', 64: '64', 65: '65', 66: '66', 67: '67', 68: '68', 69: '69', 70: '70', 71: '71', 72: '72', 73: '73', 74: '74', 75: '75', 76: '76', 77: '77', 78: '78', 79: '79', 80: '80', 81: '81', 82: '82', 83: '83', 84: '84', 85: '85', 86: '86', 87: '87', 88: '88', 89: '89', 90: '90', 91: '91', 92: '92', 93: '93', 94: '94', 95: '95', 96: '96', 97: '97', 98: '98', 99: '99'}
maxdet = 3
max_num = 3
# 定义yolo权重文件路径
MODELOBB = "/home/amov/ultralytics-main/yolo_obb_red.pt"
MODELCLASSIFY = "/home/amov/ultralytics-main/yolo_cls.pt"
print("loading obb model")
modelObb = YOLO(MODELOBB)  # 通常是pt模型的文件
print("loading classify model")
modelClassify = YOLO(MODELCLASSIFY)

# 定义调用摄像头索引
CAMERAINDEX = 0

streamInput = True

# 在模块顶层声明全局变量
dataList = []
num_list = []
num = -1
_pos = [0, 0, 0]
coordinate = (0, 0)
_time = 0
cropTensorList = [(0, 0), (0, 0), (0, 0), (0, 0)]


def auto_rotate(img):  # 此处image是numpy类型
    image = img.copy()

    # 调节图像亮度
    # image = (image * 0.7).clip(0, 255).astype(np.uint8)

    # 对图像进行锐化的处理
    # image = cv2.filter2D(image, -1, kernel=kernel1)

    crop_img = image[400:460, 140:180]
    # 将图像转换为HSV色彩空间
    hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)

    # 创建红色五边形的掩膜
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask1, mask2)

    # 创建更明亮的粉色的掩膜
    mask_pink = cv2.inRange(hsv, lower_pink, upper_pink)

    # 将红色和粉色的掩膜合并
    mask = cv2.bitwise_or(mask_red, mask_pink)

    # 进行形态学操作以去除噪声
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # 进行开运算（先腐蚀后膨胀）通过判断上边是白色或黑色来翻转图片

    if np.sum(np.sum(mask)) > 60 * 40 * 255 * 0.6:
        image = cv2.rotate(image, cv2.ROTATE_180)
        return image
    else:
        return image



def apply_num_rec_package(rawImage):
    if rawImage is not None:
        # 对图像进行裁切
        x1, y1 = 30, 280  # 80, 390
        x2, y2 = 320, 600  # 220, 520
        crop_image = rawImage[y1: y2, x1: x2]
        # 调节图像亮度(需要较亮的环境)
        # crop_image = (crop_image * 0.5).clip(0, 255).astype(np.uint8)
        # cv2.imshow("crop image", crop_image)
        # 腐蚀函数
        '''kernel = np.ones((10, 10), np.uint8)
        binary_img = cv2.dilate(binary_img, kernel, iterations=3)'''
        global crop_num
        crop_num += 1
        cv2.imwrite(f"/home/amov/Desktop/well{folder_name}/crop/{crop_num}.png", crop_image)
        # print(rawImage.shape[0], rawImage.shape[1])  # 打印的信息就是函数croptarget的宽度和高度
        results_classify = modelClassify.predict(
                            source=crop_image,
                            imgsz=640,
                            device='0',
                            half=True,
                            iou=0.4,
                            conf=0.5,
                            save=False
                            )
        global num
        num = classes_names[results_classify[0].probs.top1]
        # print(results_classify[0])
        print("Classify num is:" + num)
        # logging.info("Classify num is:" + num)
        with open(f'/home/amov/Desktop/well{folder_name}/output.txt', 'a') as file:
            file.write("Classify num is:" + num + "\n")
        num_list.append(num)
        return rawImage


def cropTarget(rawImage, cropTensor, width, height):
    global cropTensorList
    # 将Tensor转换为列表(该列表内有四个元素，每一个元素是一个坐标)
    cropTensorList = cropTensor.tolist()

    # 检查列表长度是否为4，如果不是，则可能存在问题
    if len(cropTensorList) != 4:
        raise ValueError("cropTensor must contain exactly 4 elements")

    # 根据条件选择不同的点集合
    if (cropTensorList[0][0] - cropTensorList[1][0]) ** 2 + (cropTensorList[0][1] - cropTensorList[1][1]) ** 2 > (
            cropTensorList[1][0] - cropTensorList[2][0]) ** 2 + (cropTensorList[1][1] - cropTensorList[2][1]) ** 2:
        rectPoints = np.array([cropTensorList[0], cropTensorList[1], cropTensorList[2], cropTensorList[3]],
                              dtype=np.float32)
    else:
        rectPoints = np.array([cropTensorList[3], cropTensorList[0], cropTensorList[1], cropTensorList[2]],
                              dtype=np.float32)

    dstPoints = np.array([[0, 0], [0, height], [width, height], [width, 0]], dtype=np.float32)

    affineMatrix = cv2.getAffineTransform(rectPoints[:3], dstPoints[:3])

    return cv2.warpAffine(rawImage, affineMatrix, (width, height))


def most_common_four_strings(strings):
    # 使用Counter计算每个字符串的出现次数
    count = Counter(strings)
    # 获取出现次数最多的四个字符串及其次数
    most_common = count.most_common(max_num)
    # 提取字符串
    result = [item[0] for item in most_common]
    return result

def obb_predict(frame):
    results_obb = modelObb.predict(
        source=frame,
        imgsz=640,  # 此处可以调节
        half=True,
        iou=0.4,
        conf=0.7,
        device='0',  # '0'使用GPU运行
        max_det=maxdet,
        save=False
        # augment = True
    )
    return results_obb[0]

def plot(result):
    try:
        annotatedFrame = result.plot()  # 获取框出的图像
        cropTensors = result.obb.xyxyxyxy.cpu()  # 矩形的四个坐标
        # cv2.imshow("target", annotatedFrame)
        # 将帧写入视频文件
        out.write(annotatedFrame)
    except AttributeError:
        print("No result.obb, maybe you have used a classify model")
    return cropTensors

def cls_predict():
    cropTensors = plot(result)
    for j, cropTensor in enumerate(cropTensors):
        framet = cropTarget(result.orig_img, cropTensor, 320, 640)
        if framet is not None and framet.size != 0:
            global origin_num
            origin_num += 1
            cv2.imwrite(f"/home/amov/Desktop/well{folder_name}/origin/{origin_num}.png", framet)
            # cv2.imshow("five", framet)
            framet = auto_rotate(framet)
            if framet is not None and framet.size != 0:
                global rotate_num
                rotate_num += 1
                cv2.imwrite(f"/home/amov/Desktop/well{folder_name}/rotate/{rotate_num}.png", framet)
                apply_num_rec_package(framet)
                imgdata = pos.Imgdata(image=result, pos=[local_x, local_y, local_z], coordinate=coordinate, num=num, time=_time, yaw = local_yaw)
                dataList.append(imgdata)
                # cv2.imshow("img_num" + str(j), img_num)
            else:
                continue
        else:
            continue

def coordinate_change(height=20, pos_=[0, 0, 20], yaw=0):
    #print("cropTensorList:", cropTensorList)  # 调试输出
    # 相机标定矩阵(完全已知，后期可能还要调节)
    a11 = 0.000731099032716040
    a12 = 0
    a13 = -0.979300105807494
    a21 = 0
    a22 = 0.000728955271191633
    a23 = -0.527880941143807
    a31 = 0
    a32 = 0
    a33 = 1

    # 相机内参的深度值(貌似是要测的)
    height = 20

    # u, v 是天井像素坐标系坐标
    well_width = (cropTensorList[0][0] + cropTensorList[2][0]) // 2
    well_height = (cropTensorList[0][1] + cropTensorList[2][1]) // 2
    # 用于调节相机畸变， 但此处未使用(后续看如何增加使用)
    k1 = -0.0735
    k2 = 0.0398
    p1 = -0.0016
    p2 = -0.0019

    # 从图像平面上的点反投影到相机坐标系中的点
    Xc = (well_width * a11 + well_height * a12 + 1 * a13) * height
    Yc = (well_width * a21 + well_height * a22 + 1 * a23) * height
    Zc = (well_width * a31 + well_height * a32 + 1 * a33) * height

    # 偏航角(通过ros获得)
    yaw = 0

    # 旋转矩阵(完全已知)
    b11 = np.cos(np.deg2rad(yaw))
    b12 = np.sin(np.deg2rad(yaw))
    b13 = 0
    b21 = -np.sin(np.deg2rad(yaw))
    b22 = np.cos(np.deg2rad(yaw))
    b23 = 0
    b31 = 0
    b32 = 0
    b33 = -1

    # 通过ros获取飞行的高度以及X与Y的值  此处默认设置为20
    X0 = pos_[0]
    Y0 = pos_[1]
    Z0 = pos_[2]

    # 相机坐标系通过旋转矩阵得到天井在真实世界的坐标
    Xw = Xc * b11 + Yc * b12 + Zc * b13 + X0
    Yw = Xc * b21 + Yc * b22 + Zc * b23 + Y0
    Zw = Xc * b31 + Yc * b32 + Zc * b33 + Z0


    return Xw, Yw, Zw

def get_middle(list):
    if list[0] < list[1] < list[2] or list[2] < list[1] < list[0]:
        return int(list[1])
    elif list[1] < list[0] < list[2] or list[2] < list[0] < list[1]:
        return int(list[0])
    elif list[0] < list[2] < list[1] or list[1] < list[2] < list[0]:
        return int(list[2])

def loc_pose_callback(msg):
    global local_x, local_y, local_z, local_yaw
    local_x = msg.pose.pose.position.x
    local_y = msg.pose.pose.position.y
    local_z = msg.pose.pose.position.z
    # local_x = msg.pose.position.x
    # local_y = msg.pose.position.y
    # local_z = msg.pose.position.z
    euler1 = tf.transformations.euler_from_quaternion([msg.pose.pose.orientation.x, msg.pose.pose.orientation.y, msg.pose.pose.orientation.z, msg.pose.pose.orientation.w])
    # euler1 = tf.transformations.euler_from_quaternion([msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w])
    local_yaw = euler1[2]
    #print("yaw = %f", euler1[2])
    #print("yaw = %f", local_yaw)

    # rospy.loginfo("yaw in /global_positon/local topic: %f", np.rad2deg(euler1[2]))

def statistic_frequency(list):
    statistic_list = {}
    empty_list = []
    length = len(list)
    for i in range(0, length):
        if list[i] not in statistic_list:
            statistic_list[list[i]] = 1
            empty_list.append(list[i])
        else:
            statistic_list[list[i]] += 1

    for i in range(0, len(empty_list)):
        value = statistic_list[empty_list[i]] / length
        percentage = value * 100
        formatted_percentage = "{:.2f}%".format(percentage)
        print(str(empty_list[i]) + " 占比为" + str(formatted_percentage))

if __name__=="__main__":
    rospy.init_node("vision_node")
    rate = rospy.Rate(5)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 330)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    frameWidth = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    frameHeight = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frameFps = cap.get(cv2.CAP_PROP_FPS)  # 帧率

    print(frameWidth, frameHeight, frameFps)
    while not rospy.is_shutdown():
        
        
        if cap.isOpened():
            print("camera is opened")
            # pose_data = rospy.wait_for_message("/mavros/global_position/local", PoseStamped, timeout=None)
            pose_data = rospy.wait_for_message("/mavros/global_position/local", Odometry, timeout=None)
            loc_pose_callback(pose_data)
            print("callback is used")
            success, frame = cap.read()
            print("frame is read")
            end_time = time.time()
            if success == True:
                if end_time - start_time > 180:
                    break
                #print(end_time - start_time)
                result = obb_predict(frame)
                # 按 'q' 键退出循环(必须有要不然没有画面 目前不知道为什么)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                cls_predict()  # 实现数字摆正与数字识别
            else:
                break
        rate.sleep()

    cap.release()
    cv2.destroyAllWindows()    
    zero_pose = [0, 0, 0]
    #print("numlist is: " + str(num_list))
    num_list = most_common_four_strings(num_list)
    #print("three numlist is: " + str(num_list))
    middle_num = get_middle(num_list)
    #print("middle_num is: " + str(middle_num))
    object_sum = len(dataList)
    #print("dateList length is: " + str(object_sum))
    middle_ = 0
    for k in range(0, object_sum):  # 识别到数字的有效
        # dataList[k].display()
        #print(f"{k} epoch: middle_num = " + str(middle_num) + " dataList[k].get_num() = " + str(dataList[k].get_num()))
        # print("type middle_num is; " + str(type(middle_num)) + " get_num type is: " + str(type(dataList[k].get_num())))
        #print("dataList[k].get_pos() is: " + dataList[k].get_pos()[0]+ " type is: " + str(type(dataList[k].get_pos())))
        if middle_num == int(dataList[k].get_num()):
            zero_pose[0] += coordinate_change(height= dataList[k].get_pos()[2], pos_ = dataList[k].get_pos(), yaw = dataList[k].get_yaw())[0]
            zero_pose[1] += coordinate_change(height= dataList[k].get_pos()[2], pos_ = dataList[k].get_pos(), yaw = dataList[k].get_yaw())[1]
            zero_pose[2] += coordinate_change(height= dataList[k].get_pos()[2], pos_ = dataList[k].get_pos(), yaw = dataList[k].get_yaw())[2]
            middle_ += 1
            #print("middle_ += 1")
    final_pos = [zero_pose[0] / middle_, zero_pose[1] / middle_, zero_pose[2] / middle_]

    # 对应着飞机打点得到的坐标位置
    print("the final coordinate is:" + str(final_pos))
    print("the final number is" + str(most_common_four_strings(num_list)))
    print("middle_num is: " + str(middle_num))
    # logging.info("the final coordinate is:" + str(final_pos))
    # logging.info("the final number is" + str(most_common_four_strings(num_list)))
    # logging.info("middle_num is: " + str(middle_num))
    with open(f'/home/amov/Desktop/well{folder_name}/output.txt', 'a') as file:
        file.write("the final coordinate is:" + str(final_pos) + "\n")
        file.write("the final number is" + str(most_common_four_strings(num_list)) + "\n")
        file.write("middle_num is: " + str(middle_num) + "\n")
    print("finished!")

