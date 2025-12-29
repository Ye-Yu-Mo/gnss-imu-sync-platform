"""
数据结构定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TimestampedData:
    """带时间戳的数据基类"""
    year: int
    month: int
    day: int
    hour: int
    minute: int
    microsecond: int
    timestamp: float = field(init=False)  # 自动计算，不需要传入

    def __post_init__(self):
        """初始化后自动计算时间戳，如果时间非法则设为NaN"""
        try:
            dt = datetime(self.year, self.month, self.day, self.hour, self.minute, 0)
            self.timestamp = dt.timestamp() + self.microsecond / 1e6
        except (ValueError, OverflowError) as e:
            # 时间字段非法（如月份13），保留原始字段，timestamp设为NaN
            self.timestamp = float('nan')


@dataclass
class GNSSData(TimestampedData):
    """GNSS 数据结构（时间戳 + 位置 + 速度）"""
    longitude: float  # 经度（度）
    latitude: float   # 纬度（度）
    altitude: float   # 高度（米）

    velocity_x: float  # 速度 x（m/s）
    velocity_y: float  # 速度 y（m/s）
    velocity_z: float  # 速度 z（m/s）

    valid: bool = True  # 数据有效性


@dataclass
class IMUData(TimestampedData):
    """IMU 数据结构（时间戳 + 角增量 + 速度增量）"""
    gyro_x: float  # 三轴陀螺仪输出（rad/s）
    gyro_y: float
    gyro_z: float

    accel_x: float  # 三轴加速度输出（m/s²）
    accel_y: float
    accel_z: float


@dataclass
class NavigationResult(TimestampedData):
    """组合导航结果数据结构"""
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
