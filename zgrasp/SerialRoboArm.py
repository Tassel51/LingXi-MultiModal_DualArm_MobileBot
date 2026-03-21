from functools import wraps
import time

import serial
import json


class SerialArmControllerClass:
    # 串口配置参数
    __baud_rate: int
    __serial_port: str
    __busy_flag: bool
    # 当前坐标（直接来自串口）
    __coord_x: float

    @property
    def coord_x(self) -> float:
        return self.__coord_x

    __coord_y: float

    @property
    def coord_y(self) -> float:
        return self.__coord_y

    __coord_z: float

    @property
    def coord_z(self) -> float:
        return self.__coord_z

    __coord_t: float

    @property
    def coord_t(self) -> float:
        return self.__coord_t

    __coord_g: float

    @property
    def coord_g(self) -> float:
        return self.__coord_g

    __step_delay: int = 10

    @property
    def step_delay(self) -> int:
        return self.__step_delay

    @step_delay.setter
    def step_delay(self, step_delay) -> None:
        self.__step_delay = step_delay

    __grabber_speed: int = 200

    @property
    def grabber_speed(self) -> int:
        return self.__grabber_speed

    @grabber_speed.setter
    def grabber_speed(self, grabber_speed) -> None:
        self.__grabber_speed = grabber_speed

    __serial_entity: serial.Serial

    def __init__(self, serial_port="serial_port", baud_rate=115200):
        # 打开串口
        self.__serial_port = serial_port
        self.__baud_rate = baud_rate
        try:
            self.__serial_entity = serial.Serial(self.__serial_port, self.__baud_rate)
        except serial.SerialException as e:
            print(f'Error opening serial port{self.__serial_port}, {e}')
            exit(1)
        # 后续可能有多线程操作，留个装饰器备用
        self.__busy_flag = False
        # 初始化一次坐标变量
        self.coord_ctrl()
        import time


    def busy(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.__busy_flag:
                print(f'robot arm {self.__serial_port} is busy,access is denied')
                return
            self.__busy_flag = True
            ans = func(self, *args, **kwargs)
            self.__busy_flag = False
            return ans
        return wrapper

    def __send_command_frame(self, frame: json) -> bool:
        """
        通过串口向下位机发送控制帧
        :param frame: 待写入的控制帧
        :return: 是否成功写入
        """
        try:
            self.__serial_entity.write(frame.encode())
        except serial.SerialException as e:
            print("Error writing to serial port:", e)
            return False
        return True

    # COORD_CTRL: T:cmdType, P1 - 3: coordInput, P4: thetaAngle, P5: grabberAngle, S1: stepDelay, S5: grabberSpeed
    # {"T": 2, "P1": 277.5104065, "P2": -13.75, "P3": 276.5822754, "P4": 90, "P5": 180, "S1": 10, "S5": 200}
    @busy
    def coord_ctrl(self, target_x: float = 277, target_y: float = -14, target_z: float = 277,
                   theta_angle: float = 90, grabber_angle: float = 180) -> None:
        """
        逆运动学解算机械臂位置（xyz坐标系）
        COORD_CTRL: T:cmdType, P1 - 3: coordInput, P4: thetaAngle, P5: grabberAngle, S1: stepDelay, S5: grabberSpeed
        {"T": 2, "P1": 277.5104065, "P2": -13.75, "P3": 276.5822754, "P4": 90, "P5": 180, "S1": 10, "S5": 200}
        :param target_x: 目标x坐标
        :param target_y: 目标y坐标
        :param target_z: 目标z坐标
        :param theta_angle: 爪子的偏角
        :param grabber_angle: 爪子的张开角度,360为完全关闭
        """
        command_frame: str = (f'{{"T": 2, "P1": {target_x}, "P2": {target_y}, "P3": {target_z}, '
                              f'"P4": {theta_angle}, "P5": {grabber_angle}, '
                              f'"S1": {self.step_delay}, "S5": {self.grabber_speed}}}')
        self.__serial_entity.flush()
        if self.__send_command_frame(command_frame):
            # time.sleep(1)

            data: bytes = self.__serial_entity.read_until(b'\n')
            print(data)
            data = self.__serial_entity.read_until(b'\n')
            print(data)
            try:
                json_data = json.loads(data.decode('utf-8'))
                # 更新位置坐标
                print("JSON 数据：", json_data)
                self.__coord_x = json_data["P1"]
                self.__coord_y = json_data["P2"]
                self.__coord_z = json_data["P3"]
                self.__coord_t = json_data["P4"]
                self.__coord_g = json_data["P5"]
            except json.JSONDecodeError:
                self.__coord_x = target_x
                self.__coord_y = target_y
                self.__coord_z = target_z
                self.__coord_t = theta_angle
                self.__coord_g = grabber_angle
        else:
            raise Warning("串口工作异常")

    def get_device_info(self) -> None:
        """
        获取机械臂硬件信息
        :return:None
        """
        command_frame = '{"T":4}'
        self.send_command_frame(command_frame)
        raise NotImplementedError

    def get_angle_torque_info(self) -> None:
        """
        获取每个舵机的角度和力矩
        :return:None
        """
        command_frame = '{"T":5}'
        self.send_command_frame(command_frame)
        raise NotImplementedError

    def get_info_buffer(self):
        raise Warning("接口废弃", DeprecationWarning)
        command_frame = '{"T":6}'
        self.send_command_frame(command_frame)
        raise NotImplementedError

    def placeholder(self):
        raise Warning("接口废弃", DeprecationWarning)
        command_frame = '{"T":7}'
        self.send_command_frame(command_frame)
        raise NotImplementedError
