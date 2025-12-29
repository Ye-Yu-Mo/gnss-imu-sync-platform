"""
时序同步模块：时间戳转换与数据对齐
"""
from datetime import datetime
from typing import List, Tuple
import bisect
from ..models.data_types import GNSSData, IMUData


class TimestampConverter:
    """时间戳统一转换器"""

    @staticmethod
    def convert_imu_data(imu_list: List[IMUData],
                        start_timestamp: float,
                        frequency: float = 95.0) -> List[IMUData]:
        """
        为IMU数据设置时间戳

        由于INS帧没有时间戳，根据采样频率生成时间戳并更新IMU对象。

        Args:
            imu_list: IMU数据列表（解析后的，时间戳为epoch）
            start_timestamp: 起始Unix时间戳（秒）
            frequency: 采样频率（Hz）
        """
        dt = 1.0 / frequency
        start_dt = datetime.fromtimestamp(start_timestamp)

        for i, imu in enumerate(imu_list):
            current_timestamp = start_timestamp + i * dt
            current_dt = datetime.fromtimestamp(current_timestamp)

            # 更新时间字段
            imu.year = current_dt.year
            imu.month = current_dt.month
            imu.day = current_dt.day
            imu.hour = current_dt.hour
            imu.minute = current_dt.minute
            imu.microsecond = current_dt.microsecond

            # 直接设置timestamp（绕过__post_init__）
            object.__setattr__(imu, 'timestamp', current_timestamp)

        return imu_list


class TimeAlignment:
    """时序对齐算法"""

    @staticmethod
    def find_nearest_gnss(imu_timestamp: float,
                         gnss_timestamps: List[float]) -> Tuple[int, float]:
        """
        为IMU时间戳找到最近的GNSS时间戳

        Args:
            imu_timestamp: IMU时间戳
            gnss_timestamps: GNSS时间戳列表（已排序）

        Returns:
            (index, time_diff): 最近GNSS的索引和时间差
        """
        # 使用二分查找
        idx = bisect.bisect_left(gnss_timestamps, imu_timestamp)

        if idx == 0:
            return 0, abs(gnss_timestamps[0] - imu_timestamp)
        elif idx == len(gnss_timestamps):
            return len(gnss_timestamps) - 1, abs(gnss_timestamps[-1] - imu_timestamp)

        # 比较左右两个点，选择更近的
        left_diff = abs(gnss_timestamps[idx - 1] - imu_timestamp)
        right_diff = abs(gnss_timestamps[idx] - imu_timestamp)

        if left_diff < right_diff:
            return idx - 1, left_diff
        else:
            return idx, right_diff

    @staticmethod
    def align_data(gnss_list: List[GNSSData],
                   imu_list: List[IMUData]) -> List[Tuple[GNSSData, IMUData, float]]:
        """
        对齐GNSS和IMU数据

        Returns:
            List of (gnss, imu, time_diff): 对齐后的数据对和时间差
        """
        # 提取GNSS时间戳
        gnss_timestamps = [gnss.timestamp for gnss in gnss_list]

        aligned_pairs = []
        for imu in imu_list:
            idx, time_diff = TimeAlignment.find_nearest_gnss(imu.timestamp, gnss_timestamps)
            aligned_pairs.append((gnss_list[idx], imu, time_diff))

        return aligned_pairs

    @staticmethod
    def validate_alignment(aligned_pairs: List[Tuple[GNSSData, IMUData, float]]) -> dict:
        """
        验证对齐质量

        Returns:
            质量报告字典
        """
        time_diffs = [time_diff for _, _, time_diff in aligned_pairs]

        return {
            'total_pairs': len(aligned_pairs),
            'max_time_diff': max(time_diffs),
            'min_time_diff': min(time_diffs),
            'avg_time_diff': sum(time_diffs) / len(time_diffs),
            'pairs_within_5ms': sum(1 for d in time_diffs if d < 0.005),
            'pairs_within_10ms': sum(1 for d in time_diffs if d < 0.01),
        }
