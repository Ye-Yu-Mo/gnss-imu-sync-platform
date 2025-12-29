#!/usr/bin/env python3
"""
GNSS/IMU数据处理管线 - 命令行工具
"""
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.data_pipeline import DataPipeline, PipelineConfig


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='GNSS/IMU数据处理管线',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用配置文件
  %(prog)s --config config.json

  # 直接指定文件
  %(prog)s \\
    --gnss data/3_NavigationResultGNSS.dat \\
    --imu data/3_NavigationResult.dat \\
    --output output

  # 指定插值参数
  %(prog)s \\
    --gnss data/3_NavigationResultGNSS.dat \\
    --imu data/3_NavigationResult.dat \\
    --interpolation spline \\
    --frequency 95
        """
    )

    # 配置文件
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件路径（JSON格式）'
    )

    # 输入文件
    parser.add_argument(
        '--gnss',
        type=str,
        help='GNSS数据文件路径'
    )
    parser.add_argument(
        '--imu',
        type=str,
        help='IMU数据文件路径'
    )
    parser.add_argument(
        '--result',
        type=str,
        help='解算结果文件路径（可选）'
    )

    # 输出目录
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='output',
        help='输出目录（默认: output）'
    )

    # 处理参数
    parser.add_argument(
        '--imu-freq',
        type=float,
        default=95.0,
        help='IMU采样频率（Hz，默认: 95）'
    )
    parser.add_argument(
        '--interpolation',
        choices=['linear', 'spline'],
        default='linear',
        help='插值方法（默认: linear）'
    )
    parser.add_argument(
        '--frequency',
        type=float,
        default=95.0,
        help='插值目标频率（Hz，默认: 95）'
    )

    # 可视化控制
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='不生成可视化图表'
    )
    parser.add_argument(
        '--plot-window',
        type=float,
        default=1000.0,
        help='可视化时间窗口（秒，默认: 1000）'
    )

    # 其他选项
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.verbose)

    # 创建配置
    if args.config:
        # 从配置文件加载
        logging.info(f"从配置文件加载: {args.config}")
        config = PipelineConfig.from_json(args.config)
    else:
        # 从命令行参数创建
        if not args.gnss or not args.imu:
            parser.error("必须指定 --gnss 和 --imu，或使用 --config")

        config = PipelineConfig(
            gnss_file=args.gnss,
            imu_file=args.imu,
            result_file=args.result,
            output_dir=args.output,
            imu_frequency=args.imu_freq,
            interpolation_method=args.interpolation,
            interpolation_frequency=args.frequency,
            generate_plots=not args.no_plots,
            plot_time_window=args.plot_window
        )

    # 创建并运行管线
    try:
        pipeline = DataPipeline(config)
        results = pipeline.run()

        print("\n" + "=" * 60)
        print("处理完成！")
        print("=" * 60)
        print(f"\n输出目录: {results.output_dir.absolute()}")
        print(f"GNSS数据: {len(results.gnss_data)} 条")
        print(f"IMU数据: {len(results.imu_data)} 条")
        if results.interpolated_gnss:
            print(f"插值后GNSS: {len(results.interpolated_gnss)} 条")
        if results.alignment_report:
            print(f"\n对齐质量:")
            print(f"  平均时间差: {results.alignment_report['avg_time_diff']*1000:.2f} ms")

    except Exception as e:
        logging.error(f"管线执行失败: {e}")
        if args.verbose:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
