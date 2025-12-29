"""
数据可视化模块

提供各种图表生成函数，用于分析GNSS/IMU数据质量、时序对齐、插值效果等。
"""
import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple
from pathlib import Path

from ..models.data_types import GNSSData, IMUData

logger = logging.getLogger(__name__)

# 设置matplotlib中文支持（可选）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def plot_timestamp_alignment(
    gnss_list: List[GNSSData],
    imu_list: List[IMUData],
    output_path: Optional[str] = None,
    max_points: int = 10000
) -> None:
    """
    绘制GNSS和IMU时间戳对齐图

    Args:
        gnss_list: GNSS数据列表
        imu_list: IMU数据列表
        output_path: 输出文件路径（None则显示）
        max_points: 最大绘制点数（避免太密集）
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # 提取时间戳
    gnss_ts = np.array([g.timestamp for g in gnss_list])
    imu_ts = np.array([i.timestamp for i in imu_list])

    # 过滤NaN
    valid_gnss = ~np.isnan(gnss_ts)
    valid_imu = ~np.isnan(imu_ts)
    gnss_ts = gnss_ts[valid_gnss]
    imu_ts = imu_ts[valid_imu]

    # 采样（如果点太多）
    if len(gnss_ts) > max_points:
        gnss_indices = np.linspace(0, len(gnss_ts)-1, max_points, dtype=int)
        gnss_ts = gnss_ts[gnss_indices]

    if len(imu_ts) > max_points:
        imu_indices = np.linspace(0, len(imu_ts)-1, max_points, dtype=int)
        imu_ts = imu_ts[imu_indices]

    # 图1: 时间戳分布
    ax1.plot(range(len(gnss_ts)), gnss_ts, 'b.', markersize=2, label=f'GNSS ({len(gnss_list)} points, 1Hz)')
    ax1.plot(range(len(imu_ts)), imu_ts, 'r.', markersize=1, alpha=0.3, label=f'IMU ({len(imu_list)} points, ~95Hz)')
    ax1.set_xlabel('Data Index')
    ax1.set_ylabel('Unix Timestamp (s)')
    ax1.set_title('GNSS vs IMU Timestamp Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 图2: 时间戳间隔（频率检查）
    gnss_dt = np.diff(gnss_ts)
    imu_dt = np.diff(imu_ts)

    ax2.hist(gnss_dt, bins=50, alpha=0.7, label=f'GNSS Δt (mean={np.mean(gnss_dt):.3f}s)', color='blue')
    ax2.hist(imu_dt, bins=50, alpha=0.7, label=f'IMU Δt (mean={np.mean(imu_dt):.4f}s)', color='red')
    ax2.set_xlabel('Time Interval (s)')
    ax2.set_ylabel('Count')
    ax2.set_title('Timestamp Interval Distribution (Sampling Rate Check)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"时间戳对齐图已保存: {output_path}")
    else:
        plt.show()

    plt.close()


def plot_imu_data(
    imu_list: List[IMUData],
    output_path: Optional[str] = None,
    max_points: int = 10000,
    time_range: Optional[Tuple[float, float]] = None
) -> None:
    """
    绘制IMU数据曲线（陀螺仪+加速度计）

    Args:
        imu_list: IMU数据列表
        output_path: 输出文件路径
        max_points: 最大绘制点数
        time_range: 时间范围 (start_ts, end_ts)，None则全部
    """
    # 过滤时间范围
    if time_range:
        imu_list = [i for i in imu_list if time_range[0] <= i.timestamp <= time_range[1]]

    if len(imu_list) == 0:
        logger.warning("IMU数据为空，无法绘图")
        return

    # 采样
    if len(imu_list) > max_points:
        indices = np.linspace(0, len(imu_list)-1, max_points, dtype=int)
        imu_list = [imu_list[i] for i in indices]

    # 提取数据
    timestamps = np.array([i.timestamp for i in imu_list])
    gyro_x = np.array([i.gyro_x for i in imu_list])
    gyro_y = np.array([i.gyro_y for i in imu_list])
    gyro_z = np.array([i.gyro_z for i in imu_list])
    accel_x = np.array([i.accel_x for i in imu_list])
    accel_y = np.array([i.accel_y for i in imu_list])
    accel_z = np.array([i.accel_z for i in imu_list])

    # 转换为相对时间（秒）
    time_rel = timestamps - timestamps[0]

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # 陀螺仪
    ax_gyro = axes[0]
    ax_gyro.plot(time_rel, gyro_x, 'r-', linewidth=0.8, label='Gyro X', alpha=0.8)
    ax_gyro.plot(time_rel, gyro_y, 'g-', linewidth=0.8, label='Gyro Y', alpha=0.8)
    ax_gyro.plot(time_rel, gyro_z, 'b-', linewidth=0.8, label='Gyro Z', alpha=0.8)
    ax_gyro.set_xlabel('Time (s)')
    ax_gyro.set_ylabel('Angular Velocity (rad/s)')
    ax_gyro.set_title(f'IMU Gyroscope Data ({len(imu_list)} points)')
    ax_gyro.legend(loc='upper right')
    ax_gyro.grid(True, alpha=0.3)

    # 加速度计
    ax_accel = axes[1]
    ax_accel.plot(time_rel, accel_x, 'r-', linewidth=0.8, label='Accel X', alpha=0.8)
    ax_accel.plot(time_rel, accel_y, 'g-', linewidth=0.8, label='Accel Y', alpha=0.8)
    ax_accel.plot(time_rel, accel_z, 'b-', linewidth=0.8, label='Accel Z', alpha=0.8)
    ax_accel.set_xlabel('Time (s)')
    ax_accel.set_ylabel('Acceleration (m/s²)')
    ax_accel.set_title(f'IMU Accelerometer Data ({len(imu_list)} points)')
    ax_accel.legend(loc='upper right')
    ax_accel.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"IMU数据曲线已保存: {output_path}")
    else:
        plt.show()

    plt.close()


def plot_gnss_trajectory(
    gnss_list: List[GNSSData],
    output_path: Optional[str] = None,
    show_velocity: bool = False
) -> None:
    """
    绘制GNSS轨迹图（经纬度）

    Args:
        gnss_list: GNSS数据列表
        output_path: 输出文件路径
        show_velocity: 是否用颜色表示速度
    """
    if len(gnss_list) == 0:
        logger.warning("GNSS数据为空，无法绘图")
        return

    # 过滤NaN
    valid_gnss = [g for g in gnss_list if not np.isnan(g.timestamp)]

    if len(valid_gnss) == 0:
        logger.warning("没有有效的GNSS数据")
        return

    # 提取数据
    lons = np.array([g.longitude for g in valid_gnss])
    lats = np.array([g.latitude for g in valid_gnss])
    alts = np.array([g.altitude for g in valid_gnss])

    if show_velocity:
        speeds = np.array([np.sqrt(g.velocity_x**2 + g.velocity_y**2 + g.velocity_z**2)
                          for g in valid_gnss])

    fig = plt.figure(figsize=(14, 6))

    # 轨迹图（经纬度）
    ax1 = plt.subplot(1, 2, 1)
    if show_velocity:
        scatter = ax1.scatter(lons, lats, c=speeds, cmap='jet', s=10, alpha=0.6)
        plt.colorbar(scatter, ax=ax1, label='Speed (m/s)')
    else:
        ax1.plot(lons, lats, 'b-', linewidth=0.8, alpha=0.6)
        ax1.plot(lons[0], lats[0], 'go', markersize=8, label='Start')
        ax1.plot(lons[-1], lats[-1], 'ro', markersize=8, label='End')
        ax1.legend()

    ax1.set_xlabel('Longitude (°)')
    ax1.set_ylabel('Latitude (°)')
    ax1.set_title(f'GNSS Trajectory ({len(valid_gnss)} points)')
    ax1.grid(True, alpha=0.3)
    ax1.axis('equal')

    # 高度曲线
    ax2 = plt.subplot(1, 2, 2)
    ax2.plot(range(len(alts)), alts, 'b-', linewidth=0.8)
    ax2.set_xlabel('Data Index')
    ax2.set_ylabel('Altitude (m)')
    ax2.set_title(f'Altitude Profile (mean={np.mean(alts):.2f}m)')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"GNSS轨迹图已保存: {output_path}")
    else:
        plt.show()

    plt.close()


def plot_interpolation_comparison(
    original_gnss: List[GNSSData],
    interpolated_gnss: List[GNSSData],
    output_path: Optional[str] = None,
    field: str = 'longitude',
    max_points: int = 1000
) -> None:
    """
    绘制插值前后对比图

    Args:
        original_gnss: 原始GNSS数据（1Hz）
        interpolated_gnss: 插值后GNSS数据（95Hz）
        output_path: 输出文件路径
        field: 对比字段 ('longitude', 'latitude', 'altitude', 'velocity_x', etc.)
        max_points: 最大显示点数（原始数据）
    """
    # 过滤NaN
    valid_orig = [g for g in original_gnss if not np.isnan(g.timestamp)]
    valid_interp = [g for g in interpolated_gnss if not np.isnan(g.timestamp)]

    if len(valid_orig) == 0 or len(valid_interp) == 0:
        logger.warning("数据为空，无法绘图")
        return

    # 采样原始数据
    if len(valid_orig) > max_points:
        indices = np.linspace(0, len(valid_orig)-1, max_points, dtype=int)
        valid_orig = [valid_orig[i] for i in indices]

    # 提取时间戳和字段值
    orig_ts = np.array([g.timestamp for g in valid_orig])
    orig_val = np.array([getattr(g, field) for g in valid_orig])

    interp_ts = np.array([g.timestamp for g in valid_interp])
    interp_val = np.array([getattr(g, field) for g in valid_interp])

    # 转换为相对时间
    t0 = min(orig_ts.min(), interp_ts.min())
    orig_time = orig_ts - t0
    interp_time = interp_ts - t0

    # 只显示原始数据时间范围内的插值数据
    mask = (interp_time >= orig_time.min()) & (interp_time <= orig_time.max())
    interp_time = interp_time[mask]
    interp_val = interp_val[mask]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # 图1: 全局对比
    ax1.plot(interp_time, interp_val, 'b-', linewidth=0.5, alpha=0.5, label=f'Interpolated ({len(valid_interp)} pts, 95Hz)')
    ax1.plot(orig_time, orig_val, 'ro', markersize=4, label=f'Original ({len(valid_orig)} pts, 1Hz)')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel(field)
    ax1.set_title(f'Interpolation Comparison: {field}')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 图2: 局部放大（前100秒）
    zoom_duration = min(100, orig_time.max())
    zoom_mask_orig = orig_time <= zoom_duration
    zoom_mask_interp = interp_time <= zoom_duration

    ax2.plot(interp_time[zoom_mask_interp], interp_val[zoom_mask_interp],
             'b-', linewidth=0.8, alpha=0.6, label='Interpolated')
    ax2.plot(orig_time[zoom_mask_orig], orig_val[zoom_mask_orig],
             'ro', markersize=5, label='Original')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel(field)
    ax2.set_title(f'Zoomed View (first {zoom_duration:.0f}s)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"插值对比图已保存: {output_path}")
    else:
        plt.show()

    plt.close()
