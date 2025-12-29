"""
数据处理管线

整合解析、同步、插值、可视化等所有步骤。
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json

from ..parsers.hex_parser import HexFrameParser
from ..parsers.ins_parser import INSFrameParser
from ..parsers.result_text_parser import ResultTextParser
from ..sync.time_sync import TimestampConverter, TimeAlignment
from ..interpolation.gnss_interpolation import LinearInterpolator, CubicSplineInterpolator
from ..visualization.plots import (
    plot_timestamp_alignment,
    plot_imu_data,
    plot_gnss_trajectory,
    plot_interpolation_comparison
)
from ..models.data_types import GNSSData, IMUData, NavigationResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """管线配置"""
    # 输入文件
    gnss_file: str
    imu_file: str
    result_file: Optional[str] = None

    # 输出目录
    output_dir: str = "output"

    # 处理参数
    imu_frequency: float = 95.0  # IMU采样频率（Hz）
    interpolation_method: str = "linear"  # 'linear' or 'spline'
    interpolation_frequency: float = 95.0  # 插值目标频率（Hz）

    # 可视化参数
    generate_plots: bool = True
    plot_max_points: int = 10000
    plot_time_window: Optional[float] = 1000.0  # 秒，None=全部

    # 输出控制
    save_interpolated_gnss: bool = True  # 默认保存插值后的GNSS数据
    save_aligned_data: bool = True  # 默认保存对齐数据

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PipelineConfig':
        """从字典创建配置"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})

    @classmethod
    def from_json(cls, json_path: str) -> 'PipelineConfig':
        """从JSON文件加载配置"""
        with open(json_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def validate(self) -> None:
        """验证配置有效性"""
        if not Path(self.gnss_file).exists():
            raise FileNotFoundError(f"GNSS文件不存在: {self.gnss_file}")
        if not Path(self.imu_file).exists():
            raise FileNotFoundError(f"IMU文件不存在: {self.imu_file}")
        if self.result_file and not Path(self.result_file).exists():
            raise FileNotFoundError(f"解算结果文件不存在: {self.result_file}")

        if self.interpolation_method not in ['linear', 'spline']:
            raise ValueError(f"不支持的插值方法: {self.interpolation_method}")

        if self.imu_frequency <= 0 or self.interpolation_frequency <= 0:
            raise ValueError("频率必须为正数")


@dataclass
class PipelineResults:
    """管线输出结果"""
    gnss_data: List[GNSSData]
    imu_data: List[IMUData]
    interpolated_gnss: Optional[List[GNSSData]] = None
    navigation_results: Optional[List[NavigationResult]] = None
    alignment_report: Optional[Dict[str, Any]] = None
    output_dir: Optional[Path] = None


class DataPipeline:
    """数据处理管线"""

    def __init__(self, config: PipelineConfig):
        """
        初始化管线

        Args:
            config: 管线配置
        """
        self.config = config
        config.validate()

        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 中间结果
        self.gnss_data: Optional[List[GNSSData]] = None
        self.imu_data: Optional[List[IMUData]] = None
        self.interpolated_gnss: Optional[List[GNSSData]] = None
        self.navigation_results: Optional[List[NavigationResult]] = None

        logger.info(f"管线初始化完成，输出目录: {self.output_dir}")

    def run(self) -> PipelineResults:
        """
        运行完整管线

        Returns:
            处理结果
        """
        logger.info("=" * 60)
        logger.info("开始数据处理管线")
        logger.info("=" * 60)

        # 步骤1: 加载数据
        self._load_data()

        # 步骤2: 时序同步
        self._sync_timestamps()

        # 步骤3: GNSS插值
        self._interpolate_gnss()

        # 步骤4: 数据对齐与质量评估
        alignment_report = self._align_and_evaluate()

        # 步骤5: 生成可视化
        if self.config.generate_plots:
            self._generate_visualizations()

        # 步骤6: 保存结果
        self._save_results()

        logger.info("=" * 60)
        logger.info("管线执行完成")
        logger.info("=" * 60)

        return PipelineResults(
            gnss_data=self.gnss_data,
            imu_data=self.imu_data,
            interpolated_gnss=self.interpolated_gnss,
            navigation_results=self.navigation_results,
            alignment_report=alignment_report,
            output_dir=self.output_dir
        )

    def _load_data(self) -> None:
        """步骤1: 加载所有数据"""
        logger.info("\n[1/6] 加载数据...")

        # 加载GNSS
        logger.info(f"加载GNSS数据: {self.config.gnss_file}")
        self.gnss_data, _ = HexFrameParser.parse_file(self.config.gnss_file)
        logger.info(f"  GNSS数据: {len(self.gnss_data)} 条")

        # 加载IMU
        logger.info(f"加载IMU数据: {self.config.imu_file}")
        self.imu_data = INSFrameParser.parse_file(self.config.imu_file)
        logger.info(f"  IMU数据: {len(self.imu_data)} 条")

        # 加载解算结果（可选）
        if self.config.result_file:
            logger.info(f"加载解算结果: {self.config.result_file}")
            self.navigation_results = ResultTextParser.parse_file(self.config.result_file)
            logger.info(f"  解算结果: {len(self.navigation_results)} 条")

    def _sync_timestamps(self) -> None:
        """步骤2: 时序同步"""
        logger.info("\n[2/6] 时序同步...")

        # 为IMU设置时间戳
        start_ts = self.gnss_data[0].timestamp
        logger.info(f"为IMU设置时间戳（起始={start_ts:.3f}, 频率={self.config.imu_frequency}Hz）")
        TimestampConverter.convert_imu_data(
            self.imu_data,
            start_ts,
            frequency=self.config.imu_frequency
        )
        logger.info("  时间戳设置完成")

    def _interpolate_gnss(self) -> None:
        """步骤3: GNSS插值"""
        logger.info("\n[3/6] GNSS插值...")

        # 过滤有效GNSS数据
        import numpy as np
        valid_gnss = [g for g in self.gnss_data if not np.isnan(g.timestamp)]
        logger.info(f"有效GNSS数据: {len(valid_gnss)} 条")

        if len(valid_gnss) < 2:
            logger.warning("GNSS数据不足，跳过插值")
            return

        # 生成目标时间戳
        start_ts = valid_gnss[0].timestamp
        end_ts = valid_gnss[-1].timestamp
        duration = end_ts - start_ts
        num_points = int(duration * self.config.interpolation_frequency)

        target_timestamps = np.linspace(start_ts, end_ts, num_points)
        logger.info(f"插值目标: {num_points} 个点 ({self.config.interpolation_frequency} Hz)")

        # 选择插值方法
        if self.config.interpolation_method == 'linear':
            logger.info("使用线性插值")
            self.interpolated_gnss = LinearInterpolator.interpolate(
                valid_gnss,
                target_timestamps.tolist()
            )
        else:
            logger.info("使用三次样条插值")
            self.interpolated_gnss = CubicSplineInterpolator.interpolate(
                valid_gnss,
                target_timestamps.tolist()
            )

        logger.info(f"  插值完成: {len(self.interpolated_gnss)} 条数据")

    def _align_and_evaluate(self) -> Dict[str, Any]:
        """步骤4: 数据对齐与质量评估"""
        logger.info("\n[4/6] 数据对齐与质量评估...")

        # 使用插值后的GNSS（如果有）
        gnss_to_use = self.interpolated_gnss if self.interpolated_gnss else self.gnss_data

        # 对齐数据（只取前1000个IMU点做评估）
        sample_size = min(1000, len(self.imu_data))
        aligned_pairs = TimeAlignment.align_data(gnss_to_use, self.imu_data[:sample_size])

        # 生成质量报告
        report = TimeAlignment.validate_alignment(aligned_pairs)

        logger.info("对齐质量报告:")
        logger.info(f"  样本大小: {report['total_pairs']}")
        logger.info(f"  最大时间差: {report['max_time_diff']*1000:.2f} ms")
        logger.info(f"  平均时间差: {report['avg_time_diff']*1000:.2f} ms")
        logger.info(f"  5ms内对齐: {report['pairs_within_5ms']} ({report['pairs_within_5ms']/report['total_pairs']*100:.1f}%)")
        logger.info(f"  10ms内对齐: {report['pairs_within_10ms']} ({report['pairs_within_10ms']/report['total_pairs']*100:.1f}%)")

        return report

    def _generate_visualizations(self) -> None:
        """步骤5: 生成可视化"""
        logger.info("\n[5/6] 生成可视化...")

        plots_dir = self.output_dir / "plots"
        plots_dir.mkdir(exist_ok=True)

        # 1. 时间戳对齐图
        logger.info("生成时间戳对齐图...")
        plot_timestamp_alignment(
            self.gnss_data,
            self.imu_data,
            output_path=str(plots_dir / "timestamp_alignment.png"),
            max_points=self.config.plot_max_points
        )

        # 2. IMU数据曲线
        logger.info("生成IMU数据曲线...")
        time_range = None
        if self.config.plot_time_window:
            start = self.imu_data[0].timestamp
            time_range = (start, start + self.config.plot_time_window)

        plot_imu_data(
            self.imu_data,
            output_path=str(plots_dir / "imu_data.png"),
            max_points=self.config.plot_max_points,
            time_range=time_range
        )

        # 3. GNSS轨迹图
        logger.info("生成GNSS轨迹图...")
        plot_gnss_trajectory(
            self.gnss_data,
            output_path=str(plots_dir / "gnss_trajectory.png"),
            show_velocity=True
        )

        # 4. 插值对比图（如果有插值）
        if self.interpolated_gnss:
            logger.info("生成插值对比图...")
            for field in ['longitude', 'latitude', 'altitude']:
                plot_interpolation_comparison(
                    self.gnss_data[:1000],
                    self.interpolated_gnss,
                    output_path=str(plots_dir / f"interpolation_{field}.png"),
                    field=field,
                    max_points=500
                )

        logger.info(f"  图表已保存至: {plots_dir}")

    def _save_results(self) -> None:
        """步骤6: 保存处理结果"""
        logger.info("\n[6/6] 保存处理结果...")

        # 保存对齐后的数据为CSV
        if self.aligned_pairs:
            self._save_aligned_data_csv()

        # 保存插值后的GNSS数据为CSV
        if self.config.save_interpolated_gnss and self.interpolated_gnss:
            self._save_interpolated_gnss_csv()

        logger.info("结果保存完成")

    def _save_aligned_data_csv(self) -> None:
        """保存对齐后的GNSS-IMU配对数据为CSV"""
        import csv

        output_file = self.output_dir / "aligned_gnss_imu.csv"
        logger.info(f"保存对齐数据: {output_file}")

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入表头
            writer.writerow([
                'timestamp',
                'gnss_latitude', 'gnss_longitude', 'gnss_altitude',
                'gnss_vel_n', 'gnss_vel_e', 'gnss_vel_d',
                'imu_gyro_x', 'imu_gyro_y', 'imu_gyro_z',
                'imu_accel_x', 'imu_accel_y', 'imu_accel_z',
                'time_diff_ms'
            ])

            # 写入数据
            for (gnss, imu), time_diff in zip(self.aligned_pairs, self.time_diffs):
                writer.writerow([
                    gnss.timestamp,
                    gnss.latitude, gnss.longitude, gnss.altitude,
                    gnss.vel_n, gnss.vel_e, gnss.vel_d,
                    imu.gyro_x, imu.gyro_y, imu.gyro_z,
                    imu.accel_x, imu.accel_y, imu.accel_z,
                    time_diff * 1000  # 转换为毫秒
                ])

        logger.info(f"已保存 {len(self.aligned_pairs)} 条对齐数据")

    def _save_interpolated_gnss_csv(self) -> None:
        """保存插值后的GNSS数据为CSV"""
        import csv

        output_file = self.output_dir / "interpolated_gnss.csv"
        logger.info(f"保存插值GNSS数据: {output_file}")

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入表头
            writer.writerow([
                'timestamp',
                'year', 'month', 'day', 'hour', 'minute', 'microsecond',
                'latitude', 'longitude', 'altitude',
                'vel_n', 'vel_e', 'vel_d'
            ])

            # 写入数据
            for gnss in self.interpolated_gnss:
                writer.writerow([
                    gnss.timestamp,
                    gnss.year, gnss.month, gnss.day,
                    gnss.hour, gnss.minute, gnss.microsecond,
                    gnss.latitude, gnss.longitude, gnss.altitude,
                    gnss.vel_n, gnss.vel_e, gnss.vel_d
                ])

        logger.info(f"已保存 {len(self.interpolated_gnss)} 条插值GNSS数据")

