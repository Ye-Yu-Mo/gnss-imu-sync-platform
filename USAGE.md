# 使用文档

## 5分钟快速上手

```bash
# 1. 安装依赖
uv sync

# 2. 运行管线（使用示例数据）
uv run python run_pipeline.py \
  --gnss data/3_NavigationResultGNSS.dat \
  --imu data/3_NavigationResult.dat \
  --output output

# 3. 查看结果
open output/plots/timestamp_alignment.png
```

完成。你会得到：
- 同步后的GNSS/IMU数据
- 1Hz→95Hz的GNSS插值数据
- 对齐质量报告（时间差0.01ms）
- 6张可视化图表

---

## 命令行使用

### 方式1：配置文件（推荐）

**创建配置** `my_config.json`：
```json
{
  "gnss_file": "data/3_NavigationResultGNSS.dat",
  "imu_file": "data/3_NavigationResult.dat",
  "result_file": "data/3_NavigationResult_txt.dat",
  "output_dir": "output",
  "imu_frequency": 95.0,
  "interpolation_method": "linear",
  "interpolation_frequency": 95.0,
  "generate_plots": true
}
```

**运行**：
```bash
uv run python run_pipeline.py --config my_config.json
```

### 方式2：命令行参数

```bash
uv run python run_pipeline.py \
  --gnss <GNSS文件路径> \
  --imu <IMU文件路径> \
  --output <输出目录> \
  --interpolation linear \     # 或 spline
  --frequency 95 \              # IMU采样频率
  --plots                       # 生成图表
```

**完整参数列表**：
```bash
--gnss PATH           # GNSS数据文件（必需）
--imu PATH            # IMU数据文件（必需）
--result PATH         # 解算结果文件（可选）
--output DIR          # 输出目录（默认：output）
--interpolation TYPE  # 插值方法：linear/spline（默认：linear）
--frequency HZ        # IMU频率（默认：95.0）
--interp-freq HZ      # 插值目标频率（默认：95.0）
--plots               # 生成可视化图表（默认：开启）
--no-plots            # 不生成图表
```

### 方式3：Python API

```python
from src.pipeline.data_pipeline import DataPipeline, PipelineConfig

# 创建配置
config = PipelineConfig(
    gnss_file="data/3_NavigationResultGNSS.dat",
    imu_file="data/3_NavigationResult.dat",
    output_dir="output",
    imu_frequency=95.0,
    interpolation_method="linear",  # 或 "spline"
    generate_plots=True
)

# 运行管线
pipeline = DataPipeline(config)
results = pipeline.run()

# 查看结果
print(f"GNSS数据: {len(results.gnss_data)} 条")
print(f"IMU数据: {len(results.imu_data)} 条")
print(f"插值后: {len(results.interpolated_gnss)} 条")
print(f"平均时间差: {results.alignment_report['avg_time_diff']*1000:.3f} ms")
print(f"5ms内对齐率: {results.alignment_report['pairs_within_5ms']/results.alignment_report['total_pairs']*100:.1f}%")
```

---

## Web界面使用

### 启动服务

```bash
# 安装Web依赖
uv sync --extra web

# 启动服务器
python run_web.py
```

服务器启动后访问：
- **Web界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs

### 使用流程

**步骤1：上传文件**
- GNSS数据文件（必需）
- IMU数据文件（必需）
- 解算结果文件（可选）

**步骤2：配置参数**
- IMU采样频率（默认95Hz）
- 插值方法（线性/三次样条）
- 插值目标频率（默认95Hz）
- 是否生成图表

**步骤3：启动处理**
- 点击"开始处理"
- 实时监控状态（2秒轮询）
- 等待处理完成（约17秒）

**步骤4：查看结果**
- 数据统计（GNSS/IMU/插值数据量）
- 对齐质量报告（时间差、对齐率）
- 可视化图表（6张PNG）

### API端点

如果你想自己写客户端：

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /api/upload | 上传文件，返回job_id |
| POST | /api/process/{job_id} | 启动处理 |
| GET | /api/status/{job_id} | 查询状态 |
| GET | /api/results/{job_id} | 获取结果 |
| GET | /api/plots/{job_id}/{filename} | 下载图表 |
| GET | /api/jobs | 列出所有任务 |
| DELETE | /api/jobs/{job_id} | 删除任务 |

