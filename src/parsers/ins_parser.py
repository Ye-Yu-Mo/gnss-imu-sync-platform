"""
INS 帧解析器（附录1 INS帧格式，52字节）
"""
import struct
from typing import List, Optional
from ..models.data_types import IMUData


class INSFrameParser:
    """INS 帧解析器（52字节独立帧）"""

    INS_HEADER = bytes([0x55, 0xaa])
    INS_LENGTH = 0x34  # 52 字节

    @staticmethod
    def checksum(data: bytes) -> int:
        """计算校验和（求和取低8位）"""
        return sum(data) & 0xFF

    @staticmethod
    def parse_ins_frame(data: bytes) -> Optional[IMUData]:
        """
        解析单独的 INS 帧（52字节）
        返回 IMUData 或 None（解析失败）
        """
        if len(data) < 52:
            return None

        # 验证帧头
        if data[0:2] != INSFrameParser.INS_HEADER:
            return None

        # 验证长度字段
        if data[2] != INSFrameParser.INS_LENGTH:
            return None

        # 校验和验证（字节3-51求和取低8位）
        expected_checksum = INSFrameParser.checksum(data[3:51])
        actual_checksum = data[51]
        if expected_checksum != actual_checksum:
            return None

        # 解析 IMU 数据（低字节序）
        # 字节3-26: 三轴陀螺仪（3 × 8字节 double）
        gyro_x = struct.unpack('<d', data[3:11])[0]
        gyro_y = struct.unpack('<d', data[11:19])[0]
        gyro_z = struct.unpack('<d', data[19:27])[0]

        # 字节27-50: 三轴加速度计（3 × 8字节 double）
        accel_x = struct.unpack('<d', data[27:35])[0]
        accel_y = struct.unpack('<d', data[35:43])[0]
        accel_z = struct.unpack('<d', data[43:51])[0]

        # INS帧没有时间戳，暂时设为0
        return IMUData(
            timestamp=0.0,
            year=0,
            month=0,
            day=0,
            hour=0,
            minute=0,
            microsecond=0,
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            accel_x=accel_x,
            accel_y=accel_y,
            accel_z=accel_z
        )

    @staticmethod
    def parse_file(file_path: str) -> List[IMUData]:
        """
        解析 INS 数据文件（ASCII hex 编码，每行一帧）
        返回 IMUData 列表
        """
        imu_list = []

        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                # 转换为二进制
                try:
                    binary_data = bytes.fromhex(line)
                except ValueError:
                    continue

                # 解析 INS 帧
                imu = INSFrameParser.parse_ins_frame(binary_data)
                if imu:
                    imu_list.append(imu)

        return imu_list
