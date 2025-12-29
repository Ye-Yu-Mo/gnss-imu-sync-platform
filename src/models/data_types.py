"""
数据结构定义
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GNSSData:
    """GNSS 数据结构（时间戳 + 位置 + 速度）"""
    timestamp: float  # 秒（从某个基准时间开始）
    year: int
    month: int
    day: int
    hour: int
    minute: int
    microsecond: int

    longitude: float  # 经度（度）
    latitude: float   # 纬度（度）
    altitude: float   # 高度（米）

    velocity_x: float  # 速度 x（m/s）
    velocity_y: float  # 速度 y（m/s）
    velocity_z: float  # 速度 z（m/s）

    valid: bool = True  # 数据有效性

    def to_timestamp(self) -> float:
        """转换为时间戳（秒）"""
        dt = datetime(self.year, self.month, self.day,
                     self.hour, self.minute, 0)
        return dt.timestamp() + self.microsecond / 1e6


@dataclass
class IMUData:
    """IMU 数据结构（时间戳 + 角增量 + 速度增量）"""
    timestamp: float  # 秒（从某个基准时间开始）
    year: int
    month: int
    day: int
    hour: int
    minute: int
    microsecond: int

    gyro_x: float  # 三轴陀螺仪输出（rad/s）
    gyro_y: float
    gyro_z: float

    accel_x: float  # 三轴加速度输出（m/s²）
    accel_y: float
    accel_z: float

    def to_timestamp(self) -> float:
        """转换为时间戳（秒）"""
        dt = datetime(self.year, self.month, self.day,
                     self.hour, self.minute, 0)
        return dt.timestamp() + self.microsecond / 1e6


@dataclass
class NavigationResult:
    """组合导航结果数据结构"""
    timestamp: float
    year: int
    month: int
    day: int
    hour: int
    minute: int
    microsecond: int

    nav_status: int  # 0:纯惯；2:松组合；3:对准；4:待机

    # 组合导航信息
    combined_longitude: float
    combined_latitude: float
    combined_altitude: float
    combined_vel_x: float
    combined_vel_y: float
    combined_vel_z: float
    combined_roll: float
    combined_heading: float
    combined_pitch: float

    # 纯惯导信息
    ins_longitude: float
    ins_latitude: float
    ins_altitude: float
    ins_vel_x: float
    ins_vel_y: float
    ins_vel_z: float
    ins_roll: float
    ins_heading: float
    ins_pitch: float

    frame_index: int  # 帧序号 0-199

    def to_timestamp(self) -> float:
        """转换为时间戳（秒）"""
        dt = datetime(self.year, self.month, self.day,
                     self.hour, self.minute, 0)
        return dt.timestamp() + self.microsecond / 1e6
