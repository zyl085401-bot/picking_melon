"""
@Descripttion: 小车速度更新模型
@version: 1.0
@Author: 崔译文
@Date: 2024-03-11 15:57:54
@LastEditors: 崔译文
@LastEditTime: 2024-03-14 17:10:50
"""


class Car:
    def __init__(self, wheel_separation, init_speed):
        """初始化速度、轮距信息

        Args:
            wheel_separation (float): 轮距
            init_speed (float): 车辆行进速度
        """
        self.wheel_separation = wheel_separation  # 轮距
        self.init_left_wheel_speed, self.init_right_wheel_speed = init_speed, init_speed
        self.left_wheel_speed = init_speed
        self.right_wheel_speed = init_speed

    def reset(self, init_speed):
        self.init_left_wheel_speed, self.init_right_wheel_speed = init_speed, init_speed
        self.left_wheel_speed = init_speed
        self.right_wheel_speed = init_speed

    def update_speed(self, adjustment):
        """根据adjustment调整速度

        Args:
            adjustment (float): 调整量

        Returns:
            list: 线速度和角速度
        """
        self.left_wheel_speed = self.init_left_wheel_speed + adjustment
        self.right_wheel_speed = self.init_right_wheel_speed - adjustment
        # 左右轮速度差
        differential_speed = self.right_wheel_speed - self.left_wheel_speed
        # 车辆速度（平均速度）
        car_speed = (self.left_wheel_speed + self.right_wheel_speed) / 2.0
        # 车辆角速度
        angular_velocity = differential_speed / self.wheel_separation
        return [car_speed, angular_velocity]
