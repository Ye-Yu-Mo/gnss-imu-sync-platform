"""
解算结果解析器（附录2格式）
"""
import struct
from typing import List, Optional
from ..models.data_types import NavigationResult


class ResultParser:
    """解算结果解析器（附录2格式）"""

    # 附录2格式总长度：2+1+1+1+1+4+1+8*9+8*9+4 = 160字节
    FRAME_SIZE = 160

    @staticmethod
    def parse_frame(data: bytes) -> Optional[NavigationResult]:
        """
        解析导航结果帧（附录2格式）
        返回 NavigationResult 或 None（解析失败）
        """
        if len(data) < ResultParser.FRAME_SIZE:
            return None

        offset = 0

        # 解析时间戳
        year = struct.unpack('<H', data[offset:offset+2])[0]
        offset += 2
        month = data[offset]
        offset += 1
        day = data[offset]
        offset += 1
        hour = data[offset]
        offset += 1
        minute = data[offset]
        offset += 1
        microsecond = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4

        # 导航状态
        nav_status = struct.unpack('b', data[offset:offset+1])[0]
        offset += 1

        # 组合导航信息（9个double）
        combined_longitude = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_latitude = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_altitude = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_vel_x = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_vel_y = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_vel_z = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_roll = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_heading = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        combined_pitch = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8

        # 纯惯导信息（9个double）
        ins_longitude = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_latitude = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_altitude = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_vel_x = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_vel_y = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_vel_z = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_roll = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_heading = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ins_pitch = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8

        # 帧序号
        frame_index = struct.unpack('<i', data[offset:offset+4])[0]

        # 边界条件检查
        if year < 2000 or year > 2100:
            print(f"导航结果时间戳非法: 年份 {year}")
            return None

        if nav_status not in [0, 2, 3, 4]:
            print(f"导航状态异常: {nav_status}")
            # 不直接返回None，只告警

        return NavigationResult(
            timestamp=0.0,  # 后续统一计算
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            microsecond=microsecond,
            nav_status=nav_status,
            combined_longitude=combined_longitude,
            combined_latitude=combined_latitude,
            combined_altitude=combined_altitude,
            combined_vel_x=combined_vel_x,
            combined_vel_y=combined_vel_y,
            combined_vel_z=combined_vel_z,
            combined_roll=combined_roll,
            combined_heading=combined_heading,
            combined_pitch=combined_pitch,
            ins_longitude=ins_longitude,
            ins_latitude=ins_latitude,
            ins_altitude=ins_altitude,
            ins_vel_x=ins_vel_x,
            ins_vel_y=ins_vel_y,
            ins_vel_z=ins_vel_z,
            ins_roll=ins_roll,
            ins_heading=ins_heading,
            ins_pitch=ins_pitch,
            frame_index=frame_index
        )

    @staticmethod
    def parse_file(file_path: str) -> List[NavigationResult]:
        """
        解析导航结果文件（ASCII hex 编码 或 二进制）
        返回 NavigationResult 列表
        """
        results = []

        with open(file_path, 'rb') as f:
            content = f.read()

        # 尝试判断是 ASCII hex 还是二进制
        try:
            # 尝试作为 ASCII 读取
            content_str = content.decode('ascii').replace('\n', '').replace(' ', '')
            binary_data = bytes.fromhex(content_str)
        except (ValueError, UnicodeDecodeError):
            # 如果失败，直接作为二进制
            binary_data = content

        offset = 0
        while offset + ResultParser.FRAME_SIZE <= len(binary_data):
            frame_data = binary_data[offset:offset + ResultParser.FRAME_SIZE]
            result = ResultParser.parse_frame(frame_data)
            if result:
                results.append(result)
            offset += ResultParser.FRAME_SIZE

        if offset < len(binary_data):
            print(f"文件尾部剩余 {len(binary_data) - offset} 字节")

        return results
