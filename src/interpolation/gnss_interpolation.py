"""
GNSS 数据插值算法

将低频 GNSS 数据（1Hz）插值到高频（如95Hz），以匹配 IMU 采样率。
"""
import logging
import numpy as np
from typing import List
from scipy.interpolate import interp1d, CubicSpline
from ..models.data_types import GNSSData

logger = logging.getLogger(__name__)


class GNSSInterpolator:
    """GNSS 数据插值器基类"""

    @staticmethod
    def _validate_input(gnss_list: List[GNSSData], target_timestamps: np.ndarray):
        """验证输入数据"""
        if len(gnss_list) < 2:
            raise ValueError("GNSS数据至少需要2个点才能插值")

        gnss_timestamps = np.array([g.timestamp for g in gnss_list])

        # 检查是否有NaN timestamp
        if np.any(np.isnan(gnss_timestamps)):
            raise ValueError("GNSS数据中存在非法时间戳（NaN）")

        # 检查并处理时间戳顺序问题
        if not np.all(gnss_timestamps[:-1] <= gnss_timestamps[1:]):
            logger.warning("GNSS时间戳未严格递增，将排序并去重")
            # 这是警告，不修改数据，由调用方处理

        # 检查目标时间戳是否在GNSS范围内
        if np.any(target_timestamps < gnss_timestamps.min()) or \
           np.any(target_timestamps > gnss_timestamps.max()):
            logger.warning("部分目标时间戳超出GNSS时间范围，将外推（可能不准确）")

        return gnss_timestamps

    @staticmethod
    def _sort_and_deduplicate(gnss_list: List[GNSSData]) -> List[GNSSData]:
        """
        对GNSS数据按时间戳排序并去重

        如果存在重复时间戳，保留第一个
        """
        # 按timestamp排序
        sorted_gnss = sorted(gnss_list, key=lambda g: g.timestamp)

        # 去重：如果连续两个timestamp相同，跳过后者
        dedup_gnss = []
        prev_ts = None
        for g in sorted_gnss:
            if prev_ts is None or abs(g.timestamp - prev_ts) > 1e-9:  # 容忍1纳秒误差
                dedup_gnss.append(g)
                prev_ts = g.timestamp
            else:
                logger.debug(f"跳过重复时间戳: {g.timestamp}")

        if len(dedup_gnss) < len(sorted_gnss):
            logger.info(f"去除了 {len(sorted_gnss) - len(dedup_gnss)} 个重复时间戳")

        return dedup_gnss

    @staticmethod
    def _extract_fields(gnss_list: List[GNSSData]) -> dict:
        """提取GNSS各字段为numpy数组"""
        return {
            'longitude': np.array([g.longitude for g in gnss_list]),
            'latitude': np.array([g.latitude for g in gnss_list]),
            'altitude': np.array([g.altitude for g in gnss_list]),
            'velocity_x': np.array([g.velocity_x for g in gnss_list]),
            'velocity_y': np.array([g.velocity_y for g in gnss_list]),
            'velocity_z': np.array([g.velocity_z for g in gnss_list]),
        }


class LinearInterpolator(GNSSInterpolator):
    """线性插值器"""

    @staticmethod
    def interpolate(gnss_list: List[GNSSData],
                   target_timestamps: List[float]) -> List[GNSSData]:
        """
        对GNSS数据进行线性插值

        Args:
            gnss_list: 原始GNSS数据列表（低频，如1Hz）
            target_timestamps: 目标时间戳列表（高频，如95Hz）

        Returns:
            插值后的GNSS数据列表
        """
        # 排序并去重
        clean_gnss = LinearInterpolator._sort_and_deduplicate(gnss_list)

        target_ts = np.array(target_timestamps)
        gnss_ts = LinearInterpolator._validate_input(clean_gnss, target_ts)
        fields = LinearInterpolator._extract_fields(clean_gnss)

        # 对每个字段进行线性插值
        interp_results = {}
        for field_name, field_values in fields.items():
            f = interp1d(gnss_ts, field_values, kind='linear',
                        fill_value='extrapolate')
            interp_results[field_name] = f(target_ts)

        # 构造插值后的GNSSData对象
        interpolated_gnss = []
        for i, ts in enumerate(target_ts):
            # 从timestamp反推时间字段（简化处理，实际应该更精确）
            # 这里使用第一个GNSS的日期，只更新时间
            base_gnss = gnss_list[0]

            gnss = GNSSData(
                year=base_gnss.year,
                month=base_gnss.month,
                day=base_gnss.day,
                hour=base_gnss.hour,
                minute=base_gnss.minute,
                microsecond=base_gnss.microsecond,
                longitude=interp_results['longitude'][i],
                latitude=interp_results['latitude'][i],
                altitude=interp_results['altitude'][i],
                velocity_x=interp_results['velocity_x'][i],
                velocity_y=interp_results['velocity_y'][i],
                velocity_z=interp_results['velocity_z'][i],
                valid=True
            )
            # 直接设置正确的timestamp
            object.__setattr__(gnss, 'timestamp', ts)
            interpolated_gnss.append(gnss)

        return interpolated_gnss


class CubicSplineInterpolator(GNSSInterpolator):
    """三次样条插值器"""

    @staticmethod
    def interpolate(gnss_list: List[GNSSData],
                   target_timestamps: List[float],
                   bc_type='natural') -> List[GNSSData]:
        """
        对GNSS数据进行三次样条插值

        Args:
            gnss_list: 原始GNSS数据列表
            target_timestamps: 目标时间戳列表
            bc_type: 边界条件类型 ('natural', 'clamped', 'not-a-knot')

        Returns:
            插值后的GNSS数据列表
        """
        # 排序并去重
        clean_gnss = CubicSplineInterpolator._sort_and_deduplicate(gnss_list)

        target_ts = np.array(target_timestamps)
        gnss_ts = CubicSplineInterpolator._validate_input(clean_gnss, target_ts)
        fields = CubicSplineInterpolator._extract_fields(clean_gnss)

        # 对每个字段进行三次样条插值
        interp_results = {}
        for field_name, field_values in fields.items():
            cs = CubicSpline(gnss_ts, field_values, bc_type=bc_type)
            interp_results[field_name] = cs(target_ts)

        # 构造插值后的GNSSData对象
        interpolated_gnss = []
        for i, ts in enumerate(target_ts):
            base_gnss = gnss_list[0]

            gnss = GNSSData(
                year=base_gnss.year,
                month=base_gnss.month,
                day=base_gnss.day,
                hour=base_gnss.hour,
                minute=base_gnss.minute,
                microsecond=base_gnss.microsecond,
                longitude=interp_results['longitude'][i],
                latitude=interp_results['latitude'][i],
                altitude=interp_results['altitude'][i],
                velocity_x=interp_results['velocity_x'][i],
                velocity_y=interp_results['velocity_y'][i],
                velocity_z=interp_results['velocity_z'][i],
                valid=True
            )
            object.__setattr__(gnss, 'timestamp', ts)
            interpolated_gnss.append(gnss)

        return interpolated_gnss
