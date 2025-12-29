# GNSS/IMU 原始数据读写与时序同步处理平台

## 项目简介

开发一个健壮的数据预处理模块，负责读取异构的 GNSS 和 IMU 日志文件，解决传感器间时序对齐问题，并实现基础的数学插值方法来生成高频的 GNSS 观测数据，为后续的组合导航融合算法提供同步、统一的数据接口。

**核心功能**
- GNSS/IMU 数据文件读取与解析
- 时序同步算法（时戳对齐、漂移检测）
- GNSS 数据插值（线性/样条/多项式）
- 数据可视化与验证
- Web 前端界面（数据上传、解析、图表展示）

## 项目结构

```
gnss-imu-sync-platform/
├── src/
│   ├── parsers/           # 数据解析器
│   │   ├── hex_parser.py          # 十六进制 GNSS 数据解析
│   │   ├── result_parser.py       # 二进制解算结果解析
│   │   └── result_text_parser.py  # 文本解算结果解析
│   ├── models/
│   │   └── data_types.py          # 数据结构定义
│   └── __init__.py
├── data/                  # 数据文件
│   ├── DATA_FORMAT.md             # 数据格式详细说明
│   ├── 3_NavigationResultGNSS.dat # GNSS 数据 (29,831 条)
│   ├── 3_NavigationResult_txt.dat # 解算结果文本 (2.8M 条)
│   └── ...
├── tests/                 # 测试脚本
├── features.json          # 需求文档
├── pyproject.toml         # 项目配置 (uv)
└── README.md
```

## 快速开始

### 环境要求

- Python >= 3.11
- uv (包管理器)

### 安装依赖

```bash
# 安装项目依赖
uv sync

# 安装 Web 相关依赖（可选）
uv sync --extra web

# 安装开发工具（可选）
uv sync --extra dev
```

### 运行示例

```bash
# 数据文件汇总分析
uv run data_summary.py

# 测试 GNSS 数据解析
uv run test_hex_parser.py

# 测试解算结果解析
uv run test_result_text_parser.py
```

## 当前进度

**F1 - 数据读取模块** [已完成]
- [x] F1.1 十六进制 GNSS 数据解析器（附录1 GNSS帧）
- [x] F1.2 十六进制 IMU 数据解析器（附录1 INS帧）
- [x] F1.3 解算结果解析器（附录2格式）
- [x] F1.4 统一数据结构设计
- [x] 边界条件处理（校验和、时戳验证、文件尾处理）

**数据统计**
- GNSS 数据: 29,831 条 (1 Hz)
- IMU 数据: 2,832,350 条 (约 95 Hz)
- 解算结果: 2,833,904 条 (约 200 Hz)

**F2 - 时序同步算法** [进行中]
- 时戳统一转换
- 最邻近搜索算法
- 时戳漂移检测

**F3 - GNSS 插值** [待开始]
- 线性插值
- 三次样条插值
- 高频伪观测量生成

**F4 - 数据可视化** [待开始]
- 时戳对比图
- IMU 数据曲线
- GNSS 轨迹可视化

**F5 - 平台整合** [待开始]
- 数据处理管线
- 统一 API 接口
- 配置管理

**F6 - Web 前端** [计划中]
- 后端 REST API
- 前端界面
- 图表集成

## 数据说明

详见 [`data/DATA_FORMAT.md`](data/DATA_FORMAT.md)

**可用数据**
- GNSS 数据: 29,831 条 (1 Hz, 经纬高+速度)
- IMU 原始数据: 2,832,350 条 (约 95 Hz, 陀螺仪+加速度计)
- 解算结果: 2,833,904 条 (约 200 Hz, 组合导航+纯惯导)
- NMEA 导航输出: com15.txt (1 Hz) / com16.txt (10 Hz)

## 技术栈

- **语言**: Python 3.11+
- **包管理**: uv
- **数值计算**: NumPy, SciPy
- **可视化**: Matplotlib
- **数据处理**: Pandas
- **Web 后端** (计划): FastAPI
- **Web 前端** (计划): React + ECharts

---

## 开发规范

- 使用 `uv` 管理依赖
- 代码格式化: `black`
- 代码检查: `ruff`
- 测试框架: `pytest`
