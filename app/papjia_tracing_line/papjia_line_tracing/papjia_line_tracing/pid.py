"""
@Descripttion: PID控制（保留原参数格式 + 修复队列错误 + 积分限幅 + 微分滤波）
@version: 2.1
@Author: 崔译文
@Date: 2024-03-07 16:45:49
"""


class PIDController:
    def __init__(self, Kp, Ki, Kd, integral_limit=0.5, derivative_alpha=0.3):
        """
        Args:
            Kp: 比例增益
            Ki: 积分增益
            Kd: 微分增益
            integral_limit: 积分限幅绝对值（防饱和）
            derivative_alpha: 微分项滤波系数 (0.0~1.0, 越小滤波越强)
        """
        # 参数校验
        if Kp < 0 or Ki < 0 or Kd < 0:
            raise ValueError("PID参数必须为非负值")

        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        # 积分限幅
        self.integral_limit = abs(integral_limit)
        self.integral = 0.0

        # 微分滤波
        self.derivative_alpha = derivative_alpha
        self.filtered_derivative = 0.0

        # 误差记录
        self.prev_error = 0.0

    def reset(self):
        """重置控制器状态"""
        self.prev_error = 0.0
        self.integral = 0.0
        self.filtered_derivative = 0.0

    def update(self, error, dt):
        """
        计算控制输出（参数与原版兼容）
        Args:
            error: 当前误差（target - current）
            dt: 距离上次更新的时间间隔（秒）
        Returns:
            控制器输出
        """
        # 处理dt异常
        if dt <= 0:
            dt = 1e-5

        # 比例项
        P = self.Kp * error

        # 积分项（带限幅）
        self.integral += error * dt
        self.integral = max(
            min(self.integral, self.integral_limit), -self.integral_limit
        )
        I = self.Ki * self.integral

        # 微分项（带滤波）
        raw_derivative = (error - self.prev_error) / dt
        self.filtered_derivative = (
            self.derivative_alpha * raw_derivative
            + (1 - self.derivative_alpha) * self.filtered_derivative
        )
        D = self.Kd * self.filtered_derivative

        print(f"--- PID({P}, {I}, {D}) ---", flush=True)

        # 保存误差
        self.prev_error = error

        return P + I + D