**示例** (curl)：
```bash
# 上传文件
curl -X POST http://localhost:8000/api/upload \
  -F "gnss_file=@data/3_NavigationResultGNSS.dat" \
  -F "imu_file=@data/3_NavigationResult.dat"

# 返回：{"job_id": "xxx-xxx-xxx", "status": "uploaded"}

# 启动处理
curl -X POST http://localhost:8000/api/process/xxx-xxx-xxx \
  -F "imu_frequency=95" \
  -F "interpolation_method=linear" \
  -F "generate_plots=true"

# 查询状态
curl http://localhost:8000/api/status/xxx-xxx-xxx

# 获取结果
curl http://localhost:8000/api/results/xxx-xxx-xxx
```

---

## 数据格式要求

### GNSS数据（必需）

- **格式**: 十六进制二进制文件
- **帧结构**: 46字节/帧
- **帧头**: 0x9966
- **内容**: 时间戳 + 经纬高 + 三轴速度
- **频率**: 约1Hz
- **示例**: `data/3_NavigationResultGNSS.dat`

详见 `data/DATA_FORMAT.md` 附录1 GNSS帧格式。

### IMU数据（必需）

- **格式**: 十六进制二进制文件
- **帧结构**: 52字节/帧
- **帧头**: 0x55aa
- **内容**: 三轴陀螺仪 + 三轴加速度计（无时间戳）
- **频率**: 约95Hz
- **示例**: `data/3_NavigationResult.dat`

**重要**: IMU帧没有时间戳，系统会根据GNSS起始时间和IMU频率自动生成。

详见 `data/DATA_FORMAT.md` 附录1 INS帧格式。

### 解算结果（可选）

- **格式**: 文本文件
- **字段**: 26个空格分隔
- **内容**: 时间 + 组合导航 + 纯惯导
- **频率**: 约200Hz
- **示例**: `data/3_NavigationResult_txt.dat`

详见 `data/DATA_FORMAT.md` 附录2。

---

## 配置说明

### 插值方法选择

**linear（线性插值）**
- 优点：速度快，实时性好
- 缺点：分段线性，不够平滑
- 适用：实时系统、快速验证

**spline（三次样条插值）**
- 优点：平滑无震荡，高精度
- 缺点：计算量大（约慢2-3倍）
- 适用：离线分析、高精度需求

**精度对比**：
- 经纬度误差：< 1e-8° (亚毫米级)
- 高度误差：< 0.003m
- 两者差异极小，通常用linear即可

### IMU频率设置

必须设置正确的IMU采样频率，否则时间戳计算错误。

**检查方法**：
```python
from src.parsers.ins_parser import parse_ins_file
imu_data = parse_ins_file("data/3_NavigationResult.dat")
print(f"IMU数据量: {len(imu_data)}")
# 用文件时长估算频率
```

示例数据的IMU频率约为95Hz。

### 插值目标频率

通常设为IMU频率，确保GNSS和IMU时间戳对齐。

可以设为其他值（如200Hz），但对齐质量可能下降。

### 输出目录结构

```
output/
├── plots/                          # 可视化图表
│   ├── timestamp_alignment.png    # 时间戳对齐分析
│   ├── imu_data.png                # IMU传感器数据
│   ├── gnss_trajectory.png         # GNSS轨迹
│   ├── interpolation_longitude.png # 经度插值对比
│   ├── interpolation_latitude.png  # 纬度插值对比
│   └── interpolation_altitude.png  # 高度插值对比
└── ...
```

Web模式：
```
uploads/{job_id}/           # 上传的文件
output/web_results/{job_id}/  # 处理结果
```

---

## 常见问题

### Q: 处理失败，提示"month must be in 1..12"

**原因**: 数据中存在非法时间字段（月份不在1-12范围）。

**解决**: 系统会自动将非法时间戳设为NaN，不影响处理。如果大量数据非法，检查数据源。

### Q: 插值后对齐效果不好

**检查**：
1. IMU频率设置是否正确？
2. 插值目标频率是否等于IMU频率？
3. GNSS和IMU时间范围是否重叠？

**正常指标**：
- 平均时间差：< 0.1ms
- 5ms内对齐率：> 99%

### Q: 图表显示数据点很少

**原因**: 自动采样机制，避免图表过密。

**解决**: 不影响处理结果，仅影响显示。如需查看原始数据，使用Python API直接访问。

### Q: Web界面卡在"处理中"

**排查**：
1. 检查终端日志，是否有错误信息
2. 访问 http://localhost:8000/api/status/{job_id} 查看状态
3. 检查文件是否过大（建议<500MB）

**超时设置**: 默认最多等待120秒，可在 `tests/test_web_api.py` 修改。

