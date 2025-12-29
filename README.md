# GNSS/IMU 原始数据读写与时序同步处理平台

## 项目简介

健壮的数据预处理平台，解决GNSS和IMU异构传感器的时序对齐问题，通过插值算法生成高频GNSS观测数据，为组合导航融合算法提供同步、统一的数据接口。

**核心功能**
- ✅ GNSS/IMU数据解析（十六进制+文本格式）
- ✅ 时序同步算法（二分查找优化）
- ✅ GNSS插值（线性/三次样条）
- ✅ 数据可视化（时间戳对齐、轨迹、传感器曲线）
- ✅ 完整处理管线（一键处理）
- ✅ Web前端界面（异步API+实时监控）

## 项目结构

```
gnss-imu-sync-platform/
├── src/
│   ├── parsers/           # 数据解析器
│   │   ├── hex_parser.py
│   │   ├── ins_parser.py
│   │   └── result_text_parser.py
│   ├── models/            # 数据结构
│   │   └── data_types.py
│   ├── sync/              # 时序同步
│   │   └── time_sync.py
│   ├── interpolation/     # 插值算法
│   │   └── gnss_interpolation.py
│   ├── visualization/     # 可视化
│   │   └── plots.py
│   └── pipeline/          # 数据管线
│       └── data_pipeline.py
├── data/                  # 数据文件
├── tests/                 # 测试脚本
├── examples/              # 示例脚本
├── run_pipeline.py        # 命令行工具
├── config.json            # 配置示例
└── pyproject.toml         # 项目配置
```

## 快速开始

**详细使用文档**: 见 [`USAGE.md`](USAGE.md)

### 1. 安装依赖

```bash
# 安装项目依赖
uv sync
```

### 2. 运行完整管线

**方式1：使用配置文件**
```bash
uv run python run_pipeline.py --config config.json
```

**方式2：命令行参数**
```bash
uv run python run_pipeline.py \
  --gnss data/3_NavigationResultGNSS.dat \
  --imu data/3_NavigationResult.dat \
  --output output \
  --interpolation linear \
  --frequency 95
```

**方式3：Python API**
```python
from src.pipeline.data_pipeline import DataPipeline, PipelineConfig

config = PipelineConfig(
    gnss_file="data/3_NavigationResultGNSS.dat",
    imu_file="data/3_NavigationResult.dat",
    output_dir="output"
)
pipeline = DataPipeline(config)
results = pipeline.run()

# 查看结果
print(f"对齐精度: {results.alignment_report['avg_time_diff']*1000:.2f} ms")
```

### 3. 查看结果

管线输出包括：
```
output/
├── plots/
│   ├── timestamp_alignment.png  # 时间戳对齐分析
│   ├── imu_data.png             # IMU传感器数据
│   ├── gnss_trajectory.png      # GNSS轨迹
│   └── interpolation_*.png      # 插值效果对比
└── ...
```

### 4. Web界面

**启动Web服务**：
```bash
# 安装Web依赖
uv sync --extra web

# 启动服务器
python run_web.py
```

**访问地址**：
- **Web界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs

**使用流程**：
1. 上传GNSS和IMU数据文件
2. 配置处理参数（频率、插值方法等）
3. 启动处理并实时监控进度
4. 查看对齐质量报告和可视化图表

## 核心功能

### 数据解析
支持三种数据格式：
- **GNSS数据**: 十六进制帧格式（46字节，1Hz）
- **IMU数据**: 十六进制帧格式（52字节，95Hz）
- **解算结果**: 文本格式（26字段，200Hz）

### 时序同步
- 自动为IMU数据设置时间戳（基于采样频率）
- 最邻近搜索算法（二分查找优化）
- 对齐质量报告（时间差统计）

### GNSS插值
- **线性插值**: 简单快速，适合实时处理
- **三次样条插值**: 平滑无震荡，高精度
- 从1Hz插值到95Hz，完美匹配IMU频率

### 数据可视化
- 时间戳分布与对齐分析
- IMU 6轴传感器数据（陀螺仪+加速度计）
- GNSS轨迹与高度剖面
- 插值前后效果对比

## 处理效果

| 指标 | 插值前 | 插值后 | 提升 |
|------|--------|--------|------|
| 平均时间差 | 468 ms | 0.01 ms | **46,800倍** |
| 5ms内对齐率 | 0.6% | 100% | **167倍** |
| 10ms内对齐率 | 1.0% | 100% | **100倍** |

**结论**: 插值将对齐精度从毫秒级提升到微秒级。

## 开发进度

**F1 - 数据读取模块** [✅ 已完成]
- GNSS/IMU/解算结果数据解析器
- 统一数据结构设计
- 完整测试覆盖

**F2 - 时序同步算法** [✅ 已完成]
- 时间戳统一转换
- 数据对齐算法（二分查找优化）
- 对齐质量验证

**F3 - GNSS插值** [✅ 已完成]
- 线性插值
- 三次样条插值
- 高频伪观测量生成（1Hz → 95Hz）

**F4 - 数据可视化** [✅ 已完成]
- 时间戳对齐图
- IMU数据曲线
- GNSS轨迹可视化
- 插值效果对比

**F5 - 平台整合** [✅ 已完成]
- 完整数据处理管线
- 配置文件支持
- 命令行工具
- Python API

**F6 - Web前端** [✅ 已完成]
- FastAPI异步后端
- Bootstrap响应式界面
- 文件上传与在线处理
- 实时状态监控与图表展示

## 数据说明

详见 [`data/DATA_FORMAT.md`](data/DATA_FORMAT.md)

**可用数据**
- GNSS 数据: 29,831 条 (1 Hz, 经纬高+速度)
- IMU 原始数据: 2,832,350 条 (约 95 Hz, 陀螺仪+加速度计)
- 解算结果: 2,833,904 条 (约 200 Hz, 组合导航+纯惯导)

## 技术栈

- **语言**: Python 3.11+
- **包管理**: uv
- **数值计算**: NumPy, SciPy
- **可视化**: Matplotlib
- **Web后端**: FastAPI, Uvicorn
- **Web前端**: HTML5, Bootstrap 5, Vanilla JS

## 开发规范

- 使用 `uv` 管理依赖
- 代码格式化: `black`
- 代码检查: `ruff`
- 测试框架: `pytest`

---

**详细进度**: 见 [`Status.md`](Status.md)
