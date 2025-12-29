"""
十六进制混合帧解析器（附录1格式）
"""
import logging
import struct
from typing import List, Tuple, Optional
from ..models.data_types import GNSSData, IMUData

logger = logging.getLogger(__name__)


class HexFrameParser:
    """十六进制混合帧解析器"""

    GNSS_HEADER = bytes([0x99, 0x66])
    INS_HEADER = bytes([0x55, 0xaa])  # PDF 附录1：0x55, 0xaa（不是 0x55ca）
    GNSS_LENGTH = 0x2e  # 46 字节
    INS_LENGTH = 0x34   # 52 字节

    @staticmethod
    def checksum(data: bytes) -> int:
        """计算校验和（求和取低8位）"""
        return sum(data) & 0xFF

    @staticmethod
    def parse_gnss_frame(data: bytes) -> Optional[GNSSData]:
        """
        解析 GNSS 帧（附录1格式）
        返回 GNSSData 或 None（解析失败）
        """
        if len(data) < 46:
            return None

        # 验证帧头
        if data[0:2] != HexFrameParser.GNSS_HEADER:
            return None

        # 验证长度
        if data[2] != HexFrameParser.GNSS_LENGTH:
            return None

        # 校验和验证（字节4-45求和取低8位）
        expected_checksum = HexFrameParser.checksum(data[3:45])
        actual_checksum = data[45]
        if expected_checksum != actual_checksum:
            logger.warning(f"GNSS 校验和错误: 期望 {expected_checksum:02x}, 实际 {actual_checksum:02x}")
            return None

        # 解析时间戳（低字节序）
        year = struct.unpack('<H', data[3:5])[0]
        month = data[5]
        day = data[6]
        hour = data[7]
        minute = data[8]
        microsecond = struct.unpack('<I', data[9:13])[0]

        # 边界检查：时间戳合法性
        if year < 2000 or year > 2100:
            logger.warning(f"GNSS 时间戳非法: 年份 {year}")
            return None

        # 解析 GNSS 数据（低字节序）
        longitude = struct.unpack('<d', data[13:21])[0]
        latitude = struct.unpack('<d', data[21:29])[0]
        altitude = struct.unpack('<f', data[29:33])[0]
        velocity_x = struct.unpack('<f', data[33:37])[0]
        velocity_y = struct.unpack('<f', data[37:41])[0]
        velocity_z = struct.unpack('<f', data[41:45])[0]

        return GNSSData(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            microsecond=microsecond,
            longitude=longitude,
            latitude=latitude,
            altitude=altitude,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            velocity_z=velocity_z
        )

    @staticmethod
    def parse_ins_frame(data: bytes) -> Optional[IMUData]:
        """
        解析 INS 帧（附录1格式，98字节混合帧中的INS部分）

        注意：当前数据文件中GNSS和INS是分开存储的，此函数暂未使用。
        如果未来需要解析98字节混合帧，可以启用此函数。

        返回 IMUData 或 None（解析失败）
        """
        # 此函数期待98字节混合帧，但当前数据是分离的
        # 保留代码以备未来使用
        if len(data) < 98:
            return None

        # 验证帧头（从字节46开始）
        if data[46:48] != HexFrameParser.INS_HEADER:
            return None

        # 验证长度
        if data[48] != HexFrameParser.INS_LENGTH:
            return None

        # 校验和验证（字节50-97求和取低8位）
        expected_checksum = HexFrameParser.checksum(data[49:97])
        actual_checksum = data[97]
        if expected_checksum != actual_checksum:
            logger.warning(f"INS 校验和错误: 期望 {expected_checksum:02x}, 实际 {actual_checksum:02x}")
            return None

        # INS 帧复用 GNSS 帧的时间戳
        year = struct.unpack('<H', data[3:5])[0]
        month = data[5]
        day = data[6]
        hour = data[7]
        minute = data[8]
        microsecond = struct.unpack('<I', data[9:13])[0]

        # 解析 IMU 数据（低字节序）
        gyro_x = struct.unpack('<d', data[49:57])[0]
        gyro_y = struct.unpack('<d', data[57:65])[0]
        gyro_z = struct.unpack('<d', data[65:73])[0]
        accel_x = struct.unpack('<d', data[73:81])[0]
        accel_y = struct.unpack('<d', data[81:89])[0]
        accel_z = struct.unpack('<d', data[89:97])[0]

        return IMUData(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            microsecond=microsecond,
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            accel_x=accel_x,
            accel_y=accel_y,
            accel_z=accel_z
        )

    @staticmethod
    def parse_file(file_path: str) -> Tuple[List[GNSSData], List[IMUData]]:
        """
        解析十六进制文件（ASCII hex 编码）
        返回 (gnss_list, imu_list)
        """
        gnss_list = []
        imu_list = []

        with open(file_path, 'r') as f:
            content = f.read().replace('\n', '').replace(' ', '')

        # 转成二进制
        try:
            binary_data = bytes.fromhex(content)
        except ValueError as e:
            logger.error(f"文件格式错误: {e}")
            return gnss_list, imu_list

        offset = 0
        while offset < len(binary_data):
            # 边界条件：文件尾部不足一帧
            if offset + 98 > len(binary_data):
                logger.debug(f"文件尾部不足一帧，剩余 {len(binary_data) - offset} 字节")
                break

            # 尝试解析 GNSS+INS 混合帧
            frame_data = binary_data[offset:offset + 98]

            gnss = HexFrameParser.parse_gnss_frame(frame_data)
            if gnss:
                gnss_list.append(gnss)

            ins = HexFrameParser.parse_ins_frame(frame_data)
            if ins:
                imu_list.append(ins)

            # 只有同时解析成功才前进，否则跳过1字节继续搜索
            if gnss and ins:
                offset += 98
            else:
                offset += 1

        return gnss_list, imu_list
