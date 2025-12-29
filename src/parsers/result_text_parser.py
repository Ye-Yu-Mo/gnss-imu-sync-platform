"""
解算结果文本解析器（附录2文本格式）
"""
import logging
from typing import List
from ..models.data_types import NavigationResult

logger = logging.getLogger(__name__)


class ResultTextParser:
    """解算结果文本解析器"""

    @staticmethod
    def parse_file(file_path: str) -> List[NavigationResult]:
        """
        解析导航结果文本文件
        格式：年 月 日 时 分 微秒 导航状态 组合导航(9值) 纯惯导(9值) 帧序号
        """
        results = []

        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) != 26:
                    logger.warning(f"第{line_num}行格式错误，字段数={len(parts)}，跳过")
                    continue

                try:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    hour = int(parts[3])
                    minute = int(parts[4])
                    microsecond = int(parts[5])
                    nav_status = int(parts[6])

                    # 组合导航信息
                    combined_longitude = float(parts[7])
                    combined_latitude = float(parts[8])
                    combined_altitude = float(parts[9])
                    combined_vel_x = float(parts[10])
                    combined_vel_y = float(parts[11])
                    combined_vel_z = float(parts[12])
                    combined_roll = float(parts[13])
                    combined_heading = float(parts[14])
                    combined_pitch = float(parts[15])

                    # 纯惯导信息
                    ins_longitude = float(parts[16])
                    ins_latitude = float(parts[17])
                    ins_altitude = float(parts[18])
                    ins_vel_x = float(parts[19])
                    ins_vel_y = float(parts[20])
                    ins_vel_z = float(parts[21])
                    ins_roll = float(parts[22])
                    ins_heading = float(parts[23])
                    ins_pitch = float(parts[24])

                    frame_index = int(parts[25])

                    result = NavigationResult(
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
                    results.append(result)

                except (ValueError, IndexError) as e:
                    logger.warning(f"第{line_num}行解析错误: {e}")
                    continue

        return results