### Q: 如何使用自己的数据？

**步骤**：
1. 确认数据格式符合要求（见"数据格式要求"）
2. 测量实际IMU频率
3. 修改配置文件或命令行参数
4. 运行管线

**如果格式不同**：
- 编写自己的解析器（参考 `src/parsers/`）
- 转换为平台支持的格式

### Q: 内存不足

**症状**: 处理大文件时OOM。

**解决**：
1. 分批处理（目前不支持，需自己切分）
2. 关闭图表生成（`--no-plots`）
3. 使用线性插值而非样条插值
4. 增加系统内存

**参考**：示例数据（280万+数据点）约占用500MB内存。

### Q: 如何部署到生产环境？

**不建议直接生产使用**，因为：
- 任务存储在内存（重启丢失）
- 无用户认证
- 无文件大小限制
- 无错误监控

**生产改进建议**：
1. 任务持久化（Redis/PostgreSQL）
2. 用户认证（JWT/OAuth）
3. 文件验证和大小限制
4. 日志聚合和监控
5. 反向代理（Nginx）
6. 容器化部署（Docker）

参考 `Status.md` "下一步计划 - 生产就绪"。

---

## 性能指标

**测试环境**: MacBook Pro M1, 16GB RAM

| 操作 | 数据量 | 耗时 |
|------|--------|------|
| GNSS解析 | 29,831条 | ~0.3s |
| IMU解析 | 2,832,350条 | ~3s |
| 线性插值 | 1Hz→95Hz | ~1s |
| 样条插值 | 1Hz→95Hz | ~3s |
| 时序对齐 | 280万对 | ~5s |
| 可视化 | 6张图表 | ~3s |
| **完整管线** | **全流程** | **~17s** |

Web API额外开销：
- 文件上传：< 100ms
- 状态查询：< 10ms

---

## 进阶使用

### 批量处理多个文件

```python
from pathlib import Path
from src.pipeline.data_pipeline import DataPipeline, PipelineConfig

data_dir = Path("data")
gnss_files = list(data_dir.glob("*GNSS.dat"))

for gnss_file in gnss_files:
    # 假设IMU文件名对应
    imu_file = gnss_file.parent / gnss_file.name.replace("GNSS", "")

    config = PipelineConfig(
        gnss_file=str(gnss_file),
        imu_file=str(imu_file),
        output_dir=f"output/{gnss_file.stem}",
        generate_plots=False  # 批量处理不生成图表
    )

    pipeline = DataPipeline(config)
    results = pipeline.run()

    print(f"{gnss_file.name}: {results.alignment_report['avg_time_diff']*1000:.2f}ms")
```

### 自定义数据解析

```python
from dataclasses import dataclass
from src.models.data_types import TimestampedData

@dataclass
class MyGNSSData(TimestampedData):
    """自定义GNSS数据结构"""
    latitude: float
    longitude: float
    altitude: float
    # ... 其他字段

def parse_my_gnss_file(file_path: str) -> list[MyGNSSData]:
    """自定义解析逻辑"""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            # 解析逻辑
            pass
    return data

# 使用自定义数据
from src.sync.time_sync import TimeAlignment
from src.interpolation.gnss_interpolation import LinearInterpolator

gnss_data = parse_my_gnss_file("my_gnss.txt")
# ... 继续使用其他模块
```

### 只使用特定模块

不需要完整管线？直接用单个模块：

```python
# 只做插值
from src.interpolation.gnss_interpolation import LinearInterpolator
from src.parsers.hex_parser import parse_gnss_file

gnss_data = parse_gnss_file("data/3_NavigationResultGNSS.dat")
target_timestamps = [t for t in range(int(gnss_data[0].timestamp),
                                       int(gnss_data[-1].timestamp),
                                       1/95)]  # 95Hz
interpolated = LinearInterpolator.interpolate(gnss_data, target_timestamps)

# 只做对齐
from src.sync.time_sync import TimeAlignment

pairs, time_diffs = TimeAlignment.align_gnss_imu(gnss_data, imu_data)

# 只做可视化
from src.visualization.plots import plot_gnss_trajectory

plot_gnss_trajectory(gnss_data, "output/my_trajectory.png")
```

---

## 技术支持

- **文档**: README.md, Status.md, data/DATA_FORMAT.md
- **示例**: examples/, tests/
- **问题**: 检查日志输出
- **贡献**: 欢迎提PR

---

**版本**: 1.0.0
**最后更新**: 2025-12-29
