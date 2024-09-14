class Imgdata(object):
    def __init__(self, image, pos, coordinate, num, time, yaw):  # pos是飞机三维坐标，coordinate是天井在照片的二维坐标
        self.image = image  # 图像
        self.pos = pos  # x, y, z
        self.coordinate = coordinate  # 二维坐标
        self.num = num  # 识别到的数字
        self.time = time  # 时间戳
        self.yaw = yaw

    @staticmethod
    def make_struct(image, pos, coordinate, num, time, yaw):
        return Imgdata(image, pos, coordinate, num, time, yaw)

    def get_pos_and_coordinate(self):
        return self.pos, self.coordinate

    def get_pos(self):
        return self.pos

    def get_coordinate(self):
        return self.coordinate

    def get_num(self):
        return self.num

    def grt_time(self):
        return self.time

    def get_yaw(self):
        return self.yaw

    def display(self):
        print("num is: ", self.num)
        print("pos is: ", self.pos)
        print("yaw is: ", self.yaw)